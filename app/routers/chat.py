from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import json
import asyncio

from app.db.database import get_db
from app.models import schemas
from app.models.models import ChatSession
from app.services.ai_service import get_llm_service

router = APIRouter(prefix="/chat", tags=["chat"])

async def generate_chat_stream(
    message: str,
    history: list,
    session_id: Optional[str],
    db: Session
):
    """SSE stream for chat responses"""
    llm = get_llm_service()
    
    full_response = ""
    chunk_id = f"msg_{id(message) % 10000000}"
    
    async for chunk in llm.chat_stream(message, history):
        full_response += chunk
        data = json.dumps({
            "chunk": chunk,
            "done": False,
            "message_id": chunk_id
        })
        yield f"data: {data}\n\n"
    
    # Save to session
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.fingerprint == session_id
        ).order_by(ChatSession.created_at.desc()).first()
        
        if session:
            messages = session.messages or []
            messages.append({"role": "user", "content": message, "timestamp": str(datetime.now())})
            messages.append({"role": "assistant", "content": full_response, "timestamp": str(datetime.now())})
            session.messages = messages[-50:]  # keep last 50
            db.commit()
        else:
            new_session = ChatSession(
                fingerprint=session_id,
                messages=[
                    {"role": "user", "content": message, "timestamp": str(datetime.now())},
                    {"role": "assistant", "content": full_response, "timestamp": str(datetime.now())}
                ]
            )
            db.add(new_session)
            db.commit()
    
    # Send done signal
    data = json.dumps({"chunk": "", "done": True, "message_id": chunk_id})
    yield f"data: {data}\n\n"

from datetime import datetime

@router.post("", response_class=StreamingResponse)
async def chat_stream(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """
    AI chat with streaming response (SSE).
    
    Client connects with:
    ```javascript
    const eventSource = new EventSource('/api/chat?message=...&fingerprint=...');
    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.done) { eventSource.close(); }
      else { appendText(data.chunk); }
    };
    ```
    """
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
    """Non-streaming chat for simple requests"""
    llm = get_llm_service()
    
    history = []
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
    
    full_text = ""
    async for chunk in llm.chat_stream(request.message, history):
        full_text += chunk
    
    return schemas.ChatStreamChunk(
        chunk=full_text,
        done=True,
        message_id=f"msg_{id(request.message) % 10000000}"
    )

@router.get("/session/{fingerprint}", response_model=schemas.ChatSessionResponse)
async def get_chat_session(fingerprint: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(
        ChatSession.fingerprint == fingerprint
    ).order_by(ChatSession.created_at.desc()).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return schemas.ChatSessionResponse(
        session_id=session.id,
        messages=[
            schemas.ChatMessage(role=m["role"], content=m["content"])
            for m in (session.messages or [])
        ],
        created_at=session.created_at
    )
