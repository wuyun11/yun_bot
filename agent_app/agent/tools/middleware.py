"""
Agent 中间件：监控工具调用、模型调用前日志、提示词切换上报等。
"""
from typing import Callable

from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command

from agent_app.utils.logger_handler import logger
from agent_app.utils.prompt_loader import load_report_prompt, load_system_prompt


@wrap_tool_call
def monitor_tool(request: ToolCallRequest,
                 handler: Callable[[ToolCallRequest], ToolMessage | Command]) -> ToolMessage | Command:
    """包装工具调用，用于监控或统计。"""
    tool_name = request.tool_call['name']
    tool_args = request.tool_call['args']
    logger.info(f"[tool monitor] 执行工具: {tool_name}")
    logger.info(f"[tool monitor] 传入参数: {tool_args}")
    try:
        result = handler(request)
        logger.info(f"[tool monitor] 工具{tool_name}调用完成")
        if tool_name == "fill_context_for_report":
            request.runtime.context["report"] = True
        return result
    except Exception as e:
        logger.error(f"[tool monitor] 工具{tool_name}调用失败: {str(e)}", exc_info=True)
        raise e


@before_model
def log_before_model(
        state: AgentState,
        runtime: Runtime
):
    """在调用模型前记录日志（如请求内容摘要）。"""
    logger.info(f"[before model monitor] 即将调用模型: 带有{len(state['messages'])}条消息")
    logger.debug(
        f"[before model monitor]{type(state['messages'][-1]).__name__}: {state['messages'][-1].content.strip()}")
    return None


@dynamic_prompt
def report_prompt_switch(request: ModelRequest):
    """上报或记录提示词切换事件。每一次生成提示词之前会调用此函数"""
    is_report = request.runtime.context.get("report", False)
    if is_report:
        return load_report_prompt()
    else:
        return load_system_prompt()
