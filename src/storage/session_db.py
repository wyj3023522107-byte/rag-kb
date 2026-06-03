# src/storage/session_db.py

import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from loguru import logger

from config.settings import settings


class SessionDB:
    """会话数据库存储"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "./data/sessions.db"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                context TEXT DEFAULT '{}',
                title TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"会话数据库初始化完成: {self.db_path}")

    def create_session(self, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建会话（如果已存在则忽略）"""
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        # 使用 INSERT OR IGNORE 避免重复创建
        cursor.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at, context) VALUES (?, ?, ?, ?)",
            (session_id, now, now, json.dumps(context or {}, ensure_ascii=False))
        )

        conn.commit()
        conn.close()

        return {
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "context": context or {},
            "messages": []
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT session_id, created_at, updated_at, context, title FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # 获取消息
        cursor.execute(
            "SELECT role, content, intent, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        messages = [
            {"role": row[0], "content": row[1], "intent": row[2], "timestamp": row[3]}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "session_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "context": json.loads(row[3]),
            "title": row[4] or "",
            "messages": messages
        }

    def update_session(self, session_id: str, context: Dict[str, Any] = None):
        """更新会话"""
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        if context is not None:
            cursor.execute(
                "UPDATE sessions SET updated_at = ?, context = ? WHERE session_id = ?",
                (now, json.dumps(context, ensure_ascii=False), session_id)
            )
        else:
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id)
            )

        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str, intent: str = None):
        """添加消息"""
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (session_id, role, content, intent, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, intent, timestamp)
        )

        # 更新会话时间
        cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (timestamp, session_id)
        )

        # 如果是第一条用户消息，设置为标题
        if role == "user":
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ? AND role = 'user'",
                (session_id,)
            )
            user_msg_count = cursor.fetchone()[0]
            if user_msg_count == 1:
                # 截取前30个字符作为标题
                title = content[:30] + ("..." if len(content) > 30 else "")
                cursor.execute(
                    "UPDATE sessions SET title = ? WHERE session_id = ?",
                    (title, session_id)
                )

        conn.commit()
        conn.close()

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出最近的会话"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT session_id, created_at, updated_at, title FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )

        sessions = [
            {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "title": row[3] or "新对话"
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return sessions

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        conn.close()

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages
        }


# 全局实例
_db: Optional[SessionDB] = None


def get_session_db() -> SessionDB:
    """获取会话数据库实例"""
    global _db
    if _db is None:
        _db = SessionDB()
    return _db
