
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
            "chunk": f"[AI unavailable. Key length: {len(llm.api_key)}.]",
            "done": True,
            "message_id": "error"
        }
    
    messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
    
    if request.history:
        for msg in request.history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
    
    messages.append({"role": "user", "content": request.message})
    
    try:
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        content = ""
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and choice.message:
                if hasattr(choice.message, 'content'):
                    content = choice.message.content
                else:
                    content = str(choice.message)
            else:
                content = str(choice)
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
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
