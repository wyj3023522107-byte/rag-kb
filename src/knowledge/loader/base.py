from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class BaseLoader(ABC):
    """文档加载器基类"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

    @abstractmethod
    def load(self) -> str:
        """加载文档内容"""
        pass

    @classmethod
    @abstractmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否支持该文件类型"""
        pass
