from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
    llm = LLMService()
    
    if not llm.client:
        return {
            "chunk": "[AI unavailable]",
            "done": True,
            "message_id": "error"
        }
    
    messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
    
    if request.history:
        for msg in request.history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
    
    messages.append({"role": "user", "content": request.message})
    
    try:
        # 非流式调用（更稳定）
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            stream=False  # 关键：不用流式
        )
        
        # 直接提取内容
        content = response.choices[0].message.content
        
        return {
            "chunk": content,
            "done": True,
            "message_id": "msg_ok"
        }
    except Exception as e:
        return {
            "chunk": f"[AI Error: {str(e)}]",
            "done": True,
            "message_id": "error"
        }
