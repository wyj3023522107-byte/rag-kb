import chromadb
from chromadb.config import Settings
from typing import List, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from config.settings import settings


class VectorStore:
    """向量存储封装"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_dir: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR

        # 确保目录存在
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端
        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建集合
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"向量存储初始化完成: collection={collection_name}, path={self.persist_dir}")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """添加向量"""
        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            count = len(ids)
            logger.debug(f"成功添加 {count} 个向量")
            return count
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise

    def search(
        self,
        embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # 格式化结果
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "doc_id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1 - results["distances"][0][i] if results["distances"] else 0
                    })

            logger.debug(f"检索返回 {len(formatted)} 条结果")
            return formatted
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise

    def delete(self, ids: List[str]) -> int:
        """删除向量"""
        try:
            self._collection.delete(ids=ids)
            count = len(ids)
            logger.debug(f"成功删除 {count} 个向量")
            return count
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise

    def delete_by_metadata(self, where: Dict[str, Any]) -> int:
        """按元数据删除"""
        try:
            # 先查询符合条件的ID
            results = self._collection.get(where=where)
            if results["ids"]:
                self._collection.delete(ids=results["ids"])
                count = len(results["ids"])
                logger.debug(f"按条件删除 {count} 个向量")
                return count
            return 0
        except Exception as e:
            logger.error(f"按条件删除失败: {e}")
            raise

    def count(self) -> int:
        """获取向量数量"""
        return self._collection.count()

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取向量"""
        return self._collection.get(ids=ids, where=where, include=["documents", "metadatas"])

    def get_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取指定文档的所有切片"""
        try:
            results = self._collection.get(
                where={"doc_id": doc_id},
                include=["documents", "metadatas"]
            )

            chunks = []
            if results["ids"]:
                for i, chunk_id in enumerate(results["ids"]):
                    chunks.append({
                        "chunk_id": chunk_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })

            logger.debug(f"获取文档 {doc_id} 的 {len(chunks)} 个切片")
            return chunks
        except Exception as e:
            logger.error(f"获取文档切片失败: {e}")
            return []


# 全局实例
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
