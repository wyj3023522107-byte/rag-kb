import pytest
import tempfile
from pathlib import Path


class TestKeywordIndex:
    """关键词索引测试"""

    def test_init_creates_index(self):
        """测试初始化创建索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            assert index is not None

    def test_add_and_search(self):
        """测试添加和搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            # 添加文档
            docs = [
                {"doc_id": "doc1", "content": "勾股定理是几何学中的重要定理"},
                {"doc_id": "doc2", "content": "函数单调性描述函数的变化规律"}
            ]
            index.add(docs)

            # 搜索
            results = index.search("勾股定理", top_k=2)

            assert len(results) > 0

    def test_delete(self):
        """测试删除"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            # 添加文档
            docs = [
                {"doc_id": "doc1", "content": "勾股定理是几何学中的重要定理"}
            ]
            index.add(docs)

            # 删除
            index.delete(["doc1"])

            # 搜索应该为空
            results = index.search("勾股定理", top_k=2)

            assert len(results) == 0
