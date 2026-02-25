"""
根据配置项从本地文件加载各类提示词（系统、RAG 总结、报告等）。
"""
from agent_app.utils.config_handler import prompts_config
from agent_app.utils.path_tool import get_abs_path
from agent_app.utils.logger_handler import logger


def load_prompt(config_key: str, prompt_name: str) -> str:
    """根据 config_key 读取提示词文件内容；配置缺失或读取失败会打日志并抛异常。"""
    try:
        prompt_path = get_abs_path(prompts_config[config_key])
    except KeyError as e:
        logger.error(f"[提示词加载]在配置文件中未找到{config_key}配置项: {str(e)}")
        raise e
    try:
        return open(prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[提示词加载]加载{prompt_name}失败: {str(e)}")
        raise e


def load_system_prompt() -> str:
    """加载系统提示词。"""
    return load_prompt("main_prompt_path", "系统提示词")


def load_rag_summarize_prompt() -> str:
    """加载 RAG 总结用提示词。"""
    return load_prompt("rag_summarize_prompt_path", "rag总结提示词")


def load_report_prompt() -> str:
    """加载报告用提示词。"""
    return load_prompt("report_prompt_path", "报告提示词")
