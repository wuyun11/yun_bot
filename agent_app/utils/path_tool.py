"""
路径工具：为整个工程提供基于项目根目录的绝对路径。
"""
import os


def get_project_path() -> str:
    """返回项目根目录的绝对路径（根据本文件位置推算）。"""
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    parent_dir = os.path.dirname(current_dir)
    project_path = os.path.dirname(parent_dir)
    return project_path


def get_abs_path(relative_path: str) -> str:
    """将相对于项目根目录的路径转为绝对路径。"""
    project_path = get_project_path()
    return os.path.normpath(os.path.join(project_path, relative_path))
