# src/agent/graph.py

from typing import Dict, Any, Optional
from loguru import logger

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes.intent_classifier import intent_classifier_node
from .nodes.slot_filler import slot_filler_node
from .nodes.slot_checker import slot_checker_node
from .nodes.router import router_node
from .nodes.handlers import get_handler
from src.conversation.session import get_session_manager
from src.conversation.history import ConversationHistory


def ask_missing_node(state: AgentState) -> Dict[str, Any]:
    """追问缺失槽位节点"""
    missing_slots = state.get("missing_slots", [])
    slots = state.get("slots", {})

    from config.prompts import ASK_MISSING_TEMPLATES

    if missing_slots:
        slot_name = missing_slots[0]
        question = ASK_MISSING_TEMPLATES.get(slot_name, f"请告诉我{slot_name}是什么？")

        return {"ask_question": question}

    return {"ask_question": "请提供更多信息"}


def create_handler_node(intent: str):
    """创建处理器节点工厂"""
    async def handler_node(state: AgentState) -> Dict[str, Any]:
        handler = get_handler(intent)

        slots = state.get("slots", {})
        history = state.get("history", [])

        response = await handler.handle(slots, history)

        return {"response": response}

    return handler_node


def build_graph() -> StateGraph:
    """构建Agent状态图"""
    # 创建状态图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("slot_filler", slot_filler_node)
    graph.add_node("slot_checker", slot_checker_node)
    graph.add_node("ask_missing", ask_missing_node)
    graph.add_node("router", router_node)

    # 添加意图处理器节点
    graph.add_node("study_qa", create_handler_node("study_qa"))
    graph.add_node("homework_help", create_handler_node("homework_help"))
    graph.add_node("emotion_support", create_handler_node("emotion_support"))
    graph.add_node("chitchat", create_handler_node("chitchat"))

    # 设置入口
    graph.set_entry_point("intent_classifier")

    # 定义边
    graph.add_edge("intent_classifier", "slot_filler")
    graph.add_edge("slot_filler", "slot_checker")

    # 条件边：槽位检查
    graph.add_conditional_edges(
        "slot_checker",
        lambda state: "router" if state.get("slots_complete") else "ask_missing",
        {
            "router": "router",
            "ask_missing": "ask_missing"
        }
    )

    # ask_missing 结束
    graph.add_edge("ask_missing", END)

    # 条件边：路由到具体handler
    graph.add_conditional_edges(
        "router",
        lambda state: state.get("intent", "chitchat"),
        {
            "study_qa": "study_qa",
            "homework_help": "homework_help",
            "emotion_support": "emotion_support",
            "chitchat": "chitchat"
        }
    )

    # 所有handler结束
    for intent in ["study_qa", "homework_help", "emotion_support", "chitchat"]:
        graph.add_edge(intent, END)

    return graph


class AgentGraph:
    """Agent图执行器"""

    def __init__(self):
        self._graph = None
        self._session_manager = get_session_manager()

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_graph().compile()
        return self._graph

    async def run(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行Agent"""
        logger.info(f"Agent执行: query={query[:50]}...")

        # 获取或创建会话
        session = self._session_manager.get_or_create(session_id)

        # 构建初始状态
        initial_state: AgentState = {
            "query": query,
            "session_id": session.session_id,
            "history": [],
            "context": session.context
        }

        # 从会话获取历史
        if session.messages:
            initial_state["history"] = [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages[-10:]  # 最近5轮
            ]

        # 执行图
        result = await self.graph.ainvoke(initial_state)

        # 更新会话
        session.touch()
        session.messages.append({
            "role": "user",
            "content": query,
            "intent": result.get("intent")
        })

        response = result.get("response") or result.get("ask_question", "抱歉，我无法理解您的问题。")

        session.messages.append({
            "role": "assistant",
            "content": response
        })

        return {
            "response": response,
            "intent": result.get("intent"),
            "slots": result.get("slots"),
            "session_id": session.session_id
        }


# 全局实例
_agent: Optional[AgentGraph] = None


def get_agent() -> AgentGraph:
    """获取Agent实例"""
    global _agent
    if _agent is None:
        _agent = AgentGraph()
    return _agent
