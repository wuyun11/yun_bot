from __future__ import annotations

from nonebot.adapters.qq import MessageEvent

from src.langchain_app.identity import GroupUserAliasStore


def get_group_id(event: MessageEvent) -> str | None:
    return getattr(event, "group_openid", None)


def get_user_id(event: MessageEvent) -> str:
    author = getattr(event, "author", None)
    if author is not None:
        for field in ("member_openid", "id", "union_openid"):
            value = getattr(author, field, None)
            if value:
                return str(value)
    return str(event.get_user_id())


def get_display_name(event: MessageEvent) -> str:
    group_id = get_group_id(event)
    user_id = get_user_id(event)
    if not group_id:
        return user_id
    return GroupUserAliasStore(group_id).get_display_name(user_id)


def is_group_message(event: MessageEvent) -> bool:
    return bool(get_group_id(event))
