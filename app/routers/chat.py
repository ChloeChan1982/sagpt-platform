from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import os
from datetime import datetime

from app.db.database import get_db
from app.models import schemas
from app.models.models import ChatSession
from app.services.ai_service import LLMService

router = APIRouter(prefix="/chat", tags=["chat"])

async def generate_chat_stream(message: str, history: list, session_id: str, db):
    # 每次请求都重新创建 LLMService（绕过 singleton 缓存问题）
    llm = LLMService()
    
    if not llm.client:
        print(f"[CHAT] LLM client not available. key_len={len(llm.api_key)}")
        yield "[AI Service temporarily unavailable. API Key not configured or invalid.]"
        return
    
    messages = [{"role": "system", "content": llm.__class__.__name__}]
    # 重新加载 system prompt
    from app.services.ai_service import SAGPT_SYSTEM_PROMPT
    messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
    
    for msg in history[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": message})
    
    model = llm._get_model_for_request(message, task_type="chat")
    
    try:
        stream = llm.client.chat.completions.create(
            model=model, messages=messages, stream=True, temperature=0.7, max_tokens=1500
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[CHAT] Error: {e}")
        yield f"[AI Error: {str(e)}]"

@router.post("", response_class=StreamingResponse)
async def chat_stream(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    history = []
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
    
    return StreamingResponse(
        generate_chat_stream(request.message, history, request.fingerprint, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/message", response_model=schemas.ChatStreamChunk)
async def chat_message(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    # 每次请求都重新创建 LLMService
    llm = LLMService()
    
    if not llm.client:
        return schemas.ChatStreamChunk(
            chunk=f"[AI unavailable. Key length: {len(llm.api_key)}. Please check OPENAI_API_KEY env var.]",
            done=True
        )
    
    history = []
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
    
    messages = [{"role": "system", "content": llm.__class__.__name__}]
    from app.services.ai_service import SAGPT_SYSTEM_PROMPT
    messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
    
    for msg in history[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": request.message})
    
    model = llm._get_model_for_request(request.message, task_type="chat")
    
    try:
        stream = llm.client.chat.completions.create(
            model=model, messages=messages, stream=True, temperature=0.7, max_tokens=1500
        )
        full_text = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
        return schemas.ChatStreamChunk(chunk=full_text, done=True)
    except Exception as e:
        return schemas.ChatStreamChunk(chunk=f"[AI Error: {str(e)}]", done=True)

@router.get("/session/{fingerprint}")
async def get_chat_session(fingerprint: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(
        ChatSession.fingerprint == fingerprint
    ).order_by(ChatSession.created_at.desc()).first()
    
    if not session:
        return {"error": "Session not found"}
    
    return {
        "session_id": str(session.id),
        "messages": session.messages or []
    }
