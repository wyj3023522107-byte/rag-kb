# src/rag/reranker.py

"""
重排序器 - 使用硅基流动 Rerank API

支持模型:
- BAAI/bge-reranker-v2-m3 (推荐，多语言)
- BAAI/bge-reranker-base
- jinaai/jina-reranker-v2-base-multilingual
"""

import httpx
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import settings


class Reranker:
    """重排序器 - API 调用方式"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.model = model or settings.RERANK_MODEL
        # 优先使用传入的 api_key，其次使用 RERANK_API_KEY，最后使用 EMBEDDING_API_KEY
        self.api_key = api_key or settings.RERANK_API_KEY or settings.EMBEDDING_API_KEY
        self.base_url = base_url or settings.RERANK_BASE_URL

        if not self.api_key:
            logger.warning("Rerank API Key 未配置，重排序功能将不可用")

    async def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        重排序检索结果

        Args:
            query: 查询文本
            docs: 文档列表，每个文档需包含 content 字段
            top_k: 返回前 K 个结果

        Returns:
            重排序后的文档列表，包含 rerank_score 字段
        """
        if not docs:
            return []

        if not self.api_key:
            logger.warning("Rerank API Key 未配置，返回原始顺序")
            # 为每个文档添加默认分数
            for doc in docs[:top_k]:
                doc["rerank_score"] = 0.5
            return docs[:top_k]

        if len(docs) <= top_k:
            # 仍然需要打分
            return await self._rerank_with_api(query, docs, len(docs))

        return await self._rerank_with_api(query, docs, top_k)

    async def _rerank_with_api(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """调用 Rerank API"""

        # 提取文档内容
        documents = [doc.get("content", "") for doc in docs]

        # 构建请求
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "return_documents": False,  # 不需要返回文档内容
            "top_n": top_k
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/rerank",
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"Rerank API 错误: {response.status_code} - {response.text}")
                    return docs[:top_k]

                data = response.json()
                results = data.get("results", [])

                # API 返回格式: [{"index": 0, "relevance_score": 0.95}, ...]
                # 按分数排序并构建结果
                reranked_docs = []
                for result in results:
                    idx = result.get("index", 0)
                    score = result.get("relevance_score", 0)

                    if idx < len(docs):
                        doc = docs[idx].copy()
                        doc["rerank_score"] = float(score)
                        reranked_docs.append(doc)

                logger.info(f"Rerank 完成: {len(reranked_docs)} 条结果, 分数范围: [{reranked_docs[-1]['rerank_score']:.3f}, {reranked_docs[0]['rerank_score']:.3f}]")
                return reranked_docs

        except httpx.TimeoutException:
            logger.error("Rerank API 超时")
            return docs[:top_k]
        except Exception as e:
            logger.error(f"Rerank 失败: {e}")
            return docs[:top_k]

    async def score(self, query: str, doc: str) -> float:
        """
        单个文档打分

        Args:
            query: 查询文本
            doc: 文档内容

        Returns:
            相关性分数 (0-1)
        """
        results = await self._rerank_with_api(query, [{"content": doc}], 1)
        return results[0].get("rerank_score", 0.0) if results else 0.0


# 全局实例
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """获取重排序器实例"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
