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
    QUIZ_GENERATION_PROMPT, ASK_GRADE_PROMPT, AGENT_SYSTEM_PROMPT,
    AGENT_TOOL_PROMPT
)


# 闲聊意图可用的工具
CHITCHAT_TOOLS = ["get_current_time", "get_holiday_date", "web_search"]


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

        elif intent == "complex_task":
            async for chunk in self._handle_complex_task(query, stream):
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
                "question_type": quiz_info.get("question_type"),
                "include_answer": quiz_info.get("include_answer", True)
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
            "question_type": context.get("question_type"),
            "include_answer": context.get("include_answer", True)
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
        include_answer = quiz_info.get("include_answer", True)

        # 根据是否需要答案决定输出格式
        if include_answer:
            answer_section = """**解析：**
[详细解析过程]

**答案：**
[最终答案]"""
        else:
            answer_section = """（提示：如果学生需要，可以稍后再询问解析和答案）"""

        prompt = QUIZ_GENERATION_PROMPT.format(
            subject=quiz_info.get("subject", "数学"),
            topic=quiz_info.get("topic", "综合"),
            difficulty=quiz_info.get("difficulty", "初二"),
            question_type=quiz_info.get("question_type", "计算题"),
            include_answer="是" if include_answer else "否",
            answer_section=answer_section
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

    async def _handle_complex_task(
        self,
        query: str,
        stream: bool
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理复杂任务：Agent Loop 模式
        让 LLM 自主规划、调用工具、直到任务完成
        """
        logger.info(f"复杂任务: {query[:50]}...")

        # Agent 可用的工具
        agent_tools = ["web_search", "web_fetch", "knowledge_search", "get_current_time", "get_holiday_date"]

        # 初始化 Agent 状态
        progress = []  # 记录执行进度
        called_tools = set()  # 记录已调用的工具
        collected_info = []  # 收集到的信息
        max_iterations = 8

        # 构建 Agent 提示
        agent_prompt = f"{AGENT_SYSTEM_PROMPT}\n\n【用户任务】\n{query}"

        for iteration in range(max_iterations):
            logger.info(f"Agent 迭代 {iteration + 1}/{max_iterations}")

            # 构建 progress 信息
            if not progress:
                progress_text = "首次执行，还未调用任何工具"
            else:
                progress_text = "\n".join(progress)
                # 添加已收集信息的摘要
                if collected_info:
                    progress_text += f"\n\n【已收集的关键信息】\n" + "\n".join(collected_info[-3:])

            # 调用 LLM
            full_prompt = f"{agent_prompt}\n\n【当前进度】\n{progress_text}\n\n请决定下一步："

            try:
                response = await self.llm_client.generate(full_prompt)
                response = response.strip()
                logger.info(f"Agent 响应: {response[:200]}...")

                # 检查是否完成
                if "FINAL_ANSWER:" in response:
                    # 提取最终答案
                    idx = response.find("FINAL_ANSWER:")
                    final_answer = response[idx + 14:].strip()
                    # 清理可能的多余内容
                    if "\n```" in final_answer:
                        final_answer = final_answer.split("\n```")[0]
                    logger.info("Agent 任务完成")

                    # 流式输出最终答案
                    yield {"type": "content", "content": final_answer}
                    self._save_messages(query, final_answer, "complex_task")
                    return

                # 解析工具调用
                tool_call = self._parse_agent_tool_call(response)

                if tool_call:
                    tool_name = tool_call.get("tool")
                    tool_args = tool_call.get("args", {})

                    if tool_name not in agent_tools:
                        progress.append(f"❌ 工具 '{tool_name}' 不可用")
                        continue

                    # 检查是否重复调用
                    tool_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
                    if tool_key in called_tools:
                        progress.append(f"⚠️ 已经调用过 {tool_name}，请使用其他工具或直接输出答案")
                        # 强制引导输出答案
                        progress.append(f"\n【提示】你已经收集了足够的信息，请直接输出 FINAL_ANSWER: 开头的答案")
                        continue

                    called_tools.add(tool_key)

                    # 执行工具
                    logger.info(f"Agent 调用工具: {tool_name}({tool_args})")
                    yield {"type": "tool_call", "tool": tool_name, "args": tool_args}

                    result = await self._tool_manager.execute(tool_name, **tool_args)

                    if result.success:
                        tool_result = result.data
                        # 截取关键信息
                        result_preview = tool_result[:800] if len(tool_result) > 800 else tool_result
                        progress.append(f"✓ {tool_name} 返回结果:\n{result_preview}")
                        collected_info.append(f"[{tool_name}] {tool_result[:300]}...")
                        yield {"type": "tool_result", "result": result_preview}
                    else:
                        progress.append(f"✗ {tool_name} 失败: {result.error}")
                        yield {"type": "tool_result", "result": f"执行失败: {result.error}"}

                else:
                    # 无法解析为工具调用
                    # 检查是否是 LLM 试图给出答案
                    if len(response) > 100 and "```" not in response[:50]:
                        # 可能是直接回答
                        progress.append(f"思考: {response[:300]}")

                    # 如果已经迭代多次，强制输出
                    if iteration >= 4:
                        # 尝试让 LLM 输出最终答案
                        force_prompt = f"{agent_prompt}\n\n【已收集信息】\n{chr(10).join(collected_info)}\n\n请基于以上信息，直接输出最终答案（以 FINAL_ANSWER: 开头）："
                        final_response = await self.llm_client.generate(force_prompt)
                        if "FINAL_ANSWER:" in final_response:
                            idx = final_response.find("FINAL_ANSWER:")
                            final_answer = final_response[idx + 14:].strip()
                        else:
                            final_answer = final_response.strip()

                        yield {"type": "content", "content": final_answer}
                        self._save_messages(query, final_answer, "complex_task")
                        return

            except Exception as e:
                logger.error(f"Agent 迭代失败: {e}")
                progress.append(f"错误: {str(e)}")

        # 达到最大迭代次数，强制总结
        if collected_info:
            summary_prompt = f"请基于以下信息，简洁地回答用户问题：{query}\n\n收集到的信息：\n{chr(10).join(collected_info)}"
            final_answer = await self.llm_client.generate(summary_prompt)
        else:
            final_answer = "抱歉，我无法完成这个任务，请尝试简化您的问题。"

        yield {"type": "content", "content": final_answer}
        self._save_messages(query, final_answer, "complex_task")

    def _parse_agent_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 Agent 的工具调用（更宽容的解析）"""
        try:
            # 尝试解析 JSON
            json_text = None

            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                # 尝试提取代码块中的 JSON
                parts = response.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 1 and "{" in part:  # 奇数索引是代码块
                        json_text = part.strip()
                        # 移除可能的语言标识
                        if json_text.startswith("json"):
                            json_text = json_text[4:].strip()
                        break

            if not json_text and "{" in response:
                # 尝试直接提取 JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                json_text = response[start:end]

            if not json_text:
                return None

            data = json.loads(json_text.strip())

            # 验证并修复格式
            action = data.get("action", "")

            # 兼容多种格式
            if action == "tool_call":
                return {
                    "tool": data.get("tool"),
                    "args": data.get("args", {})
                }
            elif "tool" in data and "args" in data:
                # 缺少 action 字段但有 tool 和 args
                return {
                    "tool": data.get("tool"),
                    "args": data.get("args", {})
                }
            elif action in ["web_search", "web_fetch", "knowledge_search"]:
                # action 直接是工具名
                return {
                    "tool": action,
                    "args": data.get("args", {})
                }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 原文: {response[:100]}")
        except Exception as e:
            logger.warning(f"解析工具调用失败: {e}")

        return None

    # ==================== 核心方法 ====================

    async def _classify_intent(self, query: str) -> str:
        """意图识别"""
        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)

        try:
            response = await self.llm_client.generate(prompt)
            intent = response.strip()
            logger.info(f"意图识别原始结果: {intent}")

            valid_intents = ["study_qa", "homework_help", "quiz_generation", "emotion_support", "complex_task", "chitchat"]
            if intent not in valid_intents:
                logger.warning(f"意图识别结果无效，使用默认chitchat: {intent}")
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

            # 设置默认值
            if "include_answer" not in result:
                result["include_answer"] = True

            return result

        except Exception as e:
            logger.error(f"出题意图分析失败: {e}")
            return {
                "subject": "数学",
                "topic": "综合",
                "difficulty": None,
                "question_type": None,
                "include_answer": True
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
        logger.info(f"工具决策: query={query[:50]}..., 可用工具={available_tools}")

        all_schemas = self._tool_manager.get_all_schemas()
        tools_schema = [s for s in all_schemas if s["name"] in available_tools]

        if not tools_schema:
            logger.warning("没有可用的工具schema")
            return None

        tools_text = ""
        for schema in tools_schema:
            tools_text += f"- {schema['name']}: {schema['description']}\n"

        prompt = TOOL_DECISION_PROMPT.format(tools_schema=tools_text, query=query)

        try:
            response = await self.llm_client.generate(prompt)
            logger.info(f"工具决策LLM响应: {response.strip()[:200]}")

            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            decision = json.loads(json_text.strip())
            logger.info(f"工具决策结果: {decision}")

            if decision.get("need_tool"):
                tool_name = decision.get("tool_name")
                tool_args = decision.get("tool_args", {})

                if tool_name == "get_holiday_date" and "holiday" in tool_args:
                    tool_args["holiday_name"] = tool_args.pop("holiday")

                if tool_name not in available_tools:
                    logger.warning(f"工具 {tool_name} 不在可用列表中")
                    return None

                logger.info(f"执行工具: {tool_name}({tool_args})")
                result = await self._tool_manager.execute(tool_name, **tool_args)

                if result.success:
                    return {"tool_name": tool_name, "result": result.data}
                else:
                    logger.error(f"工具执行失败: {result.error}")
            else:
                logger.info("工具决策: 不需要调用工具")

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
