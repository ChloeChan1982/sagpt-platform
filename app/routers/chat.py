from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import os
from datetime import datetime

from app.db.database import get_db
from app.models import schemas
from app.models.models import ChatSession
from app.services.ai_service import LLMService, SAGPT_SYSTEM_PROMPT

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message")
async def chat_message(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """Non-streaming chat for simple requests"""
    # 每次请求都重新创建 LLMService
    llm = LLMService()
    
    if not llm.client:
        return {
            "chunk": f"[AI unavailable. Key length: {len(llm.api_key)}. Check env var.]",
            "done": True,
            "message_id": "error"
        }
    
    # Build messages
    messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
    
    if request.history:
        for msg in request.history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
    
    messages.append({"role": "user", "content": request.message})
    
    # Call API directly using the client
    try:
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        content = response.choices[0].message.content
        
        return {
            "chunk": content,
            "done": True,
            "message_id": f"msg_{hash(request.message) % 10000000}"
        }
    except Exception as e:
        return {
            "chunk": f"[AI Error: {str(e)}]",
            "done": True,
            "message_id": "error"
        }
