# src/services/chat_service.py

"""
统一聊天服务 - CLI和Web共用
流程: 意图识别 → 工具决策 → LLM生成
"""

import json
from typing import AsyncGenerator, Optional, Dict, Any, List
from loguru import logger

from src.llm.client import get_llm_client
from src.conversation.session import get_session_manager
from src.agent.tools import get_tool_manager
from config.prompts import (
    CHITCHAT_PROMPT, EMOTION_SUPPORT_PROMPT, TOOL_RESULT_PROMPT,
    TOOL_DECISION_PROMPT, HOMEWORK_GUIDANCE_PROMPT,
    INTENT_CLASSIFICATION_PROMPT
)


# 意图对应的可用工具
INTENT_TOOLS = {
    "study_qa": ["knowledge_search"],           # 学科问答：知识检索
    "homework_help": ["knowledge_search"],      # 作业辅导：知识检索
    "chitchat": ["get_current_time", "get_holiday_date", "knowledge_search"],  # 闲聊：时间/节日/知识
    "emotion_support": [],                       # 情绪疏导：无工具
}


class ChatService:
    """统一聊天服务"""

    def __init__(self):
        self._session_manager = get_session_manager()
        self._tool_manager = get_tool_manager()
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        统一聊天入口

        流程: 意图识别 → 工具决策 → 知识检索 → LLM生成

        Args:
            query: 用户输入
            session_id: 会话ID
            stream: 是否流式输出

        Yields:
            {"type": "session/intent/content/done", ...}
        """
        # 1. 获取或创建会话
        session = self._session_manager.get_or_create(session_id)
        yield {"type": "session", "session_id": session.session_id}

        # 2. 意图识别
        intent = await self._classify_intent(query)
        yield {"type": "intent", "intent": intent}
        logger.info(f"意图识别: {intent}")

        # 3. 工具决策（根据意图选择可用工具）
        tool_result = await self._tool_decision(query, intent)

        if tool_result:
            # 有工具调用（可能是time/holiday/knowledge_search）
            full_response = ""
            async for chunk in self._generate_with_tool(query, tool_result):
                yield {"type": "content", "content": chunk}
                full_response += chunk
            self._save_messages(session.session_id, query, full_response, "tool_call")
            yield {"type": "done"}
            return

        # 4. 无工具调用，直接LLM生成
        full_response = ""
        async for chunk in self._generate_response(query, intent, stream):
            if stream:
                yield {"type": "content", "content": chunk}
            full_response += chunk

        if not stream:
            yield {"type": "content", "content": full_response}

        # 5. 保存消息
        self._save_messages(session.session_id, query, full_response, intent)
        yield {"type": "done"}

    async def _classify_intent(self, query: str) -> str:
        """
        意图识别

        Returns:
            intent: study_qa / homework_help / emotion_support / chitchat
        """
        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)

        try:
            response = await self.llm_client.generate(prompt)
            intent = response.strip()

            valid_intents = ["study_qa", "homework_help", "emotion_support", "chitchat"]
            if intent not in valid_intents:
                intent = "chitchat"

            return intent
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return "chitchat"

    async def _tool_decision(
        self,
        query: str,
        intent: str
    ) -> Optional[Dict[str, Any]]:
        """
        工具决策: 根据意图判断是否需要调用工具

        Args:
            query: 用户输入
            intent: 已识别的意图

        Returns:
            None: 不需要工具
            Dict: 工具执行结果
        """
        # 获取该意图可用的工具
        available_tools = INTENT_TOOLS.get(intent, [])

        if not available_tools:
            return None

        # 获取工具的schema
        all_schemas = self._tool_manager.get_all_schemas()
        tools_schema = [s for s in all_schemas if s["name"] in available_tools]

        if not tools_schema:
            return None

        # 格式化工具schema
        tools_text = ""
        for schema in tools_schema:
            tools_text += f"- {schema['name']}: {schema['description']}\n"
            if schema['parameters']['properties']:
                tools_text += "  参数:\n"
                for param_name, param_info in schema['parameters']['properties'].items():
                    tools_text += f"    - {param_name}: {param_info['description']}\n"

        prompt = TOOL_DECISION_PROMPT.format(tools_schema=tools_text, query=query)

        try:
            response = await self.llm_client.generate(prompt)
            logger.debug(f"工具决策响应: {response}")

            # 解析JSON
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            decision = json.loads(json_text.strip())

            if decision.get("need_tool"):
                tool_name = decision.get("tool_name")
                tool_args = decision.get("tool_args", {})

                # 参数名兼容处理
                if tool_name == "get_holiday_date" and "holiday" in tool_args:
                    tool_args["holiday_name"] = tool_args.pop("holiday")

                # 验证工具是否在可用范围内
                if tool_name not in available_tools:
                    logger.warning(f"工具 {tool_name} 不在意图 {intent} 的可用工具范围内")
                    return None

                logger.info(f"工具决策: 调用 {tool_name}({tool_args})")

                # 执行工具
                result = await self._tool_manager.execute(tool_name, **tool_args)

                if result.success:
                    return {
                        "tool_name": tool_name,
                        "result": result.data
                    }

        except Exception as e:
            logger.error(f"工具决策失败: {e}")

        return None

    async def _generate_with_tool(
        self,
        query: str,
        tool_result: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """基于工具结果生成回答"""
        tool_name = tool_result.get("tool_name", "")
        tool_data = tool_result.get("result", "")

        # 根据工具类型选择不同的prompt
        if tool_name == "knowledge_search":
            # 知识检索结果，使用RAG prompt
            prompt = f"""你是一位专业的K12学习辅导老师。请根据检索到的知识资料回答学生的问题。

【学生问题】
{query}

【检索到的知识资料】
{tool_data}

【回答要求】
1. 准确回答问题，内容要有依据
2. 语言通俗易懂，适合中学生理解
3. 如有例题，给出详细讲解
4. 适当延伸相关知识

请开始回答:"""
        else:
            # 其他工具（时间、节日等）
            prompt = TOOL_RESULT_PROMPT.format(
                query=query,
                tool_result=tool_data
            )

        async for chunk in self.llm_client.stream(prompt):
            yield chunk

    async def _generate_response(
        self,
        query: str,
        intent: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        生成回答（无工具调用时）

        Args:
            query: 用户问题
            intent: 意图
            stream: 是否流式
        """
        if intent == "homework_help":
            # 作业辅导（无知识点时）
            prompt = HOMEWORK_GUIDANCE_PROMPT.format(
                subject="综合",
                question=query,
                knowledge_context="暂无相关知识点"
            )
        elif intent == "emotion_support":
            # 情绪疏导
            prompt = EMOTION_SUPPORT_PROMPT.format(query=query, emotion_type="压力")
        else:
            # 闲聊或其他
            prompt = CHITCHAT_PROMPT.format(query=query)

        # 生成
        if stream:
            async for chunk in self.llm_client.stream(prompt):
                yield chunk
        else:
            response = await self.llm_client.generate(prompt)
            yield response

    def _save_messages(self, session_id: str, query: str, response: str, intent: str):
        """保存消息到会话"""
        self._session_manager.save_message(session_id, "user", query, intent)
        self._session_manager.save_message(session_id, "assistant", response)


# 全局实例
_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global _service
    if _service is None:
        _service = ChatService()
    return _service
