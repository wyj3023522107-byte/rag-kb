from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from config.settings import settings


@dataclass
class DocumentChunk:
    """文档切片"""
    id: str
    content: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata
        }


class DocumentSplitter:
    """文档切分器"""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", "；", "，", " "]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )

        logger.debug(f"文档切分器初始化: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")

    def split(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """切分文档"""
        if not text or not text.strip():
            return []

        # 执行切分
        texts = self._splitter.split_text(text)

        # 创建切片对象
        chunks = []
        base_metadata = metadata or {}

        for i, chunk_text in enumerate(texts):
            chunk_id = self._generate_id(chunk_text, i, base_metadata)

            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(texts)
                }
            )
            chunks.append(chunk)

        logger.debug(f"文档切分完成: {len(texts)} 个切片")
        return chunks

    def _generate_id(self, text: str, index: int, metadata: Dict[str, Any]) -> str:
        """生成切片ID"""
        import hashlib

        doc_id = metadata.get("doc_id", "unknown")
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]

        return f"{doc_id}_{index}_{content_hash}"
