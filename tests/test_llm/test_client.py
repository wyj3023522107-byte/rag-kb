import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestLLMClient:
    """LLM客户端测试"""

    @pytest.mark.asyncio
    async def test_generate_returns_response(self):
        """测试生成响应"""
        with patch("src.llm.client.Tongyi") as mock_tongyi:
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value="这是测试响应")
            mock_tongyi.return_value = mock_instance

            from src.llm.client import LLMClient

            client = LLMClient()
            result = await client.generate("你好")

            assert result == "这是测试响应"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """测试带系统提示的生成"""
        with patch("src.llm.client.Tongyi") as mock_tongyi:
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value="响应内容")
            mock_tongyi.return_value = mock_instance

            from src.llm.client import LLMClient

            client = LLMClient()
            result = await client.generate(
                "用户问题",
                system_prompt="你是一个助手"
            )

            # 验证调用了ainvoke
            mock_instance.ainvoke.assert_called_once()
            assert result == "响应内容"
