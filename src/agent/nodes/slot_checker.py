# src/agent/nodes/slot_checker.py

from typing import Dict, Any, List
from loguru import logger

from src.agent.state import AgentState, REQUIRED_SLOTS


def slot_checker_node(state: AgentState) -> Dict[str, Any]:
    """槽位检查节点"""
    intent = state.get("intent", "chitchat")
    slots = state.get("slots", {})

    # 获取必填槽位
    required = REQUIRED_SLOTS.get(intent, [])

    # 检查缺失槽位
    missing = []
    for slot_name in required:
        value = slots.get(slot_name)
        if value is None or value == "" or value == "null":
            missing.append(slot_name)

    is_complete = len(missing) == 0

    logger.info(f"槽位检查: required={required}, missing={missing}, complete={is_complete}")

    return {
        "slots_complete": is_complete,
        "missing_slots": missing
    }
