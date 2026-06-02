import fitz  # PyMuPDF
from typing import List
from loguru import logger

from .base import BaseLoader


class PDFLoader(BaseLoader):
    """PDF文档加载器"""

    def load(self) -> str:
        """加载PDF内容"""
        try:
            doc = fitz.open(self.file_path)
            text_parts = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.debug(f"PDF加载完成: {self.file_path.name}, {len(full_text)} 字符")

            return full_text
        except Exception as e:
            logger.error(f"PDF加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为PDF文件"""
        from pathlib import Path
        return Path(file_path).suffix.lower() == ".pdf"
