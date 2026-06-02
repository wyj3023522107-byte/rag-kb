# src/agent/nodes/router.py

from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState


def router_node(state: AgentState) -> str:
    """路由节点 - 返回下一个节点名称"""
    intent = state.get("intent", "chitchat")

    logger.info(f"路由到: {intent}")

    return intent
