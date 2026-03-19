from __future__ import annotations

import json
import os
from typing import Any

from src.langchain_app.infra.config import app_config


def _index_to_suffix(index: int) -> str:
    letters: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        letters.append(chr(ord("A") + remainder))
        if value == 0:
            break
        value -= 1
    return "".join(reversed(letters))


class GroupUserAliasStore:
    def __init__(self, group_id: str) -> None:
        self._group_id = group_id
        self._path = app_config.user_alias_path(group_id)

    def ensure_user(self, user_id: str) -> dict[str, Any]:
        payload = self._load()
        users = payload.setdefault("users", {})
        user = users.get(user_id)
        if user is not None:
            return user

        order = len(users)
        order_name = f"用户{_index_to_suffix(order)}"
        user = {
            "user_id": user_id,
            "order": order_name,
            "name": order_name,
        }
        users[user_id] = user
        self._save(payload)
        return user

    def get_user(self, user_id: str) -> dict[str, Any]:
        return self.ensure_user(user_id)

    def get_display_name(self, user_id: str) -> str:
        user = self.ensure_user(user_id)
        return str(user.get("name") or user.get("order") or user_id)

    def set_display_name(self, user_id: str, name: str) -> dict[str, Any]:
        payload = self._load()
        users = payload.setdefault("users", {})
        user = users.get(user_id) or self.ensure_user(user_id)
        user["name"] = name.strip() or user["order"]
        users[user_id] = user
        self._save(payload)
        return user

    def _load(self) -> dict[str, Any]:
        if not os.path.isfile(self._path):
            return {"group_id": self._group_id, "users": {}}
        with open(self._path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            return {"group_id": self._group_id, "users": {}}
        payload.setdefault("group_id", self._group_id)
        payload.setdefault("users", {})
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        os.makedirs(app_config.user_alias_dir_abs(), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
