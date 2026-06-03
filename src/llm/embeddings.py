# src/llm/embeddings.py

from typing import List, Optional
from loguru import logger
from openai import OpenAI

from config.settings import settings


class EmbeddingClient:
    """Embedding客户端封装 - 支持硅基流动API"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._client = None
        self._init_client()

    def _init_client(self):
        """初始化OpenAI兼容客户端"""
        api_key = settings.EMBEDDING_API_KEY
        base_url = settings.EMBEDDING_BASE_URL

        if not api_key:
            raise ValueError("EMBEDDING_API_KEY 未配置，请在 .env 文件中设置")

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"Embedding客户端初始化完成: model={self.model_name}, base_url={base_url}")

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        try:
            response = self._client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug(f"成功嵌入查询，维度: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Embedding查询失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        if not texts:
            return []

        try:
            # 批量处理，每次最多100个
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self._client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.debug(f"嵌入批次 {i // batch_size + 1}: {len(batch)} 个文档")

            logger.info(f"成功嵌入 {len(all_embeddings)} 个文档")
            return all_embeddings
        except Exception as e:
            logger.error(f"批量Embedding失败: {e}")
            raise

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入单个查询"""
        return self.embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入多个文档"""
        return self.embed_documents(texts)


# 全局实例
_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """获取Embedding客户端实例"""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client
