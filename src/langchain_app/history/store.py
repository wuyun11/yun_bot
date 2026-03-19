from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Any

from src.langchain_app.identity import GroupUserAliasStore

from src.langchain_app.infra.config import app_config


def build_group_session_id(group_id: str) -> str:
    return f"group:{group_id}"


def format_group_user_message(user_name: str, user_id: str, text: str) -> str:
    label = (user_name or "").strip() or user_id
    return f"用户[{label}]: {text.strip()}"


class FileChatHistoryStore:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._path = app_config.history_path(session_id)

    def get_records(self) -> list[dict[str, Any]]:
        if not os.path.isfile(self._path):
            return []
        with open(self._path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, list):
            return []
        records: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                return []
            role = str(item.get("role", "")).strip()
            if not role:
                return []
            records.append(item)
        return records

    def append_turn(self, *, user_id: str, user_content: str, ai_content: str) -> None:
        records = self.get_records()
        now = datetime.now().astimezone().isoformat()
        records.extend(
            [
                {
                    "role": "user",
                    "user_id": user_id,
                    "content": user_content.strip(),
                    "timestamp": now,
                },
                {
                    "role": "assistant",
                    "content": ai_content.strip(),
                    "timestamp": now,
                },
            ]
        )
        if len(records) > app_config.history_max_messages:
            records = records[-app_config.history_max_messages :]
        self._save(records)

    def render_history(self, alias_store: GroupUserAliasStore) -> str:
        lines: list[str] = []
        for record in self.get_records():
            role = record.get("role", "")
            content = str(record.get("content", "")).strip()
            if not content:
                continue

            if role == "user":
                user_id = str(record.get("user_id", "")).strip()
                if not user_id:
                    continue
                user_name = alias_store.get_display_name(user_id)
                lines.append(format_group_user_message(user_name, user_id, content))
                continue

            if role == "assistant":
                lines.append(f"机器人: {content}")
                continue

            lines.append(content)
        return "\n".join(lines)

    def clear(self) -> None:
        if os.path.isfile(self._path):
            os.remove(self._path)

    def _save(self, records: list[dict[str, Any]]) -> None:
        os.makedirs(app_config.history_dir_abs(), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
