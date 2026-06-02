# src/rag/reranker.py

from typing import List, Dict, Any
from loguru import logger

from src.llm.client import get_llm_client


class Reranker:
    """重排序器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """重排序检索结果"""
        if not docs:
            return []

        if len(docs) <= top_k:
            return docs

        # 使用LLM打分
        scores = await self._llm_score(query, docs)

        # 合并分数并排序
        for doc, score in zip(docs, scores):
            doc["rerank_score"] = score

        sorted_docs = sorted(docs, key=lambda x: x["rerank_score"], reverse=True)

        logger.debug(f"重排序完成: {len(sorted_docs[:top_k])} 条结果")
        return sorted_docs[:top_k]

    async def _llm_score(
        self,
        query: str,
        docs: List[Dict[str, Any]]
    ) -> List[float]:
        """使用LLM对文档相关性打分"""
        import json

        # 构建prompt
        doc_list = "\n".join([
            f"{i}. {doc['content'][:200]}..."
            for i, doc in enumerate(docs)
        ])

        prompt = f"""请对以下文档与查询的相关性打分(0-10分,只输出数字)。
每个文档一行,输出JSON数组格式。

查询: {query}

文档列表:
{doc_list}

输出格式示例: [8, 5, 7, 3, ...]"""

        try:
            response = await self.llm_client.generate(prompt)
            # 解析JSON
            scores = json.loads(response.strip())
            if isinstance(scores, list) and len(scores) == len(docs):
                return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"LLM打分失败: {e}")

        # 降级：返回原始顺序的默认分数
        return [0.5] * len(docs)
