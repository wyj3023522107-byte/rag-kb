# src/services/chat_service.py

"""
统一聊天服务 - CLI和Web共用

企业级架构：
- 学科问答/作业辅导：强制RAG检索（保证回答基于知识库）
- 闲聊：可选工具（时间/节日等）
- 情绪疏导：直接LLM生成
"""

import json
from typing import AsyncGenerator, Optional, Dict, Any
from loguru import logger

from src.llm.client import get_llm_client
from src.conversation.session import get_session_manager
from src.agent.tools import get_tool_manager
from src.rag.engine import get_rag_engine
from config.prompts import (
    CHITCHAT_PROMPT, EMOTION_SUPPORT_PROMPT, TOOL_RESULT_PROMPT,
    TOOL_DECISION_PROMPT, HOMEWORK_GUIDANCE_PROMPT, RAG_PROMPT,
    INTENT_CLASSIFICATION_PROMPT
)


# 闲聊意图可用的工具
CHITCHAT_TOOLS = ["get_current_time", "get_holiday_date"]


class ChatService:
    """统一聊天服务"""

    def __init__(self):
        self._session_manager = get_session_manager()
        self._tool_manager = get_tool_manager()
        self._llm_client = None
        self._rag_engine = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            self._rag_engine = get_rag_engine()
        return self._rag_engine

    async def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        统一聊天入口

        流程:
        1. 意图识别
        2. 根据意图分流:
           - study_qa/homework_help → 强制RAG检索
           - chitchat → 工具决策
           - emotion → 直接生成
        3. LLM生成回答
        """
        # 1. 获取或创建会话
        session = self._session_manager.get_or_create(session_id)
        self._current_session_id = session.session_id  # 保存当前会话ID
        yield {"type": "session", "session_id": session.session_id}

        # 2. 意图识别
        intent = await self._classify_intent(query)
        yield {"type": "intent", "intent": intent}
        logger.info(f"意图识别: {intent}")

        # 3. 根据意图分流处理
        if intent == "study_qa":
            # 学科问答：强制RAG检索
            async for chunk in self._handle_study_qa(query, stream):
                yield chunk

        elif intent == "homework_help":
            # 作业辅导：强制RAG检索
            async for chunk in self._handle_homework(query, stream):
                yield chunk

        elif intent == "chitchat":
            # 闲聊：先尝试工具，再生成
            async for chunk in self._handle_chitchat(query, stream):
                yield chunk

        elif intent == "emotion_support":
            # 情绪疏导：直接生成
            async for chunk in self._handle_emotion(query, stream):
                yield chunk

        else:
            # 未知意图：当闲聊处理
            async for chunk in self._handle_chitchat(query, stream):
                yield chunk

        yield {"type": "done"}

    # ==================== 意图处理方法 ====================

    async def _handle_study_qa(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理学科问答：强制RAG检索"""
        logger.info(f"学科问答: {query[:50]}...")

        # 强制检索知识库
        docs = await self._rag_retrieve(query)
        full_response = ""

        if docs:
            # 有检索结果，基于知识库生成
            context = self._build_context(docs)
            prompt = RAG_PROMPT.format(
                query=query,
                subject="综合",
                grade="中学",
                context=context
            )
        else:
            # 无检索结果，用LLM通用知识
            prompt = f"""你是一位专业的K12学习辅导老师。请用你的知识回答学生的问题。

学生问题: {query}

请给出详细、准确的回答，适合中学生理解。如果涉及知识点，可以适当举例说明。"""

        async for chunk in self._generate(prompt, stream):
            yield {"type": "content", "content": chunk}
            full_response += chunk

        self._save_messages(query, full_response, "study_qa")

    async def _handle_homework(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理作业辅导：强制RAG检索 + 引导式教学"""
        logger.info(f"作业辅导: {query[:50]}...")

        # 强制检索知识点
        docs = await self._rag_retrieve(query)
        context = self._build_context(docs) if docs else "暂无相关知识点"

        prompt = HOMEWORK_GUIDANCE_PROMPT.format(
            subject="综合",
            question=query,
            knowledge_context=context
        )

        full_response = ""
        async for chunk in self._generate(prompt, stream):
            yield {"type": "content", "content": chunk}
            full_response += chunk

        self._save_messages(query, full_response, "homework_help")

    async def _handle_chitchat(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊：工具决策 + 生成"""
        # 尝试工具调用
        tool_result = await self._tool_decision(query, CHITCHAT_TOOLS)

        full_response = ""
        if tool_result:
            # 有工具调用
            prompt = TOOL_RESULT_PROMPT.format(
                query=query,
                tool_result=tool_result["result"]
            )
            async for chunk in self._generate(prompt, stream):
                yield {"type": "content", "content": chunk}
                full_response += chunk
            self._save_messages(query, full_response, "tool_call")
        else:
            # 无工具，直接闲聊
            prompt = CHITCHAT_PROMPT.format(query=query)
            async for chunk in self._generate(prompt, stream):
                yield {"type": "content", "content": chunk}
                full_response += chunk
            self._save_messages(query, full_response, "chitchat")

    async def _handle_emotion(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理情绪疏导：直接生成"""
        prompt = EMOTION_SUPPORT_PROMPT.format(query=query, emotion_type="压力")

        full_response = ""
        async for chunk in self._generate(prompt, stream):
            yield {"type": "content", "content": chunk}
            full_response += chunk

        self._save_messages(query, full_response, "emotion_support")

    # ==================== 核心方法 ====================

    async def _classify_intent(self, query: str) -> str:
        """意图识别"""
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

    async def _rag_retrieve(self, query: str, min_score: float = 0.5) -> list:
        """RAG检索知识库

        Args:
            query: 查询文本
            min_score: 最小相关性分数阈值，低于此值的结果会被过滤
        """
        try:
            logger.info(f"RAG检索: {query[:50]}...")
            docs = await self.rag_engine.retrieve(query, top_k=3)

            # 过滤低相关性结果
            filtered_docs = [d for d in docs if d.get('score', 0) >= min_score]

            if len(filtered_docs) < len(docs):
                logger.info(f"过滤低相关性结果: {len(docs)} -> {len(filtered_docs)}")

            logger.info(f"检索到 {len(filtered_docs)} 条相关文档 (阈值={min_score})")
            return filtered_docs
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
            return []

    async def _tool_decision(
        self,
        query: str,
        available_tools: list
    ) -> Optional[Dict[str, Any]]:
        """工具决策"""
        # 获取工具schema
        all_schemas = self._tool_manager.get_all_schemas()
        tools_schema = [s for s in all_schemas if s["name"] in available_tools]

        if not tools_schema:
            return None

        # 格式化工具描述
        tools_text = ""
        for schema in tools_schema:
            tools_text += f"- {schema['name']}: {schema['description']}\n"

        prompt = TOOL_DECISION_PROMPT.format(tools_schema=tools_text, query=query)

        try:
            response = await self.llm_client.generate(prompt)

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

                # 参数名兼容
                if tool_name == "get_holiday_date" and "holiday" in tool_args:
                    tool_args["holiday_name"] = tool_args.pop("holiday")

                if tool_name not in available_tools:
                    return None

                logger.info(f"工具调用: {tool_name}({tool_args})")
                result = await self._tool_manager.execute(tool_name, **tool_args)

                if result.success:
                    return {"tool_name": tool_name, "result": result.data}

        except Exception as e:
            logger.error(f"工具决策失败: {e}")

        return None

    async def _generate(
        self,
        prompt: str,
        stream: bool
    ) -> AsyncGenerator[str, None]:
        """LLM生成"""
        if stream:
            async for chunk in self.llm_client.stream(prompt):
                yield chunk
        else:
            response = await self.llm_client.generate(prompt)
            yield response

    def _build_context(self, docs: list) -> str:
        """构建RAG上下文"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("filename", "未知来源")
            context_parts.append(f"【资料{i}】(来源: {source})\n{content}\n")
        return "\n".join(context_parts)

    def _save_messages(self, query: str, response: str, intent: str):
        """保存消息"""
        if hasattr(self, '_current_session_id') and self._current_session_id:
            self._session_manager.save_message(self._current_session_id, "user", query, intent)
            self._session_manager.save_message(self._current_session_id, "assistant", response)


# 全局实例
_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global _service
    if _service is None:
        _service = ChatService()
    return _service
