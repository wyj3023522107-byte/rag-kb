# src/conversation/history.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


@dataclass
class Message:
    """消息"""
    role: str  # user / assistant / system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    slots: Optional[Dict[str, Any]] = None


class ConversationHistory:
    """对话历史"""

    def __init__(self, max_turns: int = None):
        self.max_turns = max_turns or settings.MAX_HISTORY_TURNS
        self.messages: List[Message] = []

    def add_user_message(
        self,
        content: str,
        intent: Optional[str] = None,
        slots: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加用户消息"""
        msg = Message(
            role="user",
            content=content,
            intent=intent,
            slots=slots
        )
        self.messages.append(msg)
        self._trim()
        logger.debug(f"添加用户消息: {content[:50]}...")
        return msg

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        msg = Message(role="assistant", content=content)
        self.messages.append(msg)
        self._trim()
        logger.debug(f"添加助手消息: {content[:50]}...")
        return msg

    def get_context(self, turns: Optional[int] = None) -> str:
        """获取对话上下文"""
        limit = turns or self.max_turns
        msgs = self.messages[-limit * 2:]

        lines = []
        for msg in msgs:
            role_name = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role_name}: {msg.content}")

        return "\n".join(lines)

    def get_llm_messages(self) -> List[Dict[str, str]]:
        """获取LLM格式的消息列表"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def clear(self):
        """清空历史"""
        self.messages.clear()
        logger.debug("对话历史已清空")

    def _trim(self):
        """裁剪历史"""
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "intent": msg.intent,
                "slots": msg.slots
            }
            for msg in self.messages
        ]
