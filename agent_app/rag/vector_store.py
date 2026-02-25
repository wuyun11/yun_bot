"""
向量存储服务：Chroma 向量库的封装，支持从本地数据目录加载文档并检索。
"""
import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent_app.model.factory import ollama_embedding_model
from agent_app.utils.config_handler import chroma_config
from agent_app.utils.file_handler import pdf_loader, txt_loader, list_dir_with_allowed_type, get_file_md5_hex
from agent_app.utils.logger_handler import logger
from agent_app.utils.path_tool import get_abs_path


class VectorStoreService:
    """基于 Chroma 的向量存储与检索服务。"""

    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function=ollama_embedding_model,
            persist_directory=get_abs_path(chroma_config["persist_directory"]),
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_config["chunk_size"],
            chunk_overlap=chroma_config["chunk_overlap"],
            separators=chroma_config["separators"],
            length_function=len,
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """返回向量检索器，用于根据 query 检索文档。"""
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_config["k"]})

    def load_document(self):
        """从配置的数据目录加载文件并写入向量库；按文件 MD5 去重，已存在则跳过。"""

        def check_md5_hex(md5_for_check: str) -> bool:
            md5_hex_store_path = get_abs_path(chroma_config["md5_hex_store"])
            if not os.path.exists(md5_hex_store_path):
                # 如果md5.text文件不存在,则创建文件
                open(md5_hex_store_path, "w", encoding="utf-8").close()

            with open(md5_hex_store_path, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True
                return False

        def save_md5_hex(md5_for_check: str) -> None:
            md5_hex_store_path = get_abs_path(chroma_config["md5_hex_store"])
            with open(md5_hex_store_path, "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(file_path: str) -> list[Document]:
            if file_path.endswith(".pdf"):
                return pdf_loader(file_path)
            elif file_path.endswith(".txt"):
                return txt_loader(file_path)
            else:
                return []

        allowed_file_path: tuple[str, ...] = list_dir_with_allowed_type(
            get_abs_path(chroma_config["data_path"]),
            tuple(chroma_config["allow_knowledge_file_type"])
        )

        skipped_existing = 0
        for path in allowed_file_path:
            md5_hex = get_file_md5_hex(path)
            if check_md5_hex(md5_hex):
                skipped_existing += 1
                continue
            else:
                logger.info(f"[加载知识库]文件{path}内容不存在在知识库内,开始加载文件")
                documents: list[Document] = get_file_documents(path)
                try:
                    if not documents:
                        logger.warning(f"[加载知识库]文件{path}内没有有效文本内容,跳过加载")
                        continue
                    split_documents: list[Document] = self.splitter.split_documents(documents)

                    if not split_documents:
                        logger.warning(f"[加载知识库]文件{path}分片后没有有效文本内容,跳过加载")
                        continue
                    self.vector_store.add_documents(split_documents)
                    save_md5_hex(md5_hex)
                    logger.info(f"[加载知识库]文件{path}加载完成")
                except Exception as e:
                    logger.error(f"[加载知识库]文件{path}加载失败: {str(e)}", exc_info=True)

        if skipped_existing == len(allowed_file_path) and allowed_file_path:
            logger.info("[加载知识库]当前所有文件均已存在于知识库内，无需加载\n")


if __name__ == "__main__":
    vector_store_service = VectorStoreService()
    vector_store_service.load_document()
    retriever = vector_store_service.get_retriever()
    res = retriever.invoke("首次使用扫地机器人需要做什么？")
    for r in res:
        print(r.page_content)
        print("-" * 20)
