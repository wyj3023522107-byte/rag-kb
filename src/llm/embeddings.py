# src/llm/embeddings.py

import os
from typing import List, Optional
from loguru import logger

from config.settings import settings


class EmbeddingClient:
    """Embedding客户端封装"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._client = None
        self._backend = None

        # 设置API Key
        os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY

        # 尝试初始化不同的后端
        self._init_backend()

    def _init_backend(self):
        """初始化Embedding后端"""
        # 方案1: 尝试本地模型
        try:
            from sentence_transformers import SentenceTransformer
            # 使用更小的中文模型
            self._client = SentenceTransformer('shibing624/text2vec-base-chinese')
            self._backend = 'local'
            logger.info("使用本地Embedding模型: text2vec-base-chinese")
            return
        except Exception as e:
            logger.debug(f"本地模型加载失败: {e}")

        # 方案2: 使用DashScope
        self._backend = 'dashscope'
        logger.info(f"使用DashScope Embedding: {self.model_name}")

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        if self._backend == 'local':
            return self._client.encode(text).tolist()

        # DashScope API
        from dashscope.embeddings import TextEmbedding
        try:
            response = TextEmbedding.call(
                model=self.model_name,
                input=text
            )
            if response.status_code == 200:
                return response.output['embeddings'][0]['embedding']
            else:
                raise Exception(f"Embedding失败: {response.code} - {response.message}")
        except Exception as e:
            logger.error(f"Embedding失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        if self._backend == 'local':
            embeddings = self._client.encode(texts, show_progress_bar=True)
            return [e.tolist() for e in embeddings]

        # DashScope API
        from dashscope.embeddings import TextEmbedding
        try:
            response = TextEmbedding.call(
                model=self.model_name,
                input=texts
            )
            if response.status_code == 200:
                embeddings = [item['embedding'] for item in response.output['embeddings']]
                logger.debug(f"成功嵌入 {len(texts)} 个文档")
                return embeddings
            else:
                raise Exception(f"批量Embedding失败: {response.code} - {response.message}")
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
