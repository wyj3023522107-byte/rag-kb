# src/conversation/session.py

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


@dataclass
class Session:
    """会话"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def touch(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


class SessionManager:
    """会话管理器"""

    def __init__(self, max_sessions: int = 100):
        self.max_sessions = max_sessions
        self._sessions: Dict[str, Session] = {}

    def create(self) -> Session:
        """创建新会话"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = Session(session_id=session_id)

        self._sessions[session_id] = session
        self._cleanup()

        logger.debug(f"创建会话: {session_id}")
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """获取或创建会话"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create()

    def delete(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"删除会话: {session_id}")
            return True
        return False

    def _cleanup(self):
        """清理过期会话"""
        if len(self._sessions) > self.max_sessions:
            # 按更新时间排序，删除最旧的
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].updated_at
            )
            to_remove = len(self._sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                del self._sessions[session_id]

            logger.debug(f"清理了 {to_remove} 个过期会话")


# 全局实例
_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
