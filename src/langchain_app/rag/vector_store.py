from __future__ import annotations

import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.langchain_app.infra.config import app_config
from src.langchain_app.infra.llm import get_embedding_model


class VectorStoreService:
    def __init__(self, group_id: str | None = None) -> None:
        self.group_id = group_id
        self._store = Chroma(
            collection_name=self._build_collection_name(group_id),
            embedding_function=get_embedding_model(),
            persist_directory=app_config.chroma_persist_abs(),
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=app_config.chunk_size,
            chunk_overlap=app_config.chunk_overlap,
            separators=app_config.separators,
            length_function=len,
        )

    def add_documents(self, documents: list[Document]) -> int:
        if not documents:
            return 0
        split_documents = self._splitter.split_documents(documents)
        if not split_documents:
            return 0
        self._store.add_documents(split_documents)
        return len(split_documents)

    def get_retriever(self, top_k: int | None = None):
        return self._store.as_retriever(
            search_kwargs={"k": top_k or app_config.top_k}
        )

    def reset(self) -> None:
        self._store.delete_collection()

    @staticmethod
    def _build_collection_name(group_id: str | None) -> str:
        if not group_id:
            return f"{app_config.chroma_collection}_{app_config.library_code}"
        safe_group = re.sub(r"[^A-Za-z0-9._-]+", "_", group_id).strip("._")
        if not safe_group:
            safe_group = "default"
        return f"{app_config.chroma_collection}_group_{safe_group}"
