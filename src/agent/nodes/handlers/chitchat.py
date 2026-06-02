# src/agent/nodes/handlers/chitchat.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from config.prompts import CHITCHAT_PROMPT


class ChitchatHandler(BaseHandler):
    """闲聊处理器"""

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
        """处理闲聊"""
        # 从历史获取用户输入
        query = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    query = h["content"]
                    break

        logger.info(f"闲聊: query={query[:50]}...")

        prompt = CHITCHAT_PROMPT.format(query=query)

        response = await self.llm_client.generate(prompt)

        return response
