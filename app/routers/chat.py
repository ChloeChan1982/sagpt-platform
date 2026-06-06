from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
import json
import urllib.request

from app.db.database import get_db
from app.models import schemas
from app.core.ai_url import build_chat_completions_url

router = APIRouter(prefix="/chat", tags=["chat"])

SAGPT_SYSTEM_PROMPT = """You are SAGPT AI Assistant, a senior global expansion consultant.

## Saudi Arabia
- E-commerce: SAGIA/MISA license + Commercial Registration (CR)
- Budget: $15,000-$50,000 setup
- Timeline: 2-4 months
- VAT: 15%

## UAE
- Free zones: DMCC, JAFZA, ADGM
- Budget: $8,000-$25,000/year
- Tax: 9% corporate, 5% VAT

Always answer in user's language. Be specific with costs and timelines."""

@router.post("/message")
async def chat_message(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-72B-Instruct")
    
    if not api_key or len(api_key) < 10:
        return {"chunk": "[AI unavailable: no API key]", "done": True}
    
    messages = [
        {"role": "system", "content": SAGPT_SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]
    
    try:
        url = build_chat_completions_url(base_url)
        
        data = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500
        }).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result["choices"][0]["message"]["content"]
            
            return {"chunk": content, "done": True}
            
    except Exception as e:
        return {"chunk": f"[Error: {str(e)}]", "done": True}
