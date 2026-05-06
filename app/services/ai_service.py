import os
import re
from typing import List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.models.models import Expert, Demand
from app.models.schemas import MatchPreview

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

# Provider presets
PROVIDER_PRESETS = {
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "chat_model": "deepseek-ai/DeepSeek-V2.5",
        "embedding_model": "BAAI/bge-large-zh-v1.5",
        "free_model": "Qwen/Qwen2.5-7B-Instruct",
        "use_free_tier": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "chat_model": "deepseek-chat",
        "embedding_model": "text-embedding-3-large",
        "free_model": None,
        "use_free_tier": False,
    },
    "aliyun": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "chat_model": "qwen-plus",
        "embedding_model": "text-embedding-v3",
        "free_model": None,
        "use_free_tier": False,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_model": "gpt-4o",
        "embedding_model": "text-embedding-3-large",
        "free_model": None,
        "use_free_tier": False,
    },
}

SAGPT_SYSTEM_PROMPT = """You are SAGPT AI Assistant (SAGPT AI助手), a senior global expansion consultant specializing in helping Chinese enterprises expand overseas. You have 15+ years of hands-on experience in cross-border business consulting.

## Your Core Expertise
- Legal & Compliance: Company registration, contract law, IP protection, labor law, dispute resolution
- Tax & Finance: Tax planning, VAT/GST, transfer pricing, accounting standards, CFO services
- Market Entry: Market research, local partnerships, GTM strategy, distribution channels
- Human Resources: Recruitment, payroll compliance, work visas, labor quota systems
- Marketing: Digital marketing, social media (TikTok, Instagram, Snapchat), KOL partnerships, e-commerce platforms
- Logistics & Supply Chain: Warehousing, freight forwarding, customs clearance, last-mile delivery
- Cross-border Payments: Payment gateways, FX hedging, multi-currency accounts, anti-money laundering
- Government Relations: Investment licenses, industry permits, policy lobbying, FDI regulations

## Country-Specific Knowledge

### Saudi Arabia (沙特阿拉伯)
- E-commerce license: Need SAGIA/MISA investment license (投资牌照) + Commercial Registration (CR)
- Required steps: 1) Reserve company name 2) Submit SAGIA application 3) Open local bank account 4) Register for VAT (15%) 5) Obtain e-commerce permit from Ministry of Commerce
- Budget estimate: Setup costs $15,000-$50,000; VAT registration mandatory; need local sponsor/agent initially
- Key authority: SAGIA / MISA (Ministry of Investment)
- Data compliance: Must comply with SDAIA personal data protection law
- Local requirement: 100% foreign ownership allowed in e-commerce since 2023 reform
- Timeline: 2-4 months for full setup

### UAE (阿联酋)
- Free zones: DMCC (Dubai), JAFZA (Jebel Ali), ADGM (Abu Dhabi) - each has different costs
- Budget estimate: Free zone license $8,000-$25,000/year; mainland license $15,000-$40,000
- Tax: 9% corporate tax (introduced 2023); 5% VAT; no personal income tax
- E-commerce: Need DED license + TRA approval for online sales
- Timeline: 2-3 weeks in free zone

### Singapore (新加坡)
- Registration: ACRA (Accounting and Corporate Regulatory Authority)
- Budget: Company setup SGD 1,500-5,000; annual compliance SGD 2,000-5,000
- Tax: 17% corporate tax (with exemptions for first 3 years); 8% GST
- E-commerce: Need specific licenses depending on products
- Timeline: 1-2 weeks

### Turkey (土耳其)
- Company types: Limited Sirket (Ltd) or Anonim Sirket (A.S.)
- Budget: Setup $5,000-$15,000; need Turkish tax ID
- E-commerce: ETKB license for electronic commerce
- VAT: 20% standard rate

### Malaysia (马来西亚)
- SDN BHD: Private limited company, 100% foreign ownership allowed for e-commerce
- Budget: Setup RM 5,000-15,000; annual audit mandatory
- Tax: 24% corporate tax; 8% SST for services
- License: Need SSM registration + MDTC license for digital platforms

## Response Rules

1. Language: Always respond in the SAME language as the user (Chinese or English).
2. Specificity: Always mention actual regulations, costs, timelines, and authorities when possible. Use the country-specific facts above.
3. Budget ranges: When asked about costs, provide realistic ranges based on business size (startup/SME/enterprise).
4. Timeline: Always give estimated timeline for each step.
5. Honesty: If you don't know specific details about a niche regulation, be honest and recommend consulting a certified local expert through SAGPT.
6. Structure: Use bullet points, numbered steps, and clear sections. Bold key terms.
7. CTA: When appropriate, recommend submitting a formal demand on SAGPT to get matched with certified local experts. Mention we have 500+ verified experts across 50+ countries.
8. Tone: Professional but approachable. Use business Chinese for Chinese queries.

## Budget Reference Framework

When asked about budgets, use these tiers:
- Small/Startup (< $100K revenue): Setup $5K-$20K, monthly compliance $500-$2K
- Mid-size/SME ($100K-$5M): Setup $20K-$100K, monthly compliance $2K-$10K
- Large/Enterprise ($5M+): Setup $100K-$500K+, monthly compliance $10K-$50K+

Current date: 2026-04-30"""

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
        # 直接从环境变量读取，不依赖任何缓存的配置对象
        self.provider = os.getenv("AI_PROVIDER", "siliconflow")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        
        preset = PROVIDER_PRESETS.get(self.provider, {})
        self.base_url = os.getenv("OPENAI_BASE_URL", preset.get("base_url", "https://api.siliconflow.cn/v1"))
        self.model = os.getenv("OPENAI_MODEL", preset.get("chat_model", "deepseek-ai/DeepSeek-V2.5"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", preset.get("embedding_model", "BAAI/bge-large-zh-v1.5"))
        self.free_model = preset.get("free_model") or os.getenv("FREE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        use_free_env = os.getenv("USE_FREE_MODEL_TIER", "true").lower() == "true"
        self.use_free_tier = use_free_env and preset.get("use_free_tier", False)
        
        # 初始化 OpenAI 客户端
        self.client = None
        if HAS_OPENAI and self.api_key and len(self.api_key) > 10:
            try:
                self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                print(f"[LLM] Initialized: provider={self.provider}, model={self.model}, key_length={len(self.api_key)}")
            except Exception as e:
                print(f"[LLM] Init failed: {e}")
        else:
            print(f"[LLM] Warning: No client. HAS_OPENAI={HAS_OPENAI}, key_exists={bool(self.api_key)}, key_len={len(self.api_key) if self.api_key else 0}")
    
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
        
        if demand.description_embedding is None:
            embedding = await self.llm.get_embedding(
                f"Country: {demand.target_country}. Industry: {demand.industry}. "
                f"Scenario: {demand.scenario}. Budget: {demand.budget_range}. Need: {demand.description}"
            )
            if embedding:
                demand.description_embedding = embedding
                db.commit()
        
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
        
        specialty_score = 0.0
        demand_keywords = set((demand.industry + " " + demand.scenario).lower().split())
        expert_specialties = set(" ".join(expert.specialties or []).lower().split())
        if demand_keywords and expert_specialties:
            overlap = len(demand_keywords & expert_specialties)
            specialty_score = min(1.0, overlap / 3.0)
        scores.append(specialty_score * 0.2)
        
        exp_score = min(1.0, (expert.experience_years or 0) / 20.0)
        scores.append(exp_score * 0.1)
        
        return sum(scores)
    
    async def find_matches_vector_only(self, db: Session, demand: Demand, top_k: int = 5) -> List[Expert]:
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
