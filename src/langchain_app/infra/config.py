from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_CHROMA_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]+[A-Za-z0-9]$")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict) or not data:
        raise ValueError(f"Config file is empty or invalid: {path}")
    return data


def _require(data: dict[str, Any] | None, key: str, section: str) -> Any:
    if data is None:
        raise ValueError(f"Missing config section: {section}")
    value = data.get(key)
    if value is None or (isinstance(value, (str, list)) and len(value) == 0):
        raise ValueError(f"Missing required field `{key}` in `{section}`")
    return value


def _is_valid_chroma_name(value: str) -> bool:
    return bool(_CHROMA_NAME_PATTERN.fullmatch(value.strip()))


@dataclass(frozen=True, slots=True)
class AppConfig:
    library_name: str
    library_code: str
    data_dir: str
    group_refs_dir: str
    chroma_collection: str
    chroma_persist_directory: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    separators: list[str]
    allow_file_types: list[str]
    log_dir: str
    history_store_dir: str
    history_max_messages: int
    user_alias_store_dir: str

    def abs(self, *parts: str) -> str:
        return str(PROJECT_ROOT.joinpath(*parts))

    def refs_dir(self) -> str:
        return self.abs(self.data_dir, self.library_name, "refs")

    def group_refs_path(self, group_id: str) -> str:
        return self.abs(self.group_refs_dir, group_id, "refs")

    def chroma_library_dirname(self) -> str:
        return f"{self.library_name}_{self.library_code}"

    def chroma_persist_abs(self) -> str:
        return self.abs(self.chroma_persist_directory)

    def md5_store_path(self, key: str) -> str:
        safe_key = re.sub(r"[^\w.-]+", "_", key).strip("._") or "default"
        return self.abs(self.chroma_persist_directory, "_md5", f"{safe_key}.txt")

    def log_dir_abs(self) -> str:
        return self.abs(self.log_dir)

    def history_dir_abs(self) -> str:
        return self.abs(self.history_store_dir)

    def history_path(self, session_id: str) -> str:
        safe_session = re.sub(r"[^\w.-]+", "_", session_id).strip("._") or "session"
        return self.abs(self.history_store_dir, f"{safe_session}.json")

    def user_alias_dir_abs(self) -> str:
        return self.abs(self.user_alias_store_dir)

    def user_alias_path(self, group_id: str) -> str:
        safe_group = re.sub(r"[^\w.-]+", "_", group_id).strip("._") or "group"
        return self.abs(self.user_alias_store_dir, f"{safe_group}.json")

    @classmethod
    def load(cls) -> "AppConfig":
        data = _load_yaml(PROJECT_ROOT / "config" / "app.yml")

        library_name = str(_require(data, "library_name", "config/app.yml")).strip()
        library_code = str(data.get("library_code", library_name)).strip()
        if not _is_valid_chroma_name(library_code):
            raise ValueError(
                "config/app.yml `library_code` must use only [A-Za-z0-9._-] "
                "and start/end with alphanumeric characters."
            )

        paths = _require(data, "paths", "config/app.yml")
        chroma = _require(data, "chroma", "config/app.yml")
        logging_cfg = _require(data, "logging", "config/app.yml")
        history_cfg = _require(data, "history", "config/app.yml")
        user_alias_cfg = _require(data, "user_alias", "config/app.yml")

        return cls(
            library_name=library_name,
            library_code=library_code,
            data_dir=str(_require(paths, "data_dir", "config/app.yml paths")).strip(),
            group_refs_dir=str(
                _require(paths, "group_refs_dir", "config/app.yml paths")
            ).strip(),
            chroma_collection=str(
                _require(chroma, "collection_name", "config/app.yml chroma")
            ).strip(),
            chroma_persist_directory=str(
                _require(chroma, "persist_directory", "config/app.yml chroma")
            ).strip(),
            chunk_size=int(_require(chroma, "chunk_size", "config/app.yml chroma")),
            chunk_overlap=int(
                _require(chroma, "chunk_overlap", "config/app.yml chroma")
            ),
            top_k=int(_require(chroma, "k", "config/app.yml chroma")),
            separators=list(_require(chroma, "separators", "config/app.yml chroma")),
            allow_file_types=[
                str(item).lower()
                for item in _require(chroma, "allow_file_types", "config/app.yml chroma")
            ],
            log_dir=str(_require(logging_cfg, "log_dir", "config/app.yml logging")).strip(),
            history_store_dir=str(
                _require(history_cfg, "store_dir", "config/app.yml history")
            ).strip(),
            history_max_messages=int(
                _require(history_cfg, "max_messages", "config/app.yml history")
            ),
            user_alias_store_dir=str(
                _require(user_alias_cfg, "store_dir", "config/app.yml user_alias")
            ).strip(),
        )


@dataclass(frozen=True, slots=True)
class ModelConfig:
    llm_provider: str
    agent_model_name: str
    rag_chain_model_name: str
    embedding_provider: str
    embedding_model_name: str
    ollama_base_url: str | None

    @classmethod
    def load(cls) -> "ModelConfig":
        data = _load_yaml(PROJECT_ROOT / "config" / "model.yml")
        ollama_base_url = data.get("ollama_base_url")
        return cls(
            llm_provider=str(
                _require(data, "llm_provider", "config/model.yml")
            ).strip(),
            agent_model_name=str(
                _require(data, "agent_model_name", "config/model.yml")
            ).strip(),
            rag_chain_model_name=str(
                _require(data, "rag_chain_model_name", "config/model.yml")
            ).strip(),
            embedding_provider=str(
                _require(data, "embedding_provider", "config/model.yml")
            ).strip(),
            embedding_model_name=str(
                _require(data, "embedding_model_name", "config/model.yml")
            ).strip(),
            ollama_base_url=str(ollama_base_url).strip() if ollama_base_url else None,
        )


app_config = AppConfig.load()
model_config = ModelConfig.load()
