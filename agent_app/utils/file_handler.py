"""
文件处理工具：MD5 计算、目录列举、PDF/TXT 加载为 LangChain Document。
"""
import hashlib
import os

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from agent_app.utils.logger_handler import logger


def get_file_md5_hex(file_path: str) -> str | None:
    """计算文件 MD5 并返回十六进制字符串；文件不存在或非文件则返回 None。"""
    if not os.path.exists(file_path):
        logger.error(f"[md5计算]文件不存在: {file_path}")
        return None
    if not os.path.isfile(file_path):
        logger.error(f"[md5计算]文件路径不是文件: {file_path}")
        return None
    md5_obj = hashlib.md5()

    chunk_size = 4096

    try:
        with open(file_path, "rb") as f:
            """
            chunk = f.read(chunk_size)
            while chunk:
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"[md5计算]文件计算md5值失败: {str(e)}")
        return None


def list_dir_with_allowed_type(dir_path: str, allowed_type: tuple[str, ...]) -> tuple[str, ...]:
    """列出指定目录下后缀在 allowed_type 中的文件路径元组；目录不存在则返回空元组。"""
    files: list[str] = []
    if not os.path.isdir(dir_path):
        logger.error(f"[文件列表]目录不存在: {dir_path}")
        return tuple()
    for f in os.listdir(dir_path):
        if f.endswith(allowed_type):
            files.append(os.path.join(dir_path, f))
    return tuple(files)


def pdf_loader(file_path: str, password: str = None) -> list[Document]:
    """加载 PDF 文件为 LangChain Document 列表。"""
    return PyPDFLoader(file_path, password=password).load()


def txt_loader(file_path: str, encoding: str = "utf-8") -> list[Document]:
    """加载 TXT 文件为 LangChain Document 列表。"""
    return TextLoader(file_path, encoding=encoding).load()
