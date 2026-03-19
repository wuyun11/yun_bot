from __future__ import annotations

from functools import lru_cache
import os

from dotenv import load_dotenv

from .config import PROJECT_ROOT, model_config

load_dotenv(PROJECT_ROOT / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def _build_chat_model(model_name: str):
    if model_config.llm_provider == "dashscope":
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=model_name,
            api_key=_require_env("DASHSCOPE_API_KEY"),
        )

    if model_config.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        kwargs: dict[str, str] = {"model": model_name}
        if model_config.ollama_base_url:
            kwargs["base_url"] = model_config.ollama_base_url
        return ChatOllama(**kwargs)

    raise ValueError(
        "Unsupported `llm_provider` in config/model.yml. "
        "Use `dashscope` or `ollama`."
    )


@lru_cache(maxsize=1)
def get_agent_model():
    return _build_chat_model(model_config.agent_model_name)


@lru_cache(maxsize=1)
def get_rag_model():
    return _build_chat_model(model_config.rag_chain_model_name)


@lru_cache(maxsize=1)
def get_chat_model():
    return get_agent_model()


@lru_cache(maxsize=1)
def get_embedding_model():
    if model_config.embedding_provider == "dashscope":
        from langchain_community.embeddings import DashScopeEmbeddings

        return DashScopeEmbeddings(
            model=model_config.embedding_model_name,
            dashscope_api_key=_require_env("DASHSCOPE_API_KEY"),
        )

    if model_config.embedding_provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        kwargs: dict[str, str] = {"model": model_config.embedding_model_name}
        if model_config.ollama_base_url:
            kwargs["base_url"] = model_config.ollama_base_url
        return OllamaEmbeddings(**kwargs)

    raise ValueError(
        "Unsupported `embedding_provider` in config/model.yml. "
        "Use `dashscope` or `ollama`."
    )
