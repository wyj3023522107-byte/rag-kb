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

    # 出题意图的上下文信息
    quiz_context: Optional[Dict[str, Any]]  # 出题相关：学科、知识点、年级等

    # 响应
    response: Optional[str]              # 最终响应

    # 上下文
    history: Optional[List[Dict[str, str]]]  # 对话历史
    context: Optional[Dict[str, Any]]    # 上下文信息
