# src/agent/nodes/handlers/homework.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from src.rag.engine import get_rag_engine
from config.prompts import HOMEWORK_GUIDANCE_PROMPT


class HomeworkHandler(BaseHandler):
    """作业辅导处理器"""

    def __init__(self):
        self._llm_client = None
        self._rag_engine = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            self._rag_engine = get_rag_engine()
        return self._rag_engine

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理作业辅导"""
        subject = slots.get("subject", "")
        question = slots.get("question", "")

        logger.info(f"作业辅导: subject={subject}, question={question[:50]}...")

        # 检索相关知识点
        docs = await self.rag_engine.retrieve(question, top_k=2, subject=subject)

        # 构建知识点上下文
        knowledge_context = "\n".join([doc["content"] for doc in docs]) if docs else "暂无相关知识点"

        # 使用引导式教学prompt
        prompt = HOMEWORK_GUIDANCE_PROMPT.format(
            subject=subject,
            question=question,
            knowledge_context=knowledge_context
        )

        response = await self.llm_client.generate(prompt)

        return response
