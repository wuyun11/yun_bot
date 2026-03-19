from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.langchain_app.history import (
    FileChatHistoryStore,
    build_group_session_id,
    format_group_user_message,
)
from src.langchain_app.identity import GroupUserAliasStore
from src.langchain_app.infra.llm import get_agent_model
from src.langchain_app.infra.logger import (
    log_group_block,
    log_group_event,
    log_group_turn,
)
from src.langchain_app.infra.prompt_loader import load_prompt_relative_to
from src.langchain_app.tools import build_rag_search_tool


def _load_system_prompt() -> str:
    return load_prompt_relative_to(__file__, "prompts/group_agent.txt")


def _read_text_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        blocks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    blocks.append(text)
        return "\n".join(blocks).strip()
    return str(content or "").strip()


class GroupChatService:
    def chat(self, *, group_id: str, user_id: str, user_name: str, text: str) -> str:
        session_id = build_group_session_id(group_id)
        history_store = FileChatHistoryStore(session_id)
        alias_store = GroupUserAliasStore(group_id)
        history_text = history_store.render_history(alias_store) or "暂无群共享历史。"
        current_user_name = (user_name or "").strip() or user_id
        system_prompt = _load_system_prompt()
        user_prompt = (
            f"当前用户名称：{current_user_name}\n"
            f"群共享历史：\n{history_text}\n\n"
            f"当前用户消息：\n{format_group_user_message(current_user_name, user_id, text)}"
        )
        log_group_block(group_id, "AGENT SYSTEM PROMPT", system_prompt)
        log_group_block(group_id, "AGENT USER PROMPT", user_prompt)

        tool = build_rag_search_tool(group_id)
        tool_map = {tool.name: tool}
        model = get_agent_model().bind_tools([tool])
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        answer = ""

        for _ in range(4):
            response = model.invoke(messages)
            messages.append(response)
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                answer = _read_text_content(getattr(response, "content", ""))
                break

            for tool_call in tool_calls:
                tool_name = str(tool_call.get("name", "")).strip()
                tool_args = tool_call.get("args", {})
                log_group_event(
                    group_id,
                    "agent_tool_call | name=%s | args=%s",
                    tool_name,
                    tool_args,
                )
                selected_tool = tool_map.get(tool_name)
                if selected_tool is None:
                    tool_result = f"Unknown tool: {tool_name}"
                else:
                    try:
                        tool_result = str(selected_tool.invoke(tool_args))
                    except Exception as exc:
                        tool_result = f"Tool {tool_name} failed: {exc}"
                log_group_block(
                    group_id,
                    f"AGENT TOOL RESULT | {tool_name or 'unknown'}",
                    tool_result,
                )
                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=str(tool_call.get("id", "")),
                    )
                )

        if not answer:
            answer = "我先整理了一下，但这次没有生成有效回复。"

        history_store.append_turn(
            user_id=user_id,
            user_content=text,
            ai_content=answer,
        )
        log_group_turn(
            group_id=group_id,
            user_name=user_name,
            user_id=user_id,
            user_text=text,
            bot_text=answer,
        )
        return answer

    def clear_group_history(self, *, group_id: str) -> None:
        FileChatHistoryStore(build_group_session_id(group_id)).clear()
        log_group_event(group_id, "history_cleared")


@lru_cache(maxsize=1)
def get_group_chat_service() -> GroupChatService:
    return GroupChatService()
