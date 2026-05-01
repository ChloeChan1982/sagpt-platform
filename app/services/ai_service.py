import os
import re
from typing import List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.core.config import get_settings, PROVIDER_PRESETS
from app.models.models import Expert, Demand
from app.models.schemas import MatchPreview

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

settings = get_settings()

SAGPT_SYSTEM_PROMPT = """You are SAGPT AI Assistant, an expert global expansion consultant specializing in helping Chinese enterprises expand overseas.

Your expertise covers:
- Legal & Compliance (company registration, contracts, IP, labor law)
- Tax & Finance (tax planning, VAT, transfer pricing, accounting)
- Market Entry Strategy (market research, local partnerships, GTM)
- Human Resources (recruitment, payroll, compliance)
- Marketing (digital marketing, social media, KOL, TikTok)
- Logistics & Supply Chain (warehousing, freight, customs)
- Cross-border Payments (payment gateways, FX, risk control)
- Government Relations (licensing, policy consulting, lobbying)

Rules:
1. Always answer in the same language the user writes in (Chinese or English)
2. Be specific - mention actual countries, regulations, timelines, and costs when possible
3. If you don't know something specific, be honest and suggest consulting a local expert
4. When relevant, recommend the user submit a formal demand on SAGPT to get matched with certified local experts
5. Keep answers concise but informative (3-5 paragraphs max)
6. Use bullet points for lists
7. For Saudi Arabia specifically, mention SAGIA for investment licenses and SDAIA for data compliance

Current date: 2026-04-30"""

# Simple FAQ patterns that can be handled by free small models
SIMPLE_PATTERNS = [
    r'^(hi|hello|hey|你好|您好)',
    r'^(what is|what\'s|什么是|介绍).*(sagpt|your service|你们|平台)',
    r'^(how (to|do|can)|怎么|如何|请问).*(register|sign up|register|注册|入驻|成为服务商)',
    r'^(what|which|哪些|有什么).*(country|countries|国家|地区)',
    r'^(how much|what is the price|价格|费用|多少钱).*(cost|price|fee|subscription|会员)',
    r'^(thank|thanks|谢|再见|bye)',
]

def is_simple_query(message: str) -> bool:
    msg_lower = message.lower().strip()
    for pattern in SIMPLE_PATTERNS:
        if re.search(pattern, msg_lower):
            return True
    if len(msg_lower) < 20:
        return True
    return False

