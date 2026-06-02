# src/agent/nodes/handlers/emotion.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from config.prompts import EMOTION_SUPPORT_PROMPT


class EmotionHandler(BaseHandler):
    """情绪疏导处理器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理情绪疏导"""
        emotion_type = slots.get("emotion_type", "压力")

        # 从历史获取用户倾诉内容
        query = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    query = h["content"]
                    break

        logger.info(f"情绪疏导: emotion_type={emotion_type}")

        prompt = EMOTION_SUPPORT_PROMPT.format(
            query=query,
            emotion_type=emotion_type
        )

        response = await self.llm_client.generate(prompt)

        return response
