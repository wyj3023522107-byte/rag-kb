from docx import Document
from pathlib import Path
from loguru import logger

from .base import BaseLoader


class DocxLoader(BaseLoader):
    """Word文档加载器"""

    def load(self) -> str:
        """加载Word内容"""
        try:
            doc = Document(self.file_path)
            text_parts = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            logger.debug(f"Word加载完成: {self.file_path.name}, {len(full_text)} 字符")

            return full_text
        except Exception as e:
            logger.error(f"Word加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为Word文件"""
        from pathlib import Path
        return Path(file_path).suffix.lower() in [".docx", ".doc"]
