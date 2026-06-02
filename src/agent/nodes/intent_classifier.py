# src/agent/nodes/intent_classifier.py

import json
from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState
from src.llm.client import get_llm_client
from config.prompts import INTENT_CLASSIFICATION_PROMPT


async def intent_classifier_node(state: AgentState) -> Dict[str, Any]:
    """意图识别节点"""
    query = state.get("query", "")

    if not query:
        return {"intent": "chitchat", "intent_confidence": 1.0}

    logger.info(f"意图识别: {query[:50]}...")

    # 调用LLM进行意图分类
    llm_client = get_llm_client()

    prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)

    try:
        response = await llm_client.generate(prompt)
        intent = response.strip()

        # 验证意图是否有效
        valid_intents = ["study_qa", "homework_help", "emotion_support", "chitchat"]
        if intent not in valid_intents:
            intent = "chitchat"

        logger.info(f"识别意图: {intent}")

        return {
            "intent": intent,
            "intent_confidence": 0.9
        }
    except Exception as e:
        logger.error(f"意图识别失败: {e}")
        return {"intent": "chitchat", "intent_confidence": 0.5}
