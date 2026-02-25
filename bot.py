import nonebot
from nonebot import logger
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.log import default_format

nonebot.init() # 初始化nonebot

driver = nonebot.get_driver() # 设定驱动
driver.register_adapter(QQAdapter)  # 注册QQ适配器

nonebot.load_builtin_plugins('echo', 'single_session') # 添加一些自带插件
nonebot.load_from_toml("pyproject.toml") # 加载配置文件

logger.add("error.log", level="ERROR", format=default_format, rotation="1 week") # 日志输出


if __name__ == "__main__":
    nonebot.run()
