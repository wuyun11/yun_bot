from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from src.langchain_app.infra.llm import get_rag_model
from src.langchain_app.infra.logger import get_component_logger
from src.langchain_app.infra.prompt_loader import load_prompt_relative_to
from src.langchain_app.rag.vector_store import VectorStoreService

component_logger = get_component_logger("rag_chain")


def _load_prompt() -> str:
    return load_prompt_relative_to(__file__, "prompts/rag_answer.txt")


class RagChain:
    def __init__(self, vector_store: VectorStoreService) -> None:
        self._retriever = vector_store.get_retriever()
        self._prompt = PromptTemplate.from_template(_load_prompt())
        self._chain = self._prompt | get_rag_model() | StrOutputParser()

    def invoke(
        self,
        query: str,
    ) -> str:
        documents = self._retriever.invoke(query)
        context = self._format_context(documents)
        component_logger.info(
            "Running rag query. query=%s doc_count=%s", query, len(documents)
        )
        return self._chain.invoke({"query": query, "context": context})

    @staticmethod
    def _format_context(documents: list) -> str:
        if not documents:
            return "No reference documents were retrieved."

        blocks: list[str] = []
        for index, document in enumerate(documents, start=1):
            metadata = getattr(document, "metadata", {}) or {}
            source = metadata.get("source", "unknown")
            page = metadata.get("page", metadata.get("page_number", "?"))
            blocks.append(
                f"[{index}] source={source} page={page}\n{document.page_content}"
            )
        return "\n\n".join(blocks)
