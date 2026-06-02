# src/agent/nodes/router.py

from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState


def router_node(state: AgentState) -> Dict[str, Any]:
    """路由节点 - 透传状态，实际路由由条件边函数决定"""
    intent = state.get("intent", "chitchat")

    logger.info(f"路由到: {intent}")

    # 节点必须返回dict，路由决策由conditional_edges的lambda函数完成
    return {}
