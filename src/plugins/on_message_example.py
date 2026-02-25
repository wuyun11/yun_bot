from nonebot import on_message
from nonebot.adapters.qq import MessageEvent
from nonebot.rule import Rule, to_me
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import OllamaLLM

menu = ["/天气", "/查天气", "/摸摸"]

_model = None

def _get_model() -> OllamaLLM:
    global _model
    if _model is None:
        _model = OllamaLLM(model="qwen3:4b")
    return _model


async def check_value_in_menu(message: MessageEvent) -> bool:
    value = message.get_plaintext().strip().split(" ")
    if value[0] in menu:
        return False
    return True


check = on_message(rule=to_me() & Rule(check_value_in_menu), block=True, priority=10)


@check.handle()
async def handle_function(message: MessageEvent):
    text = message.get_plaintext().strip()
    if not text:
        await check.finish("请输入内容。")
        return
    model = _get_model()
    reply = model.invoke(
        [
            SystemMessage(content="你是有用的助手。回答时不要包含任何网址、链接或 URL，只输出纯文字内容。"),
            HumanMessage(content=text),
        ]
    )
    content = getattr(reply, "content", reply) or ""
    await check.finish(content.strip() or "没有获取到回复。")
