from __future__ import annotations

from datetime import datetime
import logging
import os
import re

from .config import app_config

_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


def _today_token() -> str:
    return datetime.now().strftime("%Y%m%d")


def _safe_name(value: str, fallback: str) -> str:
    return re.sub(r"[^\w.-]+", "_", value).strip("._") or fallback


def get_day_log_dir() -> str:
    return os.path.join(app_config.log_dir_abs(), _today_token())


def get_main_log_path() -> str:
    return os.path.join(get_day_log_dir(), "main.log")


def get_group_log_path(group_id: str) -> str:
    safe_group = _safe_name(group_id, "group")
    return os.path.join(get_day_log_dir(), "groups", f"{safe_group}.log")


def _build_file_handler(path: str, level: int = logging.DEBUG) -> logging.Handler:
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def get_logger(name: str = "yun_bot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    os.makedirs(get_day_log_dir(), exist_ok=True)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_FORMAT))

    logger.addHandler(console_handler)
    logger.addHandler(_build_file_handler(get_main_log_path()))
    return logger


def get_component_logger(component_name: str) -> logging.Logger:
    get_logger()
    logger = logging.getLogger(f"yun_bot.{component_name}")
    logger.setLevel(logging.DEBUG)
    return logger


def get_group_logger(group_id: str) -> logging.Logger:
    safe_group = _safe_name(group_id, "group")
    logger = logging.getLogger(f"yun_bot.group.{safe_group}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    path = get_group_log_path(group_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logger.addHandler(_build_file_handler(path, level=logging.INFO))
    return logger


def log_group_event(group_id: str, message: str, *args: object) -> None:
    get_group_logger(group_id).info("EVENT | " + message, *args)


def log_group_block(group_id: str, title: str, content: str) -> None:
    text = content.strip()
    if not text:
        return
    get_group_logger(group_id).info("%s\n%s", title, text)


def log_group_turn(
    *,
    group_id: str,
    user_name: str,
    user_id: str,
    user_text: str,
    bot_text: str,
) -> None:
    group_logger = get_group_logger(group_id)
    display_name = (user_name or "").strip() or user_id
    group_logger.info(
        "USER | name=%s | user_id=%s | message=%s",
        display_name,
        user_id,
        user_text.strip(),
    )
    group_logger.info("BOT | message=%s", bot_text.strip())


logger = get_logger()
