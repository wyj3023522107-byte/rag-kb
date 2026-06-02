# api/routes/chat.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    slots: Optional[dict] = None
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息"""
    from src.agent.graph import get_agent

    agent = get_agent()
    result = await agent.run(request.message, request.session_id)

    return ChatResponse(
        response=result["response"],
        intent=result.get("intent"),
        slots=result.get("slots"),
        session_id=result["session_id"]
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取对话历史"""
    from src.conversation.session import get_session_manager

    manager = get_session_manager()
    session = manager.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"history": [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清空对话历史"""
    from src.conversation.session import get_session_manager

    manager = get_session_manager()
    manager.delete(session_id)

    return {"status": "success"}
