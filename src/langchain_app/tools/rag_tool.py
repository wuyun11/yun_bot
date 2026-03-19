from __future__ import annotations

from langchain_core.tools import tool


def build_rag_search_tool(group_id: str):
    @tool("rag_search")
    def rag_search_tool(query: str) -> str:
        """Search the current group's knowledge base and answer from retrieved context."""
        from src.langchain_app.rag.service import get_rag_service

        query = query.strip()
        if not query:
            return "RAG 查询不能为空。"
        return (
            get_rag_service().query(group_id=group_id, query=query).strip()
            or "没有检索到可用结果。"
        )

    return rag_search_tool


rag_search_tool = build_rag_search_tool("default")
