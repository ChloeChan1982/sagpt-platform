from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import requests
import json
import os

from app.db.database import get_db
from app.models import schemas
from app.models.models import ChatSession

router = APIRouter(prefix="/chat", tags=["chat"])

# 直接用 requests 调用硅基流动 API
SAGPT_SYSTEM_PROMPT = """You are SAGPT AI Assistant, a senior global expansion consultant. 

## Saudi Arabia Knowledge
- E-commerce needs SAGIA/MISA license + Commercial Registration (CR)
- Steps: 1) Reserve name 2) SAGIA application 3) Bank account 4) VAT 15% 5) E-commerce permit
- Budget: $15,000-$50,000 setup
- Timeline: 2-4 months
- Authority: SAGIA / MISA

## UAE Knowledge
- Free zones: DMCC, JAFZA, ADGM
- Budget: $8,000-$25,000/year
- Tax: 9% corporate, 5% VAT
- Timeline: 2-3 weeks

Always answer in user's language. Be specific with costs and timelines."""

@router.post("/message")
async def chat_message(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    try:
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-72B-Instruct")
        
        if not api_key or len(api_key) < 10:
            return {"chunk": "[AI unavailable: no API key]", "done": True, "message_id": "error"}
        
        messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
        if request.history:
            for msg in request.history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.message})
        
        # 直接用 requests 调用 API
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            return {"chunk": f"[API Error {response.status_code}: {response.text[:100]}]", "done": True, "message_id": "error"}
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        return {
            "chunk": content,
            "done": True,
            "message_id": "msg_ok"
        }
        
    except Exception as e:
        return {
            "chunk": f"[Error: {str(e)}]",
            "done": True,
            "message_id": "error"
        }
