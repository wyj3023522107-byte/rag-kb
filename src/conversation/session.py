# src/conversation/session.py

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
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
    """会话管理器 - 支持数据库持久化"""

    def __init__(self, max_sessions: int = 100, use_db: bool = True):
        self.max_sessions = max_sessions
        self.use_db = use_db
        self._sessions: Dict[str, Session] = {}  # 内存缓存
        self._db = None

        if use_db:
            from src.storage.session_db import get_session_db
            self._db = get_session_db()
            logger.info("会话管理器已启用数据库持久化")

    def create(self) -> Session:
        """创建新会话"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = Session(session_id=session_id)

        self._sessions[session_id] = session

        # 保存到数据库
        if self._db:
            self._db.create_session(session_id, session.context)

        self._cleanup()

        logger.debug(f"创建会话: {session_id}")
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        # 先查内存缓存
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 从数据库加载
        if self._db:
            data = self._db.get_session(session_id)
            if data:
                session = Session(
                    session_id=data["session_id"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    messages=data["messages"],
                    context=data["context"]
                )
                self._sessions[session_id] = session
                return session

        return None

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """获取或创建会话"""
        if session_id:
            session = self.get(session_id)
            if session:
                return session
        return self.create()

    def save_message(self, session_id: str, role: str, content: str, intent: str = None):
        """保存消息"""
        # 保存到数据库
        if self._db:
            self._db.add_message(session_id, role, content, intent)

        # 更新内存缓存
        if session_id in self._sessions:
            self._sessions[session_id].messages.append({
                "role": role,
                "content": content,
                "intent": intent,
                "timestamp": datetime.now().isoformat()
            })

    def delete(self, session_id: str) -> bool:
        """删除会话"""
        # 从内存删除
        if session_id in self._sessions:
            del self._sessions[session_id]

        # 从数据库删除
        if self._db:
            return self._db.delete_session(session_id)

        return False

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """列出最近的会话"""
        if self._db:
            return self._db.list_sessions(limit)

        # 降级到内存
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True
        )[:limit]

        return [
            {"session_id": s.session_id, "updated_at": s.updated_at.isoformat()}
            for s in sessions
        ]

    def _cleanup(self):
        """清理过期会话（仅内存）"""
        if len(self._sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].updated_at
            )
            to_remove = len(self._sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                del self._sessions[session_id]

            logger.debug(f"清理了 {to_remove} 个内存会话缓存")


# 全局实例
_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
