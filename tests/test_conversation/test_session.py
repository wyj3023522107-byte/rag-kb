# tests/test_conversation/test_session.py

import pytest
from datetime import datetime


class TestSession:
    """会话测试"""

    def test_create_session(self):
        """测试创建会话"""
        from src.conversation.session import Session

        session = Session(session_id="test_123")

        assert session.session_id == "test_123"
        assert session.messages == []
        assert session.context == {}

    def test_session_touch(self):
        """测试更新时间戳"""
        from src.conversation.session import Session
        import time

        session = Session(session_id="test_123")
        old_time = session.updated_at

        time.sleep(0.01)
        session.touch()

        assert session.updated_at > old_time


class TestSessionManager:
    """会话管理器测试"""

    def test_create_session(self):
        """测试创建会话"""
        from src.conversation.session import SessionManager

        manager = SessionManager()
        session = manager.create()

        assert session.session_id.startswith("session_")
        assert session in manager._sessions.values()

    def test_get_session(self):
        """测试获取会话"""
        from src.conversation.session import SessionManager

        manager = SessionManager()
        created = manager.create()

        session = manager.get(created.session_id)

        assert session == created

    def test_get_or_create(self):
        """测试获取或创建"""
        from src.conversation.session import SessionManager

        manager = SessionManager()

        # 不存在时创建
        session1 = manager.get_or_create()
        assert session1 is not None

        # 存在时返回
        session2 = manager.get_or_create(session1.session_id)
        assert session2 == session1

    def test_delete_session(self):
        """测试删除会话"""
        from src.conversation.session import SessionManager

        manager = SessionManager()
        session = manager.create()

        result = manager.delete(session.session_id)

        assert result is True
        assert manager.get(session.session_id) is None

    def test_cleanup_old_sessions(self):
        """测试清理旧会话"""
        from src.conversation.session import SessionManager

        manager = SessionManager(max_sessions=3)

        # 创建超过限制的会话
        for _ in range(5):
            manager.create()

        assert len(manager._sessions) == 3


class TestConversationHistory:
    """对话历史测试"""

    def test_add_user_message(self):
        """测试添加用户消息"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory()
        msg = history.add_user_message("你好", intent="chitchat")

        assert len(history.messages) == 1
        assert history.messages[0].role == "user"
        assert history.messages[0].content == "你好"
        assert history.messages[0].intent == "chitchat"

    def test_add_assistant_message(self):
        """测试添加助手消息"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory()
        history.add_assistant_message("你好！有什么可以帮助你的吗？")

        assert len(history.messages) == 1
        assert history.messages[0].role == "assistant"

    def test_get_context(self):
        """测试获取上下文"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory()
        history.add_user_message("你好")
        history.add_assistant_message("你好！")

        context = history.get_context()

        assert "用户: 你好" in context
        assert "助手: 你好！" in context

    def test_get_llm_messages(self):
        """测试获取LLM格式消息"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory()
        history.add_user_message("你好")
        history.add_assistant_message("你好！")

        messages = history.get_llm_messages()

        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "你好"}

    def test_trim_history(self):
        """测试裁剪历史"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory(max_turns=2)

        # 添加超过限制的消息
        for i in range(6):
            history.add_user_message(f"消息{i}")

        # 应该只保留最后4条(2轮*2)
        assert len(history.messages) == 4

    def test_clear_history(self):
        """测试清空历史"""
        from src.conversation.history import ConversationHistory

        history = ConversationHistory()
        history.add_user_message("你好")
        history.clear()

        assert len(history.messages) == 0
