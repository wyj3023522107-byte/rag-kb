# src/services/streaming.py

from typing import AsyncGenerator, Optional, Dict, Any
from loguru import logger

from src.llm.client import get_llm_client
from src.conversation.session import get_session_manager
from config.prompts import CHITCHAT_PROMPT, EMOTION_SUPPORT_PROMPT


class StreamingChatService:
    """流式聊天服务"""

    def __init__(self):
        self._session_manager = get_session_manager()

    async def chat_stream(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天"""
        from src.agent.nodes.intent_classifier import intent_classifier_node

        # 1. 获取或创建会话
        session = self._session_manager.get_or_create(session_id)

        yield {"type": "session", "session_id": session.session_id}

        # 2. 意图识别（快速，非流式）
        state = {
            "query": query,
            "history": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in (session.messages[-10:] if session.messages else [])
            ]
        }

        try:
            intent_result = intent_classifier_node(state)
            intent = intent_result.get("intent", "chitchat")
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            intent = "chitchat"

        yield {"type": "intent", "intent": intent}

        # 3. 根据意图选择prompt
        prompt = self._build_prompt(query, intent, session.messages[-10:] if session.messages else [])

        # 4. 流式生成响应
        llm_client = get_llm_client()
        full_response = ""

        async for chunk in llm_client.stream(prompt):
            full_response += chunk
            yield {"type": "content", "content": chunk}

        # 5. 保存消息
        self._session_manager.save_message(session.session_id, "user", query, intent)
        self._session_manager.save_message(session.session_id, "assistant", full_response)

        yield {"type": "done"}

    def _build_prompt(self, query: str, intent: str, history: list) -> str:
        """构建prompt"""
        if intent == "emotion_support":
            return EMOTION_SUPPORT_PROMPT.format(query=query)
        else:
            # study_qa, homework_help, chitchat
            return CHITCHAT_PROMPT.format(query=query)


# 全局实例
_service: Optional[StreamingChatService] = None


def get_streaming_service() -> StreamingChatService:
    """获取流式服务实例"""
    global _service
    if _service is None:
        _service = StreamingChatService()
    return _service