class LLMService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        
        preset = PROVIDER_PRESETS.get(self.provider, {})
        self.base_url = settings.OPENAI_BASE_URL or preset.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = settings.OPENAI_MODEL or preset.get("chat_model", "deepseek-ai/DeepSeek-V2.5")
        self.embedding_model = settings.EMBEDDING_MODEL or preset.get("embedding_model", "BAAI/bge-large-zh-v1.5")
        self.free_model = preset.get("free_model") or settings.FREE_MODEL
        self.use_free_tier = settings.USE_FREE_MODEL_TIER and preset.get("use_free_tier", False)
        
        self.client = None
        if HAS_OPENAI and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                print(f"[LLM] Initialized: provider={self.provider}, model={self.model}")
            except Exception as e:
                print(f"[LLM] Init failed: {e}")
        else:
            print(f"[LLM] Warning: No client. HAS_OPENAI={HAS_OPENAI}, key_exists={bool(self.api_key)}")
    
    def _get_model_for_request(self, user_message: str = "", task_type: str = "chat") -> str:
        if task_type == "embedding":
            return self.embedding_model
        if self.use_free_tier and self.free_model and is_simple_query(user_message):
            return self.free_model
        return self.model
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.client:
            return None
        try:
            response = self.client.embeddings.create(
                model=self._get_model_for_request(task_type="embedding"),
                input=text[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[LLM] Embedding error: {e}")
            return None
    
    async def chat_stream(self, user_message: str, history: List[dict], language: str = "auto") -> AsyncGenerator[str, None]:
        if not self.client:
            yield "[AI Service temporarily unavailable. Please configure API key in Render Dashboard Environment Variables.]"
            return
        
        messages = [{"role": "system", "content": SAGPT_SYSTEM_PROMPT}]
        for msg in history[-10:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})
        
        model = self._get_model_for_request(user_message, task_type="chat")
        
        try:
            stream = self.client.chat.completions.create(
                model=model, messages=messages, stream=True, temperature=0.7, max_tokens=1500
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            if model == self.free_model and self.free_model:
                try:
                    stream = self.client.chat.completions.create(
                        model=self.model, messages=messages, stream=True, temperature=0.7, max_tokens=1500
                    )
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                    return
                except Exception as e2:
                    yield f"[AI Error: {str(e2)}]"
                    return
            yield f"[AI Error: {str(e)}]"
    
    async def generate_match_reason(self, demand_description, demand_country, demand_industry,
                                     expert_name, expert_specialties, expert_country, expert_bio) -> str:
        if not self.client:
            return f"{expert_name} specializes in {', '.join(expert_specialties)} and operates in {expert_country}."
        
        prompt = f"""Given this client demand and expert profile, write ONE concise sentence (max 20 words) explaining why this expert is a good match.

Demand: {demand_description[:300]}
Target Country: {demand_country}
Industry: {demand_industry}

Expert: {expert_name}
Country: {expert_country}
Specialties: {', '.join(expert_specialties)}
Bio: {expert_bio[:200] if expert_bio else 'N/A'}

Reason:"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You write concise, professional match explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, max_tokens=100
            )
            reason = response.choices[0].message.content.strip().strip('"').strip("'")
            return reason
        except Exception as e:
            return f"Expert in {expert_country} with expertise in {', '.join(expert_specialties[:2])}."

class MatchingService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def find_matches(self, db: Session, demand: Demand, top_k: int = 5, min_score: float = 0.3) -> List[MatchPreview]:
        candidates = db.query(Expert).filter(Expert.is_active == True, Expert.is_verified == True).all()
        if not candidates:
            return []
        
        # Generate embedding if not exists
        if demand.description_embedding is None:
            embedding = await self.llm.get_embedding(
                f"Country: {demand.target_country}. Industry: {demand.industry}. "
                f"Scenario: {demand.scenario}. Budget: {demand.budget_range}. Need: {demand.description}"
            )
            if embedding:
                demand.description_embedding = embedding
                db.commit()
        
        # Score candidates
        scored = []
        for expert in candidates:
            score = self._calculate_match_score(demand, expert)
            if score >= min_score:
                scored.append((expert, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored[:top_k]
        
        results = []
        for expert, score in top_candidates:
            reason = await self.llm.generate_match_reason(
                demand.description, demand.target_country, demand.industry,
                expert.name, expert.specialties or [], expert.country, expert.bio
            )
            results.append(MatchPreview(
                expert_id=expert.id, name=expert.name, company=expert.company,
                country=expert.country, rating=expert.rating or 5.0,
                experience_years=expert.experience_years or 0,
                projects_count=expert.projects_count or 0,
                specialties=expert.specialties or [],
                match_score=round(score, 2), match_reason=reason,
                photo_url=expert.photo_url
            ))
        return results
    
    def _calculate_match_score(self, demand: Demand, expert: Expert) -> float:
        scores = []
        
        # Country match (weight: 0.4)
        country_score = 0.0
        if demand.target_country.lower() == expert.country.lower():
            country_score = 1.0
        elif expert.country.lower() in ["uae", "saudi arabia", "qatar", "bahrain", "oman"] and \
             demand.target_country.lower() in ["uae", "saudi arabia", "qatar", "bahrain", "oman"]:
            country_score = 0.7
        elif expert.country.lower() in ["singapore", "malaysia", "indonesia", "thailand"] and \
             demand.target_country.lower() in ["singapore", "malaysia", "indonesia", "thailand", "vietnam", "philippines"]:
            country_score = 0.6
        scores.append(country_score * 0.4)
        
        # Vector similarity (weight: 0.3) - using JSONB embeddings with numpy
        vector_score = 0.0
        if demand.description_embedding and expert.profile_embedding:
            try:
                import numpy as np
                a = np.array(demand.description_embedding)
                b = np.array(expert.profile_embedding)
                cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                vector_score = max(0, float(cos_sim))
            except:
                vector_score = 0.0
        scores.append(vector_score * 0.3)
        
        # Specialty overlap (weight: 0.2)
        specialty_score = 0.0
        demand_keywords = set((demand.industry + " " + demand.scenario).lower().split())
        expert_specialties = set(" ".join(expert.specialties or []).lower().split())
        if demand_keywords and expert_specialties:
            overlap = len(demand_keywords & expert_specialties)
            specialty_score = min(1.0, overlap / 3.0)
        scores.append(specialty_score * 0.2)
        
        # Experience bonus (weight: 0.1)
        exp_score = min(1.0, (expert.experience_years or 0) / 20.0)
        scores.append(exp_score * 0.1)
        
        return sum(scores)
    
    async def find_matches_vector_only(self, db: Session, demand: Demand, top_k: int = 5) -> List[Expert]:
        """In-memory vector similarity matching using JSONB embeddings"""
        if demand.description_embedding is None:
            return []
        
        experts = db.query(Expert).filter(Expert.is_active == True, Expert.is_verified == True,
                                          Expert.profile_embedding.isnot(None)).all()
        if not experts:
            return []
        
        try:
            import numpy as np
            query_vec = np.array(demand.description_embedding)
            scored = []
            for expert in experts:
                expert_vec = np.array(expert.profile_embedding)
                sim = np.dot(query_vec, expert_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(expert_vec))
                scored.append((expert, float(sim)))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            return [e for e, s in scored[:top_k] if s > 0.3]
        except:
            return []

# Singleton instances
_llm_service = None
_matching_service = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

def get_matching_service() -> MatchingService:
    global _matching_service
    if _matching_service is None:
        _llm_service = get_llm_service()
        _matching_service = MatchingService(_llm_service)
    return _matching_service
