# src/agent/state.py

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """Agent状态"""
    # 输入
    query: str                           # 用户原始输入
    session_id: Optional[str]            # 会话ID

    # 意图识别
    intent: Optional[str]                # 识别的意图
    intent_confidence: Optional[float]   # 意图置信度

    # 槽位填充
    slots: Optional[Dict[str, Any]]      # 槽位信息
    slots_complete: Optional[bool]       # 槽位是否完整
    missing_slots: Optional[List[str]]   # 缺失的槽位

    # 追问
    ask_question: Optional[str]          # 追问内容

    # 响应
    response: Optional[str]              # 最终响应

    # 上下文
    history: Optional[List[Dict[str, str]]]  # 对话历史
    context: Optional[Dict[str, Any]]    # 上下文信息


# 槽位定义
SLOT_DEFINITIONS = {
    "study_qa": {
        "subject": {"type": "enum", "required": True, "values": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]},
        "grade": {"type": "enum", "required": False, "values": ["小学", "初一", "初二", "初三", "高一", "高二", "高三"]},
        "topic": {"type": "string", "required": True}
    },
    "homework_help": {
        "subject": {"type": "enum", "required": True, "values": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]},
        "question": {"type": "string", "required": True}
    },
    "emotion_support": {
        "emotion_type": {"type": "enum", "required": False, "values": ["焦虑", "沮丧", "愤怒", "迷茫", "压力"]},
        "context": {"type": "string", "required": False}
    },
    "chitchat": {}
}

# 必填槽位
REQUIRED_SLOTS = {
    "study_qa": ["subject", "topic"],
    "homework_help": ["subject", "question"],
    "emotion_support": [],
    "chitchat": []
}
