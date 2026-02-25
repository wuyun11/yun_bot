# Python 垃圾回收（GC）机制详解

## 核心问题

1. **Python 本身不做 GC 吗？**
2. **一些不用的变量也不管吗？**
3. **为什么模块不会被回收？**

---

## 答案：Python 确实有 GC，而且很强大！

Python 有**两套垃圾回收机制**：
1. **引用计数**（主要机制，实时回收）
2. **分代回收**（处理循环引用，定期回收）

---

## 1. 引用计数机制（主要机制）

### 工作原理

每个对象都有一个引用计数，记录有多少个变量/对象引用了它。

```python
import sys

# 创建一个对象
obj = [1, 2, 3]
print(sys.getrefcount(obj))  # 输出：2（obj + getrefcount的参数）

# 增加引用
obj2 = obj
print(sys.getrefcount(obj))  # 输出：3（obj + obj2 + getrefcount的参数）

# 删除引用
del obj2
print(sys.getrefcount(obj))  # 输出：2

# 删除最后一个引用
del obj
# 此时引用计数为0，对象立即被回收！
```

### 特点

- ✅ **实时回收**：引用计数为0时立即回收
- ✅ **高效**：不需要扫描整个内存
- ✅ **简单**：逻辑清晰，易于理解

### 实际例子

```python
def test_function():
    local_var = [1, 2, 3] * 1000  # 创建一个大对象
    print(f"对象创建，引用计数: {sys.getrefcount(local_var)}")
    # 函数执行结束，local_var 超出作用域
    # 引用计数变为0，对象立即被回收

test_function()
# 函数执行完后，local_var 对象已经被回收了！
```

---

## 2. 分代回收机制（处理循环引用）

### 问题：循环引用

引用计数无法处理循环引用：

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

# 创建循环引用
node1 = Node(1)
node2 = Node(2)
node1.next = node2
node2.next = node1  # 循环引用！

# 删除外部引用
del node1
del node2

# 问题：node1 和 node2 互相引用，引用计数都是1
# 引用计数无法归零，但外部已经无法访问了！
```

### 解决方案：分代回收

Python 使用**分代回收**来处理循环引用：

```python
import gc

# 创建循环引用
node1 = Node(1)
node2 = Node(2)
node1.next = node2
node2.next = node1

del node1
del node2

# 手动触发GC（实际是自动的）
collected = gc.collect()
print(f"回收了 {collected} 个对象")
```

### 分代回收的工作原理

1. **分3代**：
   - 0代：新创建的对象
   - 1代：经过一次GC后存活的对象
   - 2代：经过多次GC后存活的对象

2. **回收策略**：
   - 0代对象回收最频繁（因为大多数对象都是短命的）
   - 1代、2代对象回收较少（因为它们是长命的）

3. **回收时机**：
   - 当分配的对象数量达到阈值时触发
   - 默认阈值：`(700, 10, 10)`（0代700个，1代10次，2代10次）

---

## 3. 为什么模块不会被回收？

### 关键：sys.modules 持有永久引用

```python
import sys

# 导入模块
from utils.config_handler import rag_config

# 获取模块对象
module = sys.modules['utils.config_handler']

# 模块的引用计数包括：
# 1. sys.modules['utils.config_handler'] ← 永久引用！
# 2. 当前文件的 import 语句
# 3. 其他可能导入这个模块的文件

# 即使删除当前文件的引用
del module

# 模块仍然在 sys.modules 中！
print('utils.config_handler' in sys.modules)  # True

# 因为 sys.modules 持有引用，引用计数不会为0
# 所以模块不会被GC回收！
```

### 模块的生命周期

```
模块导入
  ↓
存入 sys.modules（永久引用）
  ↓
引用计数 ≥ 1（因为有 sys.modules 的引用）
  ↓
不会被GC回收
  ↓
程序结束时，sys.modules 被清空
  ↓
模块被回收
```

---

## 4. 变量作用域 vs 对象生命周期

### 重要区别

**变量作用域** ≠ **对象生命周期**

```python
def create_object():
    obj = [1, 2, 3]  # 局部变量
    return obj        # 返回对象

# 调用函数
returned_obj = create_object()

# 函数执行结束：
# - 局部变量 obj 超出作用域（变量不存在了）
# - 但对象 [1, 2, 3] 仍在内存中（因为 returned_obj 持有引用）
# - 对象的引用计数 = 1（returned_obj 的引用）

# 删除 returned_obj
del returned_obj

# 现在对象的引用计数 = 0
# 对象被回收！
```

### 实际例子

```python
def test():
    local_list = [1, 2, 3] * 1000
    print(f"函数内：对象内存地址 {id(local_list)}")
    return local_list  # 返回对象

# 调用函数
result = test()
print(f"函数外：对象内存地址 {id(result)}")
# 输出：两个地址相同！说明是同一个对象

