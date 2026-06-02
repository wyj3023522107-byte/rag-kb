import pytest


class TestDocumentSplitter:
    """文档切分测试"""

    def test_split_short_text(self):
        """测试切分短文本"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=100, chunk_overlap=10)

        text = "这是一个短文本。"
        chunks = splitter.split(text)

        assert len(chunks) == 1
        assert chunks[0].content == "这是一个短文本。"

    def test_split_long_text(self):
        """测试切分长文本"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=50, chunk_overlap=10)

        text = "这是第一段内容。" * 10
        chunks = splitter.split(text)

        assert len(chunks) > 1

    def test_split_with_metadata(self):
        """测试带元数据的切分"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter()

        text = "这是测试内容。"
        metadata = {"subject": "数学", "source": "test.pdf"}

        chunks = splitter.split(text, metadata)

        assert chunks[0].metadata["subject"] == "数学"
        assert chunks[0].metadata["source"] == "test.pdf"
