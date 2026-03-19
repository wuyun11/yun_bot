from __future__ import annotations

from nonebot import on_message
from nonebot.adapters.qq import MessageEvent
from nonebot.rule import Rule, to_me

from src.langchain_app.chat import get_group_chat_service
from src.langchain_app.qq import get_display_name, get_group_id, get_user_id, is_group_message

MENU_COMMANDS = {
    "/help",
    "/name",
    "/set name",
    "/rag",
    "/upload",
    "/clear",
}


async def check_value_in_menu(message: MessageEvent) -> bool:
    text = message.get_plaintext().strip()
    if not text:
        return True
    return not any(text.startswith(command) for command in MENU_COMMANDS)


check = on_message(rule=to_me() & Rule(check_value_in_menu), block=True, priority=10)


@check.handle()
async def handle_function(message: MessageEvent):
    text = message.get_plaintext().strip()
    if not text:
        await check.finish("请输入内容。")
        return

    group_id = get_group_id(message)
    if group_id and is_group_message(message):
        reply = get_group_chat_service().chat(
            group_id=group_id,
            user_id=get_user_id(message),
            user_name=get_display_name(message),
            text=text,
        )
        await check.finish(reply.strip() or "没有获取到回复。")
        return

    await check.finish("当前只支持群聊场景直接对话。")
