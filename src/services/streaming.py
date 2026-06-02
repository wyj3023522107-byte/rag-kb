# src/services/streaming.py

import json
from typing import AsyncGenerator, Optional, Dict, Any
from loguru import logger

from src.llm.client import get_llm_client
from src.conversation.session import get_session_manager
from src.agent.tools import get_tool_manager
from config.prompts import CHITCHAT_PROMPT, EMOTION_SUPPORT_PROMPT, TOOL_RESULT_PROMPT, TOOL_DECISION_PROMPT


class StreamingChatService:
    """流式聊天服务"""

    def __init__(self):
        self._session_manager = get_session_manager()
        self._tool_manager = get_tool_manager()
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def _decide_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """让LLM决定是否需要调用工具"""
        tools_schema = self._tool_manager.get_all_schemas()

        # 格式化工具schema为可读文本
        tools_text = ""
        for schema in tools_schema:
            tools_text += f"- {schema['name']}: {schema['description']}\n"
            if schema['parameters']['properties']:
                tools_text += "  参数:\n"
                for param_name, param_info in schema['parameters']['properties'].items():
                    tools_text += f"    - {param_name}: {param_info['description']}\n"

        prompt = TOOL_DECISION_PROMPT.format(
            tools_schema=tools_text,
            query=query
        )

        try:
            response = await self.llm_client.generate(prompt)
            logger.debug(f"工具决策原始响应: {response}")

            # 提取JSON（支持markdown代码块）
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            result = json.loads(json_text.strip())
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应: {response}")
        except Exception as e:
            logger.error(f"工具决策失败: {e}")

        return {"need_tool": False}

    async def chat_stream(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天"""
        from src.agent.nodes.intent_classifier import intent_classifier_node

        # 1. 获取或创建会话
        session = self._session_manager.get_or_create(session_id)
        yield {"type": "session", "session_id": session.session_id}

        # 2. 让LLM决定是否需要调用工具
        tool_decision = await self._decide_tool(query)
        logger.info(f"工具决策: {tool_decision}")

        if tool_decision.get("need_tool"):
            tool_name = tool_decision.get("tool_name")
            tool_args = tool_decision.get("tool_args", {})

            # 执行工具
            result = await self._tool_manager.execute(tool_name, **tool_args)

            if result.success:
                # 将工具结果传给LLM生成自然回复
                tool_prompt = TOOL_RESULT_PROMPT.format(
                    query=query,
                    tool_result=result.data
                )

                full_response = ""
                async for chunk in self.llm_client.stream(tool_prompt):
                    full_response += chunk
                    yield {"type": "content", "content": chunk}

                self._session_manager.save_message(session.session_id, "user", query, "tool_call")
                self._session_manager.save_message(session.session_id, "assistant", full_response)
                yield {"type": "done"}
                return

        # 3. 意图识别
        state = {
            "query": query,
            "history": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in (session.messages[-10:] if session.messages else [])
            ]
        }

        try:
            intent_result = await intent_classifier_node(state)
            intent = intent_result.get("intent", "chitchat")
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            intent = "chitchat"

        yield {"type": "intent", "intent": intent}

        # 4. 流式生成响应
        prompt = self._build_prompt(query, intent)
        full_response = ""

        async for chunk in self.llm_client.stream(prompt):
            full_response += chunk
            yield {"type": "content", "content": chunk}

        # 5. 保存消息
        self._session_manager.save_message(session.session_id, "user", query, intent)
        self._session_manager.save_message(session.session_id, "assistant", full_response)

        yield {"type": "done"}

    def _build_prompt(self, query: str, intent: str, _history: list = None) -> str:
        """构建prompt"""
        if intent == "emotion_support":
            return EMOTION_SUPPORT_PROMPT.format(query=query)
        else:
            return CHITCHAT_PROMPT.format(query=query)


# 全局实例
_service: Optional[StreamingChatService] = None


def get_streaming_service() -> StreamingChatService:
    """获取流式服务实例"""
    global _service
    if _service is None:
        _service = StreamingChatService()
    return _service
