import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings


class MetadataStore:
    """元数据存储（JSON文件）"""

    def __init__(self, metadata_dir: Optional[str] = None):
        self.metadata_dir = Path(metadata_dir or settings.METADATA_DIR)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"元数据存储初始化完成: path={self.metadata_dir}")

    def _get_file_path(self, doc_id: str) -> Path:
        """获取元数据文件路径"""
        return self.metadata_dir / f"{doc_id}.json"

    def save(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """保存元数据"""
        file_path = self._get_file_path(doc_id)

        # 添加时间戳
        metadata["updated_at"] = datetime.now().isoformat()
        if "created_at" not in metadata:
            metadata["created_at"] = metadata["updated_at"]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.debug(f"保存元数据: {doc_id}")

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取元数据"""
        file_path = self._get_file_path(doc_id)

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有元数据"""
        results = []

        for file_path in self.metadata_dir.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

                # 按学科过滤
                if subject and metadata.get("subject") != subject:
                    continue

                results.append(metadata)

        # 按创建时间排序
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return results

    def delete(self, doc_id: str) -> bool:
        """删除元数据"""
        file_path = self._get_file_path(doc_id)

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"删除元数据: {doc_id}")
            return True

        return False

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_metadata = self.list()

        total_docs = len(all_metadata)
        total_chunks = sum(m.get("chunk_count", 0) for m in all_metadata)

        # 按学科统计
        by_subject = {}
        for m in all_metadata:
            subject = m.get("subject", "未知")
            if subject not in by_subject:
                by_subject[subject] = {"docs": 0, "chunks": 0}
            by_subject[subject]["docs"] += 1
            by_subject[subject]["chunks"] += m.get("chunk_count", 0)

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "by_subject": by_subject,
            "storage_size_mb": self._get_storage_size()
        }

    def _get_storage_size(self) -> float:
        """获取存储大小（MB）"""
        total_size = 0
        for file_path in self.metadata_dir.glob("*.json"):
            total_size += file_path.stat().st_size

        # 加上向量库和索引大小
        chroma_path = Path(settings.CHROMA_PERSIST_DIR)
        if chroma_path.exists():
            for f in chroma_path.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

        bm25_path = Path(settings.BM25_INDEX_DIR)
        if bm25_path.exists():
            for f in bm25_path.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

        return round(total_size / (1024 * 1024), 2)


# 全局实例
_store: Optional[MetadataStore] = None


def get_metadata_store() -> MetadataStore:
    """获取元数据存储实例"""
    global _store
    if _store is None:
        _store = MetadataStore()
    return _store
