import uuid
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings
from .loader import get_loader
from .splitter import DocumentSplitter, DocumentChunk
from .classifier import get_document_classifier, DocumentClassifier
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
    category: str = ""
    auto_classified: bool = False


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
        self._classifier: Optional[DocumentClassifier] = None

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

    @property
    def classifier(self) -> DocumentClassifier:
        if self._classifier is None:
            self._classifier = get_document_classifier()
        return self._classifier

    async def upload(
        self,
        file_path: str,
        original_filename: Optional[str] = None,
        subject: Optional[str] = None,
        grade_range: Optional[List[str]] = None,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        auto_classify: bool = True
    ) -> UploadResult:
        """
        上传文档到知识库

        Args:
            file_path: 文件路径（可能是临时文件）
            original_filename: 原始文件名（可选，不填则从 file_path 推断）
            subject: 科目/分类（可选，不填则自动识别）
            grade_range: 适用年级（可选）
            title: 文档标题（可选）
            keywords: 关键词（可选）
            auto_classify: 是否启用智能分类（默认 True）
        """
        logger.info(f"开始上传文档: {file_path}")

        # 生成文档ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # 使用原始文件名，如果没有提供则从路径推断
        filename = original_filename or Path(file_path).name

        # 1. 加载文档
        loader = get_loader(file_path)
        if loader is None:
            raise ValueError(f"不支持的文件类型: {filename}")

        text = loader.load()

        # 2. 智能分类（如果启用且未指定分类）
        auto_classified = False
        category = subject or "未分类"
        doc_type = "其他"
        summary = ""
        confidence = 0.0

        if auto_classify and not subject:
            logger.info("启用智能分类...")
            classify_result = await self.classifier.classify(text, filename)
            category = classify_result.get("category", "未分类")
            doc_type = classify_result.get("doc_type", "其他")
            grade_range = grade_range or classify_result.get("grade_range", [])
            keywords = keywords or classify_result.get("keywords", [])
            summary = classify_result.get("summary", "")
            confidence = classify_result.get("confidence", 0.0)
            auto_classified = True
            logger.info(f"智能分类结果: {category} (置信度: {confidence})")

        # 3. 切分文档
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "subject": category,
            "title": title or filename,
            "doc_type": doc_type,
        }

        # 可选字段
        if grade_range:
            metadata["grade_range"] = grade_range
        if keywords:
            metadata["keywords"] = keywords
        if summary:
            metadata["summary"] = summary
        if auto_classified:
            metadata["auto_classified"] = True
            metadata["classify_confidence"] = confidence

        chunks = self.splitter.split(text, metadata)

        if not chunks:
            raise ValueError("文档内容为空")

        # 4. 向量化并存储
        await self._embed_and_store(chunks)

        # 5. 保存元数据
        self.metadata_store.save(doc_id, {
            **metadata,
            "chunk_count": len(chunks),
            "file_type": Path(file_path).suffix,
            "create_time": datetime.now().isoformat()
        })

        logger.info(f"文档上传完成: doc_id={doc_id}, chunks={len(chunks)}, category={category}")

        return UploadResult(
            doc_id=doc_id,
            chunk_count=len(chunks),
            filename=filename,
            category=category,
            auto_classified=auto_classified
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

        # 1. 从元数据获取文档信息
        metadata = self.metadata_store.get(doc_id)
        if not metadata:
            return False

        # 2. 先查询要删除的向量ID（删除前查询）
        results = self.vector_store.get(where={"doc_id": doc_id})
        chunk_ids = results.get("ids", [])

        # 3. 从关键词索引删除
        if chunk_ids:
            self.keyword_index.delete(chunk_ids)
            logger.debug(f"删除关键词索引: {len(chunk_ids)} 个")

        # 4. 从向量库删除
        if chunk_ids:
            self.vector_store.delete(chunk_ids)
            logger.debug(f"删除向量: {len(chunk_ids)} 个")

        # 5. 删除元数据
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
