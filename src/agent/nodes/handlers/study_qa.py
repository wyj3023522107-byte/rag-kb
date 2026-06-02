# src/agent/nodes/handlers/study_qa.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.rag.engine import get_rag_engine


class StudyQAHandler(BaseHandler):
    """学科问答处理器"""

    def __init__(self):
        self._rag_engine = None

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
        """处理学科问答"""
        subject = slots.get("subject", "")
        grade = slots.get("grade", "")
        topic = slots.get("topic", "")

        logger.info(f"学科问答: subject={subject}, topic={topic}")

        # 构建检索query
        query = f"{subject} {topic}" if subject else topic

        # 调用RAG生成回答
        response = await self.rag_engine.generate(
            query=query,
            subject=subject,
            grade=grade,
            top_k=3
        )

        return response
