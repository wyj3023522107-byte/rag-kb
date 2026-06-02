# src/rag/engine.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from loguru import logger

from .retriever import get_retriever, HybridRetriever
from .reranker import Reranker
from .generator import get_generator, RAGGenerator


@dataclass
class SearchResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGEngine:
    """RAG引擎"""

    def __init__(self):
        self._retriever: Optional[HybridRetriever] = None
        self._reranker: Optional[Reranker] = None
        self._generator: Optional[RAGGenerator] = None

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    @property
    def reranker(self) -> Reranker:
        if self._reranker is None:
            self._reranker = Reranker()
        return self._reranker

    @property
    def generator(self) -> RAGGenerator:
        if self._generator is None:
            self._generator = get_generator()
        return self._generator

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        subject: Optional[str] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        logger.info(f"RAG检索: query={query[:50]}...")

        # 混合检索
        results = await self.retriever.search(query, top_k * 2, subject)

        # 重排序
        if rerank and results:
            results = await self.reranker.rerank(query, results, top_k)

        return results[:top_k]

    async def generate(
        self,
        query: str,
        subject: str = "",
        grade: str = "",
        top_k: int = 3
    ) -> str:
        """检索并生成回答"""
        # 检索
        docs = await self.retrieve(query, top_k=top_k, subject=subject)

        if not docs:
            # 知识库无相关内容，使用大模型通用知识回答
            logger.info("知识库无相关内容，使用大模型通用知识回答")
            response = await self.generator.generate_without_context(query, subject, grade)
            return response

        # 有知识库参考，生成回答
        response = await self.generator.generate(query, docs, subject, grade)

        return response


# 全局实例
_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """获取RAG引擎实例"""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
