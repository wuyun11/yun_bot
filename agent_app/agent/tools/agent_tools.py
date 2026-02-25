"""
本模块提供 Agent 可调用的工具函数（RAG、天气、用户/月份、外部数据等）。
"""
import csv
import json
import os
import random

from langchain_core.tools import tool

from agent_app.rag.rag_service import RagSummarizeService
from agent_app.utils.config_handler import agent_config
from agent_app.utils.logger_handler import logger
from agent_app.utils.path_tool import get_abs_path

# 外部数据缓存：仅首次从 CSV 加载，后续复用
_external_data_cache: dict = {}
_external_data_loaded = False


@tool(description="从向量存储中检索参考资料,以字符串形式返回")
def rag_summarize(query: str) -> str:
    return RagSummarizeService().rag_summarize(query)


@tool(description="获取指定城市的天气,以字符串形式返回")
def get_weather(city: str) -> str:
    return f"城市{city}的天气是晴天,气温26摄氏度,空气湿度50%,南风1级,AQI指数21,最近6小时降雨概率极低"


@tool(description="获取用户所在城市的名称,以字符串形式返回")
def get_user_location() -> str:
    return random.choice(
        ["北京市", "上海市", "广州市", "深圳市", "成都市", "重庆市", "杭州市", "南京市", "武汉市", "天津市"])


@tool(description="获取用户唯一标识,以字符串形式返回")
def get_user_id() -> str:
    return random.choice(["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"])


@tool(description="获取系统当前月份,以字符串形式返回")
def get_current_month() -> str:
    return random.choice(
        ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10",
         "2025-11", "2025-12"])


def _load_external_data_by_user_month() -> dict:
    """从 CSV 加载外部数据，构建 user_id -> month -> 记录 的嵌套字典，仅首次加载，后续复用缓存。"""
    global _external_data_loaded, _external_data_cache
    if not _external_data_loaded:
        path = get_abs_path(agent_config["external_data_path"])
        if not os.path.exists(path):
            raise FileNotFoundError(f"外部数据文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid, month = row["用户ID"], row["时间"]
                if uid not in _external_data_cache:
                    _external_data_cache[uid] = {}
                _external_data_cache[uid][month] = dict(row)
        _external_data_loaded = True
    return _external_data_cache


@tool(
    description="从外部系统中获取指定用户在指定月份的扫地/扫拖机器人使用记录,以字符串形式返回,如果未检索到,则返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    by_user_month = _load_external_data_by_user_month()
    record = by_user_month.get(user_id, {}).get(month)
    if not record:
        logger.warning(f"未检索到用户{user_id}在{month}的扫地/扫拖机器人使用记录")
        return ""
    return json.dumps(record, ensure_ascii=False, indent=2)


@tool(description="无入参,无返回值,调用后触发中间件自动为报告生成的场景动态注入上下文信息,为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report 工具调用完成"