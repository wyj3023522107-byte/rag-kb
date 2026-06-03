# src/services/chat_service.py

"""
统一聊天服务 - CLI和Web共用

企业级架构：
- 学科问答/作业辅导：强制RAG检索（保证回答基于知识库）
- 出题练习：分析需求 → 追问年级（如需要）→ 生成题目
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
    INTENT_CLASSIFICATION_PROMPT, QUIZ_INTENT_ANALYSIS_PROMPT,
    QUIZ_GENERATION_PROMPT, ASK_GRADE_PROMPT
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
        # 存储会话的出题上下文（等待年级回复）
        self._quiz_contexts: Dict[str, Dict[str, Any]] = {}

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
        1. 检查是否在等待年级回复
        2. 意图识别
        3. 根据意图分流处理
        4. LLM生成回答
        """
        # 1. 获取或创建会话
        session = self._session_manager.get_or_create(session_id)
        self._current_session_id = session.session_id
        yield {"type": "session", "session_id": session.session_id}

        # 2. 检查是否在等待年级回复
        if session.session_id in self._quiz_contexts:
            async for chunk in self._handle_grade_response(query, stream):
                yield chunk
            yield {"type": "done"}
            return

        # 3. 意图识别
        intent = await self._classify_intent(query)
        yield {"type": "intent", "intent": intent}
        logger.info(f"意图识别: {intent}")

        # 4. 根据意图分流处理
        if intent == "study_qa":
            async for chunk in self._handle_study_qa(query, stream):
                yield chunk

        elif intent == "homework_help":
            async for chunk in self._handle_homework(query, stream):
                yield chunk

        elif intent == "quiz_generation":
            async for chunk in self._handle_quiz(query, stream):
                yield chunk

        elif intent == "chitchat":
            async for chunk in self._handle_chitchat(query, stream):
                yield chunk

        elif intent == "emotion_support":
            async for chunk in self._handle_emotion(query, stream):
                yield chunk

        else:
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

        docs = await self._rag_retrieve(query)

        # 返回检索调试信息
        rag_info = {
            "total": len(docs),
            "results": [
                {
                    "score": round(d.get('score', 0), 3),
                    "source": d.get('metadata', {}).get('filename', '未知'),
                    "preview": d.get('content', '')[:100] + "..."
                }
                for d in docs[:3]
            ]
        }
        yield {"type": "rag_info", "rag_info": rag_info}

        full_response = ""

        if docs:
            context = self._build_context(docs)
            prompt = RAG_PROMPT.format(
                query=query,
                subject="综合",
                grade="中学",
                context=context
            )
        else:
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

    async def _handle_quiz(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理出题意图：分析需求 → 可能追问年级 → 生成题目"""
        logger.info(f"出题请求: {query[:50]}...")

        # 1. 分析出题意图
        quiz_info = await self._analyze_quiz_intent(query)
        logger.info(f"出题分析: {quiz_info}")

        # 2. 检查是否需要追问年级
        if quiz_info.get("difficulty") is None:
            # 需要追问年级
            self._quiz_contexts[self._current_session_id] = {
                "query": query,
                "subject": quiz_info.get("subject", "数学"),
                "topic": quiz_info.get("topic", ""),
                "question_type": quiz_info.get("question_type")
            }

            prompt = ASK_GRADE_PROMPT.format(
                query=query,
                subject=quiz_info.get("subject", "数学"),
                topic=quiz_info.get("topic", "综合")
            )

            full_response = ""
            async for chunk in self._generate(prompt, stream):
                yield {"type": "content", "content": chunk}
                full_response += chunk

            self._save_messages(query, full_response, "quiz_ask_grade")
        else:
            # 年级已知，直接出题
            async for chunk in self._generate_quiz(quiz_info, stream):
                yield chunk

    async def _handle_grade_response(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户回复年级"""
        context = self._quiz_contexts.pop(self._current_session_id)

        # 从用户输入中提取年级
        grade = self._extract_grade(query)
        if not grade:
            grade = "初二"  # 默认年级

        # 补全出题信息
        quiz_info = {
            "subject": context.get("subject", "数学"),
            "topic": context.get("topic", ""),
            "difficulty": grade,
            "question_type": context.get("question_type")
        }

        # 生成题目
        async for chunk in self._generate_quiz(quiz_info, stream):
            yield chunk

    async def _generate_quiz(
        self,
        quiz_info: Dict[str, Any],
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """生成题目"""
        prompt = QUIZ_GENERATION_PROMPT.format(
            subject=quiz_info.get("subject", "数学"),
            topic=quiz_info.get("topic", "综合"),
            difficulty=quiz_info.get("difficulty", "初二"),
            question_type=quiz_info.get("question_type", "计算题")
        )

        full_response = ""
        async for chunk in self._generate(prompt, stream):
            yield {"type": "content", "content": chunk}
            full_response += chunk

        self._save_messages(quiz_info.get("topic", "出题"), full_response, "quiz_generation")

    async def _handle_chitchat(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理闲聊：工具决策 + 生成"""
        tool_result = await self._tool_decision(query, CHITCHAT_TOOLS)

        full_response = ""
        if tool_result:
            prompt = TOOL_RESULT_PROMPT.format(
                query=query,
                tool_result=tool_result["result"]
            )
            async for chunk in self._generate(prompt, stream):
                yield {"type": "content", "content": chunk}
                full_response += chunk
            self._save_messages(query, full_response, "tool_call")
        else:
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

            valid_intents = ["study_qa", "homework_help", "quiz_generation", "emotion_support", "chitchat"]
            if intent not in valid_intents:
                intent = "chitchat"

            return intent
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return "chitchat"

    async def _analyze_quiz_intent(self, query: str) -> Dict[str, Any]:
        """分析出题意图，提取学科、知识点、年级等"""
        prompt = QUIZ_INTENT_ANALYSIS_PROMPT.format(query=query)

        try:
            response = await self.llm_client.generate(prompt)

            # 解析JSON
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            result = json.loads(json_text.strip())
            return result

        except Exception as e:
            logger.error(f"出题意图分析失败: {e}")
            return {
                "subject": "数学",
                "topic": "综合",
                "difficulty": None,
                "question_type": None
            }

    def _extract_grade(self, text: str) -> Optional[str]:
        """从文本中提取年级"""
        grade_keywords = {
            "小学": ["小学", "小学生"],
            "初一": ["初一", "七年级", "初中一"],
            "初二": ["初二", "八年级", "初中二"],
            "初三": ["初三", "九年级", "初中三", "中考"],
            "高一": ["高一", "高中一"],
            "高二": ["高二", "高中二"],
            "高三": ["高三", "高中三", "高考"]
        }

        for grade, keywords in grade_keywords.items():
            for kw in keywords:
                if kw in text:
                    return grade

        return None

    async def _rag_retrieve(self, query: str, min_score: float = 0.3) -> list:
        """RAG检索知识库"""
        try:
            logger.info(f"RAG检索: {query[:50]}...")
            docs = await self.rag_engine.retrieve(query, top_k=5)

            # 记录所有检索结果的分数
            for i, doc in enumerate(docs):
                score = doc.get('score', 0)
                source = doc.get('metadata', {}).get('filename', '未知')
                logger.info(f"  结果{i+1}: 分数={score:.3f}, 来源={source}")

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
        all_schemas = self._tool_manager.get_all_schemas()
        tools_schema = [s for s in all_schemas if s["name"] in available_tools]

        if not tools_schema:
            return None

        tools_text = ""
        for schema in tools_schema:
            tools_text += f"- {schema['name']}: {schema['description']}\n"

        prompt = TOOL_DECISION_PROMPT.format(tools_schema=tools_text, query=query)

        try:
            response = await self.llm_client.generate(prompt)

            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            decision = json.loads(json_text.strip())

            if decision.get("need_tool"):
                tool_name = decision.get("tool_name")
                tool_args = decision.get("tool_args", {})

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
        stream: bool,
        include_history: bool = True
    ) -> AsyncGenerator[str, None]:
        """LLM生成"""
        history = None
        if include_history and hasattr(self, '_current_session_id') and self._current_session_id:
            history = self._get_history()

        if stream:
            async for chunk in self.llm_client.stream(prompt, history=history):
                yield chunk
        else:
            response = await self.llm_client.generate(prompt, history=history)
            yield response

    def _get_history(self, max_turns: int = 10) -> list:
        """获取历史消息"""
        if not hasattr(self, '_current_session_id') or not self._current_session_id:
            return []

        session = self._session_manager.get(self._current_session_id)
        if not session or not session.messages:
            return []

        # 获取最近的N轮对话
        messages = session.messages[-(max_turns * 2):]

        # 格式化为LLM需要的格式
        history = []
        for msg in messages:
            if isinstance(msg, dict):
                history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return history

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
        if not hasattr(self, '_current_session_id') or not self._current_session_id:
            return

        # 检查空值，避免数据库错误
        if not query or not query.strip():
            query = "[空消息]"
        if not response or not response.strip():
            response = "[无响应]"

        try:
            self._session_manager.save_message(self._current_session_id, "user", query, intent)
            self._session_manager.save_message(self._current_session_id, "assistant", response)
        except Exception as e:
            logger.error(f"保存消息失败: {e}")


# 全局实例
_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global _service
    if _service is None:
        _service = ChatService()
    return _service
