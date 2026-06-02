# src/agent/nodes/handlers/chitchat.py

import json
import re
from typing import Dict, Any, List, Optional
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from src.agent.tools import get_tool_manager
from config.prompts import CHITCHAT_PROMPT


# 时间相关关键词
TIME_KEYWORDS = [
    "几点", "现在时间", "当前时间", "什么时间",
    "今天几号", "今天日期", "几月几号", "几月几日",
    "星期几", "周几", "今天是星期", "今天是周",
    "现在日期", "当前日期", "今天是什么日子"
]


class ChitchatHandler(BaseHandler):
    """闲聊处理器（支持工具调用）"""

    def __init__(self):
        self._llm_client = None
        self._tool_manager = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    @property
    def tool_manager(self):
        if self._tool_manager is None:
            self._tool_manager = get_tool_manager()
        return self._tool_manager

    def _check_need_time_tool(self, query: str) -> Optional[str]:
        """检查是否需要调用时间工具，返回format参数"""
        query_lower = query.lower()

        for keyword in TIME_KEYWORDS:
            if keyword in query_lower:
                # 判断需要什么格式
                if "星期" in query or "周几" in query:
                    return "weekday"
                elif "几点" in query or "时间" in query:
                    return "datetime"
                elif "几号" in query or "日期" in query or "几月" in query:
                    return "date"
                else:
                    return "datetime"
        return None

    async def _call_tool(self, tool_name: str, **kwargs) -> Optional[str]:
        """调用工具并返回结果"""
        try:
            result = await self.tool_manager.execute(tool_name, **kwargs)
            if result.success:
                return str(result.data)
            else:
                logger.warning(f"工具执行失败: {result.error}")
                return None
        except Exception as e:
            logger.error(f"工具调用异常: {e}")
            return None

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理闲聊（支持工具调用）"""
        # 从历史获取用户输入
        query = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    query = h["content"]
                    break

        logger.info(f"闲聊: query={query[:50]}...")

        # 检查是否需要调用时间工具
        time_format = self._check_need_time_tool(query)
        if time_format:
            logger.info(f"检测到时间查询需求，format={time_format}")
            time_result = await self._call_tool("get_current_time", format=time_format)
            if time_result:
                # 用自然语言回复
                return f"现在是 {time_result}。"

        # 普通闲聊
        prompt = CHITCHAT_PROMPT.format(query=query)
        response = await self.llm_client.generate(prompt)

        return response
