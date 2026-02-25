from nonebot import  on_message
from nonebot.adapters.qq import MessageEvent
from nonebot.rule import Rule, to_me

menu = ["/天气", "/查天气", "/摸摸"]


async def check_value_in_menu(message: MessageEvent) -> bool:
    value = message.get_plaintext().strip().split(" ") # 获取用户发送的文本，并将其按照空格分为字符串数组
    if value[0] in menu: # 如果数组中的第一个元素在menu数组中，返回False
        return False
    else:
        return True


check = on_message(rule=to_me() & Rule(check_value_in_menu) ,block=True, priority=10)
@check.handle()
async def handle_function(message: MessageEvent):
    await check.finish("请输入正确的指令。")
