from __future__ import annotations

import hashlib
import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from src.langchain_app.infra.config import app_config
from src.langchain_app.infra.logger import log_group_event, logger
from src.langchain_app.rag.vector_store import VectorStoreService


def _file_md5(path: str) -> str:
    with open(path, "rb") as file:
        return hashlib.md5(file.read()).hexdigest()


def _load_text(path: str) -> list[Document]:
    return TextLoader(path, encoding="utf-8").load()


def _load_pdf(path: str) -> list[Document]:
    return PyPDFLoader(path).load()


class IngestService:
    def __init__(self, vector_store: VectorStoreService) -> None:
        self._vector_store = vector_store
        self._group_id = vector_store.group_id or "default"

    def ingest_refs(self, refs_dir: str | None = None) -> dict[str, int]:
        refs_dir = refs_dir or app_config.group_refs_path(self._group_id)
        if not os.path.isdir(refs_dir):
            logger.warning("Refs directory does not exist: %s", refs_dir)
            return {"files": 0, "chunks": 0, "skipped": 0}

        md5_store_path = app_config.md5_store_path(f"group_refs_{self._group_id}")
        existing_md5s = self._load_md5s(md5_store_path)

        file_count = 0
        chunk_count = 0
        skipped_count = 0

        for path in sorted(Path(refs_dir).iterdir()):
            if not path.is_file():
                continue

            ext = path.suffix.lower()
            if ext not in app_config.allow_file_types:
                skipped_count += 1
                continue

            content_md5 = _file_md5(str(path))
            if content_md5 in existing_md5s:
                skipped_count += 1
                continue

            documents = self._load_documents(path)
            if not documents:
                skipped_count += 1
                continue

            file_count += 1
            added_chunks = self._vector_store.add_documents(documents)
            chunk_count += added_chunks
            self._append_md5(md5_store_path, content_md5)
            existing_md5s.add(content_md5)
            logger.info("Ingested ref file: %s", path.name)
            log_group_event(
                self._group_id,
                "ingest_ref_file | source=%s | chunks=%s",
                path.name,
                added_chunks,
            )

        return {"files": file_count, "chunks": chunk_count, "skipped": skipped_count}

    def ingest_text(
        self,
        text: str,
        *,
        source: str,
        uploaded_by: str | None = None,
    ) -> dict[str, int]:
        text = text.strip()
        if not text:
            return {"files": 0, "chunks": 0, "skipped": 1}

        md5_store_path = app_config.md5_store_path(f"group_text_{self._group_id}")
        existing_md5s = self._load_md5s(md5_store_path)
        content_md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        if content_md5 in existing_md5s:
            return {"files": 0, "chunks": 0, "skipped": 1}

        documents = [
            Document(
                page_content=text,
                metadata={
                    "group_id": self._group_id,
                    "source_type": "command_text",
                    "source": source,
                    "uploaded_by": uploaded_by or "",
                },
            )
        ]
        chunk_count = self._vector_store.add_documents(documents)
        self._append_md5(md5_store_path, content_md5)
        log_group_event(
            self._group_id,
            "ingest_text | source=%s | uploaded_by=%s | chunks=%s",
            source,
            uploaded_by or "",
            chunk_count,
        )
        return {"files": 1, "chunks": chunk_count, "skipped": 0}

    def _load_documents(self, path: Path) -> list[Document]:
        ext = path.suffix.lower()
        if ext in {".txt", ".md"}:
            return _load_text(str(path))
        if ext == ".pdf":
            return _load_pdf(str(path))
        return []

    @staticmethod
    def _load_md5s(path: str) -> set[str]:
        if not os.path.isfile(path):
            return set()
        with open(path, "r", encoding="utf-8") as file:
            return {line.strip() for line in file if line.strip()}

    @staticmethod
    def _append_md5(path: str, md5_value: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as file:
            file.write(md5_value + "\n")
