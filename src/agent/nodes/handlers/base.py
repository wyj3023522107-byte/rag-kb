# src/agent/nodes/handlers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseHandler(ABC):
    """意图处理器基类"""

    @abstractmethod
    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理意图，返回响应"""
        pass
