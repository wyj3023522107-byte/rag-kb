import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock


class TestVectorStore:
    """向量存储测试"""

    def test_init_creates_collection(self):
        """测试初始化创建集合"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.chromadb.PersistentClient") as mock_client_class:
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_client_class.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                assert store is not None
                mock_client.get_or_create_collection.assert_called_once()

    def test_add_documents(self):
        """测试添加文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.chromadb.PersistentClient") as mock_client_class:
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_client_class.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                ids = ["id1", "id2"]
                embeddings = [[0.1, 0.2], [0.3, 0.4]]
                documents = ["文档1", "文档2"]
                metadatas = [{"subject": "数学"}, {"subject": "物理"}]

                store.add(ids, embeddings, documents, metadatas)

                mock_collection.add.assert_called_once()

    def test_search_returns_results(self):
        """测试搜索返回结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.chromadb.PersistentClient") as mock_client_class:
                mock_client = Mock()
                mock_collection = Mock()
                mock_collection.query.return_value = {
                    "ids": [["id1", "id2"]],
                    "documents": [["文档1", "文档2"]],
                    "metadatas": [[{"subject": "数学"}, {"subject": "物理"}]],
                    "distances": [[0.1, 0.2]]
                }
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_client_class.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                results = store.search([0.1, 0.2], top_k=2)

                assert len(results) == 2
                assert results[0]["doc_id"] == "id1"
