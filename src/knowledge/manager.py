import uuid
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings
from .loader import get_loader
from .splitter import DocumentSplitter, DocumentChunk
from src.storage.vector_store import get_vector_store, VectorStore
from src.storage.keyword_index import get_keyword_index, KeywordIndex
from src.storage.metadata_store import get_metadata_store, MetadataStore
from src.llm.embeddings import get_embedding_client, EmbeddingClient


@dataclass
class UploadResult:
    """上传结果"""
    doc_id: str
    chunk_count: int
    filename: str


@dataclass
class DocumentInfo:
    """文档信息"""
    doc_id: str
    filename: str
    subject: str
    chunk_count: int
    create_time: str


class KnowledgeManager:
    """知识库管理器"""

    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size

        self._vector_store: Optional[VectorStore] = None
        self._keyword_index: Optional[KeywordIndex] = None
        self._metadata_store: Optional[MetadataStore] = None
        self._embedding_client: Optional[EmbeddingClient] = None
        self._splitter: Optional[DocumentSplitter] = None

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    @property
    def keyword_index(self) -> KeywordIndex:
        if self._keyword_index is None:
            self._keyword_index = get_keyword_index()
        return self._keyword_index

    @property
    def metadata_store(self) -> MetadataStore:
        if self._metadata_store is None:
            self._metadata_store = get_metadata_store()
        return self._metadata_store

    @property
    def embedding_client(self) -> EmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    @property
    def splitter(self) -> DocumentSplitter:
        if self._splitter is None:
            self._splitter = DocumentSplitter()
        return self._splitter

    async def upload(
        self,
        file_path: str,
        subject: str,
        grade_range: Optional[List[str]] = None,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> UploadResult:
        """上传文档到知识库"""
        logger.info(f"开始上传文档: {file_path}")

        # 生成文档ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        filename = Path(file_path).name

        # 1. 加载文档
        loader = get_loader(file_path)
        if loader is None:
            raise ValueError(f"不支持的文件类型: {filename}")

        text = loader.load()

        # 2. 切分文档
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "subject": subject,
            "grade_range": grade_range or [],
            "title": title or filename,
            "keywords": keywords or []
        }

        chunks = self.splitter.split(text, metadata)

        if not chunks:
            raise ValueError("文档内容为空")

        # 3. 向量化并存储
        await self._embed_and_store(chunks)

        # 4. 保存元数据
        self.metadata_store.save(doc_id, {
            **metadata,
            "chunk_count": len(chunks),
            "file_type": Path(file_path).suffix,
            "create_time": datetime.now().isoformat()
        })

        logger.info(f"文档上传完成: doc_id={doc_id}, chunks={len(chunks)}")

        return UploadResult(
            doc_id=doc_id,
            chunk_count=len(chunks),
            filename=filename
        )

    async def _embed_and_store(self, chunks: List[DocumentChunk]) -> None:
        """向量化并存储"""
        total = len(chunks)

        for i in range(0, total, self.batch_size):
            batch = chunks[i:i + self.batch_size]

            # 批量获取embedding
            texts = [chunk.content for chunk in batch]
            embeddings = self.embedding_client.embed_documents(texts)

            # 存储到向量库
            self.vector_store.add(
                ids=[chunk.id for chunk in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[chunk.metadata for chunk in batch]
            )

            # 存储到关键词索引
            self.keyword_index.add([
                {"doc_id": chunk.id, "content": chunk.content, "metadata": chunk.metadata}
                for chunk in batch
            ])

            logger.debug(f"处理批次 {i//self.batch_size + 1}/{(total-1)//self.batch_size + 1}")

    def list(self, subject: Optional[str] = None) -> List[DocumentInfo]:
        """列出文档"""
        metadata_list = self.metadata_store.list(subject=subject)

        return [
            DocumentInfo(
                doc_id=m["doc_id"],
                filename=m["filename"],
                subject=m["subject"],
                chunk_count=m.get("chunk_count", 0),
                create_time=m.get("create_time", "")
            )
            for m in metadata_list
        ]

    def delete(self, doc_id: str) -> bool:
        """删除文档"""
        logger.info(f"删除文档: {doc_id}")

        # 1. 从元数据获取所有切片ID
        metadata = self.metadata_store.get(doc_id)
        if not metadata:
            return False

        # 2. 从向量库删除
        self.vector_store.delete_by_metadata({"doc_id": doc_id})

        # 3. 从关键词索引删除
        results = self.vector_store.get(where={"doc_id": doc_id})
        if results.get("ids"):
            self.keyword_index.delete(results["ids"])

        # 4. 删除元数据
        self.metadata_store.delete(doc_id)

        logger.info(f"文档删除完成: {doc_id}")
        return True

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.metadata_store.stats()


# 全局实例
_manager: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    """获取知识库管理器实例"""
    global _manager
    if _manager is None:
        _manager = KnowledgeManager()
    return _manager
