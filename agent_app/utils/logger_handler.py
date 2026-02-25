"""
日志工具：按日期写文件、控制台彩色输出，提供统一 get_logger。
级别由 config_handler 提供的 logging_config 决定，未配置时使用下方默认常量。
"""
import logging
import os
import sys
from datetime import datetime

from agent_app.utils.config_handler import logging_config
from agent_app.utils.path_tool import get_abs_path

# 默认级别（logging_config 中未提供或无效时使用）
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG

_LEVEL_NAMES = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 日志保存的根目录
LOG_ROOT_DIR = get_abs_path("logs")

# 确保日志的文件存在
os.makedirs(LOG_ROOT_DIR, exist_ok=True)

# 控制台按级别着色（ANSI 码，Windows 10+ / 现代终端均支持）
_COLORS = {
    logging.DEBUG: "\033[36m",  # 青色
    logging.INFO: "\033[0m",  # 默认（黑/白）
    logging.WARNING: "\033[33m",  # 黄色
    logging.ERROR: "\033[31m",  # 红色
    logging.CRITICAL: "\033[35m",  # 紫红
}
_RESET = "\033[0m"


class ColoredConsoleFormatter(logging.Formatter):
    """控制台用：按日志级别给整行上色。"""

    def format(self, record: logging.LogRecord) -> str:
        raw = super().format(record)
        color = _COLORS.get(record.levelno, _RESET)
        return f"{color}{raw}{_RESET}"


# 日志格式（文件用纯文本，控制台用彩色）
LOG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DEFAULT_LOG_FORMAT = logging.Formatter(LOG_FMT)


def get_logger(
        name: str = "agent",
        console_level: int = None,
        file_level: int = None,
        log_file=None,
) -> logging.Logger:
    """获取或创建 Logger，支持控制台（彩色）与按日期的文件输出；已存在 handler 则直接返回。
    级别优先用入参，否则从 config_handler.logging_config 读取，再否则用模块默认 DEFAULT_*。"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加Handler
    if logger.handlers:
        return logger

    if console_level is None:
        key = (logging_config.get("console_level") or "INFO").upper().strip()
        console_level = _LEVEL_NAMES.get(key, DEFAULT_CONSOLE_LEVEL)
    if file_level is None:
        key = (logging_config.get("file_level") or "DEBUG").upper().strip()
        file_level = _LEVEL_NAMES.get(key, DEFAULT_FILE_LEVEL)

    # 输出到 stdout，避免 PyCharm 把 stderr 整段标红；颜色由 ANSI 码控制
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(ColoredConsoleFormatter(LOG_FMT))

    logger.addHandler(console_handler)

    # 添加文件Handler
    if not log_file:
        # 默认文件名：name_年月日.log
        log_file = os.path.join(LOG_ROOT_DIR, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(file_handler)

    return logger


# 全局默认 Logger，供各模块使用
logger = get_logger()
