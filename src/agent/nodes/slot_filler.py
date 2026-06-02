# src/agent/nodes/slot_filler.py

import json
from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState, SLOT_DEFINITIONS
from src.llm.client import get_llm_client
from config.prompts import SLOT_FILLING_PROMPT, SLOT_DEFINITIONS as PROMPT_SLOT_DEFS


async def slot_filler_node(state: AgentState) -> Dict[str, Any]:
    """槽位填充节点"""
    query = state.get("query", "")
    intent = state.get("intent", "chitchat")

    logger.info(f"槽位填充: intent={intent}")

    # 闲聊不需要槽位
    if intent == "chitchat":
        return {"slots": {}, "slots_complete": True, "missing_slots": []}

    # 获取槽位定义
    slot_def = PROMPT_SLOT_DEFS.get(intent, "")
    if not slot_def:
        return {"slots": {}, "slots_complete": True, "missing_slots": []}

    # 构建历史对话
    history = state.get("history", [])
    history_text = "\n".join([
        f"{'用户' if h['role'] == 'user' else '助手'}: {h['content']}"
        for h in history[-4:]  # 最近2轮
    ])

    # 调用LLM提取槽位
    llm_client = get_llm_client()

    prompt = SLOT_FILLING_PROMPT.format(
        intent=intent,
        slot_definition=slot_def,
        query=query,
        history=history_text or "无"
    )

    try:
        response = await llm_client.generate(prompt)

        # 解析JSON
        slots = json.loads(response.strip())

        logger.info(f"提取槽位: {slots}")

        return {"slots": slots}
    except Exception as e:
        logger.error(f"槽位提取失败: {e}")
        return {"slots": {}}
