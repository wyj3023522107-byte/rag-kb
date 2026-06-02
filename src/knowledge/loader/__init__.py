from typing import Optional
from pathlib import Path
from loguru import logger

from .base import BaseLoader
from .pdf_loader import PDFLoader
from .docx_loader import DocxLoader
from .txt_loader import TxtLoader


# 注册的加载器列表
LOADERS = [PDFLoader, DocxLoader, TxtLoader]


def get_loader(file_path: str) -> Optional[BaseLoader]:
    """根据文件类型获取对应的加载器"""
    for loader_cls in LOADERS:
        if loader_cls.supports(file_path):
            return loader_cls(file_path)

    logger.warning(f"不支持的文件类型: {file_path}")
    return None


def get_supported_extensions() -> list:
    """获取支持的文件扩展名"""
    return [".pdf", ".docx", ".doc", ".txt", ".md"]
