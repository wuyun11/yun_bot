from __future__ import annotations

from nonebot import on_command, on_startswith
from nonebot.adapters.qq import MessageEvent
from nonebot.params import CommandArg

from src.langchain_app.chat import get_group_chat_service
from src.langchain_app.identity import GroupUserAliasStore
from src.langchain_app.qq import get_group_id, get_user_id
from src.langchain_app.rag.service import get_rag_service

help_command = on_command("help", priority=5, block=True)
name_command = on_command("name", priority=5, block=True)
set_name_command = on_startswith("/set name", priority=5, block=True)
rag_query = on_command("rag", priority=5, block=True)
upload_command = on_command("upload", priority=5, block=True)
clear_command = on_command("clear", priority=5, block=True)


def _require_group_id(event: MessageEvent) -> str | None:
    return get_group_id(event)


def _extract_set_name(text: str) -> str:
    prefix = "/set name"
    if not text.startswith(prefix):
        return ""
    return text[len(prefix) :].strip()


@help_command.handle()
async def handle_help():
    await help_command.finish(
        "可用指令：\n"
        "/help 查看帮助\n"
        "/name 查看你当前的名称\n"
        "/set name 新名称 设置你的名称\n"
        "/rag 问题 直接检索本群知识库\n"
        "/upload 文本 把一段字符串录入本群知识库\n"
        "/clear 清空本群共享聊天历史\n"
        "@机器人 直接对话会走 agent"
    )


@name_command.handle()
async def handle_name(event: MessageEvent):
    group_id = _require_group_id(event)
    if not group_id:
        await name_command.finish("当前只支持群聊场景查看名称。")
        return

    user = GroupUserAliasStore(group_id).get_user(get_user_id(event))
    await name_command.finish(
        f"你当前的名称: {user['name']}\n"
        f"默认顺序名: {user['order']}"
    )


@set_name_command.handle()
async def handle_set_name(event: MessageEvent):
    group_id = _require_group_id(event)
    if not group_id:
        await set_name_command.finish("当前只支持群聊场景设置名称。")
        return

    name = _extract_set_name(event.get_plaintext().strip())
    if not name:
        await set_name_command.finish("用法: /set name 你想使用的名称")
        return

    user = GroupUserAliasStore(group_id).set_display_name(get_user_id(event), name)
    await set_name_command.finish(
        f"你的名称已更新为: {user['name']}\n"
        f"默认顺序名: {user['order']}"
    )


@rag_query.handle()
async def handle_rag_query(event: MessageEvent, args=CommandArg()):
    group_id = _require_group_id(event)
    if not group_id:
        await rag_query.finish("当前只支持群聊场景使用 /rag。")
        return

    query = args.extract_plain_text().strip()
    if not query:
        await rag_query.finish("用法: /rag 你的问题")
        return

    answer = get_rag_service().query(group_id=group_id, query=query).strip()
    await rag_query.finish(answer or "没有检索到可用结果。")


@upload_command.handle()
async def handle_upload(event: MessageEvent, args=CommandArg()):
    group_id = _require_group_id(event)
    if not group_id:
        await upload_command.finish("当前只支持群聊场景使用 /upload。")
        return

    text = args.extract_plain_text().strip()
    if not text:
        await upload_command.finish("用法: /upload 需要录入知识库的一段文本")
        return

    result = get_rag_service().ingest_text(
        group_id=group_id,
        text=text,
        source="upload_command",
        uploaded_by=get_user_id(event),
    )
    await upload_command.finish(
        "本群知识录入完成。\n"
        f"新增文件: {result['files']}\n"
        f"新增分块: {result['chunks']}\n"
        f"跳过数量: {result['skipped']}"
    )


@clear_command.handle()
async def handle_clear(event: MessageEvent):
    group_id = _require_group_id(event)
    if not group_id:
        await clear_command.finish("当前只支持群聊场景清空对话历史。")
        return

    get_group_chat_service().clear_group_history(group_id=group_id)
    await clear_command.finish("本群共享聊天历史已清空。")
