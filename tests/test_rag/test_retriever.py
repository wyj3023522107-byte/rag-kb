# tests/test_rag/test_retriever.py

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# 在导入任何模块之前设置环境变量
os.environ["DASHSCOPE_API_KEY"] = "test-api-key-for-testing"


class TestHybridRetriever:
    """混合检索器测试"""

    @pytest.mark.asyncio
    async def test_search_combines_results(self):
        """测试搜索合并结果"""
        # Mock the dependencies at the class level
        mock_vector_store = Mock()
        mock_vector_store.search = Mock(return_value=[
            {"doc_id": "doc1", "content": "内容1", "score": 0.9, "metadata": {}}
        ])

        mock_keyword_index = Mock()
        mock_keyword_index.search = Mock(return_value=[
            {"doc_id": "doc2", "content": "内容2", "score": 0.8, "metadata": {}}
        ])

        mock_embedding_client = Mock()
        mock_embedding_client.embed_query = Mock(return_value=[0.1] * 1536)

        # Import after setting environment variable
        from src.rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        # Inject mocks
        retriever._vector_store = mock_vector_store
        retriever._keyword_index = mock_keyword_index
        retriever._embedding_client = mock_embedding_client

        results = await retriever.search("测试查询", top_k=5)

        assert len(results) > 0
        # Should have merged results from both searches
        assert len(results) <= 5

    def test_rrf_fusion(self):
        """测试RRF融合算法"""
        from src.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        vector_results = [
            {"doc_id": "doc1", "content": "内容1"},
            {"doc_id": "doc2", "content": "内容2"},
        ]
        keyword_results = [
            {"doc_id": "doc2", "content": "内容2"},
            {"doc_id": "doc3", "content": "内容3"},
        ]

        results = retriever._rrf_fusion(vector_results, keyword_results, top_k=3)

        assert len(results) == 3
        # doc2 should rank first (appears in both lists)
        assert results[0]["doc_id"] == "doc2"
        # Each result should have rrf_score
        for result in results:
            assert "rrf_score" in result

    def test_rrf_fusion_empty_results(self):
        """测试空结果的RRF融合"""
        from src.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        # Empty vector results
        results = retriever._rrf_fusion([], [{"doc_id": "doc1", "content": "内容1"}], top_k=5)
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"

        # Empty keyword results
        results = retriever._rrf_fusion([{"doc_id": "doc1", "content": "内容1"}], [], top_k=5)
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"

        # Both empty
        results = retriever._rrf_fusion([], [], top_k=5)
        assert len(results) == 0

    def test_rrf_fusion_same_documents(self):
        """测试相同文档的RRF融合"""
        from src.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        # Same document appears in both lists
        vector_results = [
            {"doc_id": "doc1", "content": "相同内容"},
        ]
        keyword_results = [
            {"doc_id": "doc1", "content": "相同内容"},
        ]

        results = retriever._rrf_fusion(vector_results, keyword_results, top_k=5)

        assert len(results) == 1
        # Score should be higher since it appears in both
        assert results[0]["rrf_score"] > 0
