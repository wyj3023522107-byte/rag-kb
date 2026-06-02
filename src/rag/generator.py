# src/rag/generator.py

from typing import List, Dict, Any, Optional
from loguru import logger

from src.llm.client import get_llm_client
from config.prompts import RAG_PROMPT


class RAGGenerator:
    """RAG回答生成器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def generate(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        subject: str = "",
        grade: str = ""
    ) -> str:
        """生成回答"""
        # 构建上下文
        context = self._build_context(docs)

        # 构建prompt
        prompt = RAG_PROMPT.format(
            query=query,
            subject=subject or "通用",
            grade=grade or "中学",
            context=context
        )

        # 调用LLM生成
        response = await self.llm_client.generate(prompt)

        logger.debug(f"RAG生成完成: {len(response)} 字符")
        return response

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []

        for i, doc in enumerate(docs, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("filename", "未知来源")
            context_parts.append(f"【参考资料{i}】(来源: {source})\n{content}\n")

        return "\n".join(context_parts)


# 全局实例
_generator: Optional[RAGGenerator] = None


def get_generator() -> RAGGenerator:
    """获取生成器实例"""
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator
