from pathlib import Path
from loguru import logger

from .base import BaseLoader


class TxtLoader(BaseLoader):
    """TXT文本加载器"""

    def load(self) -> str:
        """加载TXT内容"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                text = f.read()

            logger.debug(f"TXT加载完成: {self.file_path.name}, {len(text)} 字符")

            return text
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(self.file_path, "r", encoding="gbk") as f:
                text = f.read()
            return text
        except Exception as e:
            logger.error(f"TXT加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为TXT文件"""
        from pathlib import Path
        return Path(file_path).suffix.lower() in [".txt", ".md"]
