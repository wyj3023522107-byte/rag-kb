# src/rag/retriever.py

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from src.storage.vector_store import get_vector_store
from src.storage.keyword_index import get_keyword_index
from src.llm.embeddings import get_embedding_client


class HybridRetriever:
    """混合检索器 - 向量检索 + 关键词检索"""

    def __init__(self, rrf_k: int = 60):
        """
        Args:
            rrf_k: RRF融合参数
        """
        self.rrf_k = rrf_k

        self._vector_store = None
        self._keyword_index = None
        self._embedding_client = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    @property
    def keyword_index(self):
        if self._keyword_index is None:
            self._keyword_index = get_keyword_index()
        return self._keyword_index

    @property
    def embedding_client(self):
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    async def search(
        self,
        query: str,
        top_k: int = 10,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        # 并行执行向量检索和关键词检索
        vector_task = self._vector_search(query, top_k * 2, subject)
        keyword_task = self._keyword_search(query, top_k * 2, subject)

        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task
        )

        # RRF融合
        fused_results = self._rrf_fusion(vector_results, keyword_results, top_k)

        logger.debug(f"混合检索完成: 向量{len(vector_results)}条, 关键词{len(keyword_results)}条, 融合{len(fused_results)}条")
        return fused_results

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            embedding = self.embedding_client.embed_query(query)
            where = {"subject": subject} if subject else None
            results = self.vector_store.search(embedding, top_k, where)
            return results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            results = self.keyword_index.search(query, top_k, subject)
            return results
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    def _rrf_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """RRF融合算法"""
        scores = {}
        docs = {}

        # 向量检索结果打分
        for rank, doc in enumerate(vector_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.rrf_k + rank + 1)
            docs[doc_id] = doc

        # 关键词检索结果打分
        for rank, doc in enumerate(keyword_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.rrf_k + rank + 1)
            if doc_id not in docs:
                docs[doc_id] = doc

        # 按分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # 构建结果
        results = []
        for doc_id in sorted_ids[:top_k]:
            doc = docs[doc_id].copy()
            doc["rrf_score"] = scores[doc_id]
            results.append(doc)

        return results


# 全局实例
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """获取检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
