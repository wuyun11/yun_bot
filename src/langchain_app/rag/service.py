from __future__ import annotations

from functools import lru_cache

from src.langchain_app.rag.ingest_service import IngestService
from src.langchain_app.rag.rag_chain import RagChain
from src.langchain_app.rag.vector_store import VectorStoreService


class RagService:
    """Unified entry for RAG query and ingest operations."""

    def query(
        self,
        *,
        group_id: str,
        query: str,
    ) -> str:
        vector_store = VectorStoreService(group_id)
        return RagChain(vector_store).invoke(query)

    def ingest_refs(self, *, group_id: str, refs_dir: str | None = None) -> dict[str, int]:
        vector_store = VectorStoreService(group_id)
        return IngestService(vector_store).ingest_refs(refs_dir=refs_dir)

    def ingest_text(
        self,
        *,
        group_id: str,
        text: str,
        source: str,
        uploaded_by: str | None = None,
    ) -> dict[str, int]:
        vector_store = VectorStoreService(group_id)
        return IngestService(vector_store).ingest_text(
            text,
            source=source,
            uploaded_by=uploaded_by,
        )

    def reset_group_knowledge(self, *, group_id: str) -> None:
        VectorStoreService(group_id).reset()


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService()
