from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Optional
from loguru import logger

from config.settings import settings


class EmbeddingClient:
    """Embedding客户端封装"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL

        self._client = DashScopeEmbeddings(
            model=self.model_name,
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )

        logger.info(f"Embedding客户端初始化完成: model={self.model_name}")

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        try:
            embedding = self._client.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        try:
            embeddings = self._client.embed_documents(texts)
            logger.debug(f"成功嵌入 {len(texts)} 个文档")
            return embeddings
        except Exception as e:
            logger.error(f"批量Embedding失败: {e}")
            raise

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入单个查询"""
        try:
            embedding = await self._client.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"异步Embedding失败: {e}")
            raise

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入多个文档"""
        try:
            embeddings = await self._client.aembed_documents(texts)
            logger.debug(f"成功嵌入 {len(texts)} 个文档")
            return embeddings
        except Exception as e:
            logger.error(f"异步批量Embedding失败: {e}")
            raise


# 全局实例
_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """获取Embedding客户端实例"""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client
