import pytest
import tempfile
from pathlib import Path
import json


class TestMetadataStore:
    """元数据存储测试"""

    def test_save_and_get_metadata(self):
        """测试保存和获取元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            metadata = {
                "doc_id": "doc_001",
                "filename": "test.pdf",
                "subject": "数学",
                "chunk_count": 10
            }

            store.save("doc_001", metadata)

            result = store.get("doc_001")

            assert result["doc_id"] == "doc_001"
            assert result["filename"] == "test.pdf"

    def test_list_metadata(self):
        """测试列出元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            store.save("doc_001", {"doc_id": "doc_001", "subject": "数学"})
            store.save("doc_002", {"doc_id": "doc_002", "subject": "物理"})

            results = store.list()

            assert len(results) == 2

    def test_delete_metadata(self):
        """测试删除元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            store.save("doc_001", {"doc_id": "doc_001"})
            store.delete("doc_001")

            result = store.get("doc_001")

            assert result is None
