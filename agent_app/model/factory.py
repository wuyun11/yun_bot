"""
模型工厂：根据配置生成聊天模型与各类 Embedding 模型实例。
"""
from abc import ABC, abstractmethod
from typing import Optional

from langchain_community.chat_models.tongyi import BaseChatModel, ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from agent_app.utils.config_handler import rag_config


class BaseModelFactory(ABC):
    """抽象模型工厂基类。"""

    @abstractmethod
    def generate_model(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂，生成 Tongyi 对话模型。"""

    def generate_model(self) -> ChatTongyi:
        return ChatTongyi(model=rag_config["chat_model_name"])


class EmbeddingModelFactory(BaseModelFactory):
    """嵌入模型工厂，生成 DashScope 文本 Embedding。"""

    def generate_model(self) -> DashScopeEmbeddings:
        return DashScopeEmbeddings(model=rag_config["embedding_model_name"])


class OllamaEmbeddingsModelFactory(BaseModelFactory):
    """本地嵌入模型工厂，生成 Ollama Embedding。"""

    def generate_model(self) -> OllamaEmbeddings:
        return OllamaEmbeddings(model=rag_config["local_embedding_model_name"])


# 全局模型实例，供各模块直接使用
chat_model: ChatTongyi = ChatModelFactory().generate_model()
embedding_model: DashScopeEmbeddings = EmbeddingModelFactory().generate_model()
ollama_embedding_model: OllamaEmbeddings = OllamaEmbeddingsModelFactory().generate_model()