# 函数执行结束，但对象仍在内存中（因为 result 持有引用）
# 只有删除 result，对象才会被回收
del result
# 现在对象被回收了
```

---

## 5. Python GC 的实际行为

### 普通变量：会被回收

```python
# 场景1：局部变量
def function():
    local_var = "test"
    # 函数执行结束，local_var 超出作用域
    # 如果没有外部引用，对象立即被回收

# 场景2：临时对象
result = sum([1, 2, 3])  # [1, 2, 3] 是临时对象
# 计算完成后，列表对象立即被回收（引用计数为0）

# 场景3：删除引用
obj = [1, 2, 3]
del obj  # 删除引用，对象立即被回收
```

### 模块级变量：不会被回收（直到程序结束）

```python
# config_handler.py
rag_config = load_rag_config()  # 模块级变量

# 原因：
# 1. rag_config 是模块对象的属性
# 2. 模块对象在 sys.modules 中（永久引用）
# 3. 只要模块不被删除，rag_config 就不会被回收
```

### 全局变量：通常不会被回收

```python
# 模块级全局变量
GLOBAL_VAR = "test"

# 原因：
# 1. GLOBAL_VAR 是模块对象的属性
# 2. 模块对象在 sys.modules 中
# 3. 所以不会被回收（直到程序结束）
```

---

## 6. GC 统计和监控

### 查看 GC 统计

```python
import gc

# 获取GC统计
print(gc.get_stats())
# 输出：各代的统计信息

# 获取GC阈值
print(gc.get_threshold())
# 输出：(700, 10, 10)

# 手动触发GC
collected = gc.collect()
print(f"回收了 {collected} 个对象")

# 查看GC是否启用
print(gc.isenabled())  # True
```

### 禁用/启用 GC

```python
import gc

# 禁用GC（不推荐，除非有特殊需求）
gc.disable()

# 启用GC
gc.enable()
```

---

## 7. 常见误解

### 误解1：Python 不做 GC

**错误！** Python 有强大的 GC 机制：
- 引用计数（实时回收）
- 分代回收（处理循环引用）

### 误解2：变量作用域结束 = 对象被回收

**错误！** 
- 变量作用域结束 ≠ 对象被回收
- 对象是否被回收 = 引用计数是否为0

```python
def test():
    obj = [1, 2, 3]
    return obj  # 返回对象

result = test()
# 函数执行结束，但对象仍在内存中（因为 result 持有引用）
```

### 误解3：模块会被 GC 回收

**错误！** 
- 模块对象在 sys.modules 中（永久引用）
- 引用计数不会为0，所以不会被回收
- 直到程序结束才会被回收

---

## 8. 最佳实践

### 1. 理解引用计数

```python
# 好的做法：及时删除不需要的引用
large_data = load_large_data()
process_data(large_data)
del large_data  # 及时删除，释放内存
```

### 2. 避免循环引用

```python
# 不好的做法：循环引用
class Node:
    def __init__(self):
        self.next = None

node1 = Node()
node2 = Node()
node1.next = node2
node2.next = node1  # 循环引用

# 好的做法：使用弱引用
import weakref
node2.next = weakref.ref(node1)  # 弱引用，不增加引用计数
```

### 3. 理解模块的生命周期

```python
# 模块级变量在程序运行期间一直存在
# 如果配置很大，考虑延迟加载：

# 方式1：函数方式（按需加载）
def get_config():
    return load_config()

# 方式2：属性方式（延迟加载）
class Config:
    @property
    def rag_config(self):
        if not hasattr(self, '_rag_config'):
            self._rag_config = load_config()
        return self._rag_config
```

---

## 9. 总结对比表

| 对象类型 | 回收时机 | 原因 |
|---------|---------|------|
| **局部变量** | 函数执行结束 + 无外部引用 | 引用计数为0 |
| **临时对象** | 使用完立即 | 引用计数为0 |
| **模块对象** | 程序结束时 | sys.modules 持有永久引用 |
| **模块级变量** | 程序结束时 | 是模块对象的属性 |
| **循环引用对象** | GC 触发时 | 分代回收处理 |

---

## 10. 关键要点

1. ✅ **Python 有强大的 GC 机制**
   - 引用计数（主要，实时回收）
   - 分代回收（处理循环引用）

2. ✅ **普通变量会被回收**
   - 引用计数为0时立即回收
   - 函数执行结束，局部变量通常会被回收

3. ✅ **模块不会被回收**
   - 因为 sys.modules 持有永久引用
   - 直到程序结束才会被回收

4. ✅ **变量作用域 ≠ 对象生命周期**
   - 变量作用域结束，对象不一定被回收
   - 对象是否被回收取决于引用计数

5. ✅ **理解引用计数是关键**
   - 引用计数为0 → 立即回收
   - 引用计数 > 0 → 不会被回收

---

## 11. 实际验证

运行 `python_gc_demo.py` 可以看到实际的 GC 行为！

```bash
python utils/python_gc_demo.py
```

这个脚本会演示：
- 普通变量如何被回收
- 模块为什么不会被回收
- 引用计数的工作原理
- 循环引用的处理
