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
        """生成回答（有知识库参考时使用）"""
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

    async def generate_without_context(
        self,
        query: str,
        subject: str = "",
        grade: str = ""
    ) -> str:
        """生成回答（无知识库参考，使用大模型通用知识）"""
        prompt = f"""你是一位专业的K12学习辅导老师，请用你的知识回答学生的问题。

学科: {subject or "通用"}
年级: {grade or "中学"}

学生问题: {query}

请给出详细、准确的回答，适合学生理解。如果涉及知识点，可以适当举例说明。"""

        response = await self.llm_client.generate(prompt)
        logger.debug(f"通用知识回答完成: {len(response)} 字符")
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
