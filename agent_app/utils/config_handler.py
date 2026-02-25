"""
配置文件处理：从 YAML 文件加载各类配置（rag、chroma、prompts、agent 等）。
"""
import os

import yaml

from agent_app.utils.path_tool import get_abs_path

# 所有配置文件的绝对路径
config_path = get_abs_path("config")
rag_config_path = os.path.join(config_path, "rag.yml")
chroma_config_path = os.path.join(config_path, "chroma.yml")
prompts_config_path = os.path.join(config_path, "prompts.yml")
agent_config_path = os.path.join(config_path, "agent.yml")
logging_config_path = os.path.join(config_path, "logging.yml")


def load_config(file_path: str, encoding="utf-8") -> dict:
    """加载单个 YAML 配置文件，返回配置字典。"""
    with open(file_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_rag_config() -> dict:
    """加载 RAG 相关配置。"""
    return load_config(rag_config_path)


def load_chroma_config() -> dict:
    """加载 Chroma 向量库相关配置。"""
    return load_config(chroma_config_path)


def load_prompts_config() -> dict:
    """加载提示词路径等配置。"""
    return load_config(prompts_config_path)


def load_agent_config() -> dict:
    """加载 Agent 相关配置。"""
    return load_config(agent_config_path)


def load_logging_config() -> dict:
    """加载日志级别等配置（config/logging.yml）。若文件不存在则返回默认级别。"""
    if not os.path.isfile(logging_config_path):
        return {"console_level": "INFO", "file_level": "DEBUG"}
    try:
        return load_config(logging_config_path) or {}
    except Exception:
        return {"console_level": "INFO", "file_level": "DEBUG"}


# 全局配置字典，模块加载时一次性读取
rag_config = load_rag_config()
chroma_config = load_chroma_config()
prompts_config = load_prompts_config()
agent_config = load_agent_config()
logging_config = load_logging_config()
