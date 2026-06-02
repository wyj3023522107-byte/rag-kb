# src/agent/nodes/handlers/__init__.py

from .base import BaseHandler
from .study_qa import StudyQAHandler
from .homework import HomeworkHandler
from .emotion import EmotionHandler
from .chitchat import ChitchatHandler


# 处理器映射
HANDLERS = {
    "study_qa": StudyQAHandler,
    "homework_help": HomeworkHandler,
    "emotion_support": EmotionHandler,
    "chitchat": ChitchatHandler
}


def get_handler(intent: str):
    """获取意图对应的处理器"""
    handler_cls = HANDLERS.get(intent, ChitchatHandler)
    return handler_cls()
