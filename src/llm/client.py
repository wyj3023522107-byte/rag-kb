from langchain_community.llms import Tongyi
from typing import Optional, List
from loguru import logger

from config.settings import settings


class LLMClient:
    """LLM客户端封装"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.model_name = model_name or settings.CHAT_MODEL
        self.temperature = temperature or settings.TEMPERATURE
        self.max_tokens = max_tokens or settings.MAX_TOKENS

        self._client = Tongyi(
            model_name=self.model_name,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=settings.TOP_P
        )

        logger.info(f"LLM客户端初始化完成: model={self.model_name}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """生成响应"""
        messages = []

        if system_prompt:
            messages.append(("system", system_prompt))

        messages.append(("human", prompt))

        try:
            response = await self._client.ainvoke(messages, stop=stop)
            logger.debug(f"LLM响应: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            raise

    async def classify(self, prompt: str, options: List[str]) -> str:
        """分类任务"""
        full_prompt = f"{prompt}\n\n请只从以下选项中选择一个: {', '.join(options)}"
        response = await self.generate(full_prompt)

        # 提取匹配的选项
        response = response.strip()
        for option in options:
            if option in response:
                return option

        return response


# 全局实例
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端实例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
