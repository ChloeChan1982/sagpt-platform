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
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "chat_model": "glm-4-flash",
        "embedding_model": "embedding-2",
        "free_model": "glm-4-flash",
        "use_free_tier": True,
        "api_key_env": "ZHIPU_API_KEY",
    },
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
        self.provider = os.getenv("AI_PROVIDER", "siliconflow")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        
        preset = PROVIDER_PRESETS.get(self.provider, {})
        self.base_url = os.getenv("OPENAI_BASE_URL", preset.get("base_url", "https://api.siliconflow.cn/v1"))
        self.model = os.getenv("OPENAI_MODEL", preset.get("chat_model", "Qwen/Qwen2.5-72B-Instruct"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", preset.get("embedding_model", "BAAI/bge-large-zh-v1.5"))
        self.free_model = preset.get("free_model") or os.getenv("FREE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        use_free_env = os.getenv("USE_FREE_MODEL_TIER", "true").lower() == "true"
        self.use_free_tier = use_free_env and preset.get("use_free_tier", False)
        
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
                temperature=0.5,
                max_tokens=100
            )
            reason = response.choices[0].message.content.strip().strip('"').strip("'")
            return reason
        except Exception as e:
            return f"Expert in {expert_country} with expertise in {', '.join(expert_specialties[:2])}."

    async def improve_demand_description(self, fields: dict) -> str:
        original = (fields.get("description") or "").strip()
        if not self.client or not original:
            return original

        prompt = f"""请基于以下企业出海需求，改写成一段清晰、具体、事实克制的中文需求描述，长度控制在100到500字。

要求：
- 不编造预算、国家、公司规模、政策、资质或监管事实。
- 保留用户已经提供的目标国家、行业、场景、预算和紧急程度。
- 语气专业，便于后台顾问判断服务范围。

目标国家：{fields.get("target_country", "")}
行业：{fields.get("industry", "")}
场景：{fields.get("scenario", "")}
预算：{fields.get("budget_range", "")}
原始描述：{original}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是严谨的企业出海需求编辑，只优化表达，不新增事实。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            suggestion = response.choices[0].message.content.strip()
            return suggestion or original
        except Exception:
            return original

    # ============================================================================
    # SPECIALIZED METHODS FOR AUTOMATION
    # ============================================================================

    async def score_advisor_lead(
        self,
        firm_name: str,
        country: str,
        category: str,
        china_experience_evidence: str,
        china_experience_years: int = 0,
        has_china_desk: bool = False,
        mandarin_speaking: bool = False,
        chinese_content_available: bool = False
    ) -> dict:
        """
        Score an advisor lead based on China experience (0-100 points).

        Scoring criteria:
        - China Desk/Practice: +20 points
        - Mandarin-speaking: +15 points
        - Chinese case study evidence: +25 points
        - Chinese-language content: +10 points
        - China experience years: +15 points (5+ years)
        - Priority market: +10 points
        - Public contact info: +10 points

        Returns:
            dict with total_score, status, and score breakdown
        """
        if not self.client:
            return {"total_score": 0, "status": "error", "breakdown": {}}

        prompt = f"""你是一个专业的B2B服务商评估专家。请根据以下信息评估这家服务提供商的"中国经验"得分。

提供商信息：
- 公司名称：{firm_name}
- 所在国家：{country}
- 服务类别：{category}
- 中国经验描述：{china_experience_evidence}
- 中国服务年限：{china_experience_years}年
- 是否有中国团队/中国部：{'是' if has_china_desk else '否'}
- 是否有中文服务人员：{'是' if mandarin_speaking else '否'}
- 是否有中文网站/营销材料：{'是' if chinese_content_available else '否'}

评分标准（总分100分）：
1. 中国团队/中国部（20分）- 有专门的中国服务团队或部门
2. 中文服务能力（15分）- 有中文服务人员
3. 中国客户案例（25分）- 有中国客户案例研究、成功故事或证言
4. 中文内容（10分）- 有中文网站、营销材料或客户资源
5. 服务年限（15分）- 为中国公司服务年数（5年以上得满分）
6. 目标市场（10分）- 所在国家是SAGPT的目标市场
7. 公开联系方式（10分）- 有公开邮箱或LinkedIn

请评估并返回JSON格式：
{{
    "total_score": 分数(0-100),
    "status": "qualified"(>=70分) / "flagged"(50-69分) / "rejected"(<50分),
    "breakdown": {{
        "china_desk": 得分(0-20),
        "mandarin_speaking": 得分(0-15),
        "case_study": 得分(0-25),
        "chinese_content": 得分(0-10),
        "experience_years": 得分(0-15),
        "priority_market": 得分(0-10),
        "public_contact": 得分(0-10)
    }},
    "reasoning": "简要说明评分理由"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的B2B服务商评估专家，基于客观事实进行评分。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract score with regex
                import re
                score_match = re.search(r'"total_score":\s*(\d+)', content)
                if score_match:
                    score = int(score_match.group(1))
                    status = "qualified" if score >= 70 else "flagged" if score >= 50 else "rejected"
                    return {
                        "total_score": score,
                        "status": status,
                        "breakdown": {},
                        "reasoning": content
                    }
                return {"total_score": 0, "status": "error", "breakdown": {}}

        except Exception as e:
            print(f"[LLM] Advisor scoring error: {e}")
            return {"total_score": 0, "status": "error", "breakdown": {}}

    async def qualify_demand(
        self,
        company_name: str,
        industry: str,
        target_country: str,
        description: str,
        budget_range: str = "",
        timeline: str = "",
        company_size: str = "",
        contact_email: str = "",
        contact_phone: str = ""
    ) -> dict:
        """
        Qualify a company demand lead (0-100 points).

        Scoring criteria:
        - Company legitimacy: +25 points (website, LinkedIn, business email)
        - Project clarity: +20 points (detailed description, specific requirements)
        - Urgency: +15 points (immediate to 6+ months)
        - Budget range: +15 points (appropriate budget specified)
        - Expansion stage: +15 points (active planning stage)
        - Contact quality: +10 points (business email, phone, LinkedIn)

        Returns:
            dict with total_score, status, qualification_reasons, and key_requirements
        """
        if not self.client:
            return {
                "total_score": 0,
                "status": "error",
                "qualification_reasons": ["AI service unavailable"],
                "key_requirements": []
            }

        prompt = f"""你是一个专业的B2B需求评估专家。请根据以下信息评估这家企业出海需求的"质量"得分。

企业信息：
- 公司名称：{company_name}
- 所在行业：{industry}
- 目标国家：{target_country}
- 需求描述：{description}
- 预算范围：{budget_range or '未提供'}
- 预期时间：{timeline or '未提供'}
- 公司规模：{company_size or '未提供'}
- 联系邮箱：{contact_email}
- 联系电话：{contact_phone or '未提供'}

评分标准（总分100分）：
1. 公司合法性（25分）- 公司网站、LinkedIn主页、企业邮箱等
2. 项目清晰度（20分）- 需求描述详细、具体要求明确
3. 紧急程度（15分）- 立即/1-3个月/3-6个月/6+个月
4. 预算范围（15分）- 提供了合理的预算范围
5. 扩张阶段（15分）- 处于积极规划/研究阶段
6. 联系质量（10分）- 企业邮箱、电话、LinkedIn等

请评估并返回JSON格式：
{{
    "total_score": 分数(0-100),
    "status": "qualified"(>=60分) / "flagged"(40-59分) / "rejected"(<40分),
    "qualification_reasons": ["评分理由1", "评分理由2", ...],
    "key_requirements": ["关键需求1", "关键需求2", ...],
    "flagged_issues": ["需要注意的问题1", ...],
    "complexity_score": 复杂度评分(0-100)
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的B2B需求评估专家，基于客观事实进行评分。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()

            import json
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, extract score with regex
                import re
                score_match = re.search(r'"total_score":\s*(\d+)', content)
                if score_match:
                    score = int(score_match.group(1))
                    status = "qualified" if score >= 60 else "flagged" if score >= 40 else "rejected"
                    return {
                        "total_score": score,
                        "status": status,
                        "qualification_reasons": [content[:200]],
                        "key_requirements": [],
                        "flagged_issues": [],
                        "complexity_score": score
                    }
                return {"total_score": 0, "status": "error", "qualification_reasons": [], "key_requirements": []}

        except Exception as e:
            print(f"[LLM] Demand qualification error: {e}")
            return {
                "total_score": 0,
                "status": "error",
                "qualification_reasons": ["AI service unavailable"],
                "key_requirements": []
            }

    async def generate_personalized_email(
        self,
        recipient_name: str,
        recipient_title: str,
        firm_name: str,
        recipient_email: str,
        china_experience: str,
        template_type: str = "warm_intro",
        sender_name: str = "Chloe",
        target_market: str = "",
        category: str = "",
        reason_for_fit: str = ""
    ) -> dict:
        """
        Generate personalized outreach email for advisor.

        Template types:
        - warm_intro: First introduction email
        - value_prop: Value proposition email
        - urgency: Urgency/FOMO email
        - breakup: Final break-up email
        - response_handler: Thank you for response

        Returns:
            dict with subject_line and body_html
        """
        if not self.client:
            return {
                "subject_line": "Invitation to join SAGPT.COM",
                "body_html": "<p>Hi,</p><p>I'd like to invite you to join SAGPT.COM.</p><p>Best regards,<br>Chloe</p>"
            }

        template_descriptions = {
            "warm_intro": "First introduction email",
            "value_prop": "Value proposition email with benefits",
            "urgency": "Urgency/FOMO email with limited spots",
            "breakup": "Gentle break-up email",
            "response_handler": "Thank you for response email"
        }

        prompt = f"""你是SAGPT.COM的邮件撰写专家。请为以下顾问生成一封{template_descriptions.get(template_type, template_type)}。

收件人信息：
- 姓名：{recipient_name}
- 职位：{recipient_title}
- 公司：{firm_name}
- 邮箱：{recipient_email}
- 中国经验：{china_experience}
- 目标市场：{target_market}
- 服务类别：{category}
- 适配理由：{reason_for_fit}

发件人信息：
- 姓名：{sender_name}
- 公司：SAGPT.COM
- 目的：邀请顾问加入SAGPT.COM平台

邮件要求：
1. 个性化：在开头提及对方的具体中国经验
2. 专业性：语气专业但友好
3. 简洁：控制在150-250字
4. CTA：有明确的行动号召
5. 格式：HTML格式，用<p>标签分段

请返回JSON格式：
{{
    "subject_line": "邮件主题",
    "body_html": "HTML格式的邮件正文"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的B2B邮件撰写专家，擅长个性化邮件写作。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()

            import json
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, generate a default email
                return {
                    "subject_line": f"Invitation to join SAGPT.COM - {target_market} services",
                    "body_html": f"<p>Hi {recipient_name},</p><p>I came across {firm_name}'s work helping Chinese companies expand to {target_country} — particularly your experience: {china_experience[:100]}...</p><p>I'm building sagpt.com, an AI-powered advisor marketplace connecting Chinese businesses with local experts. Your China experience makes you an ideal fit.</p><p>Would you be open to a 15-minute call to learn more?</p><p>Best regards,<br><strong>{sender_name}</strong><br>Founder, sagpt.com</p>"
                }

        except Exception as e:
            print(f"[LLM] Email generation error: {e}")
            return {
                "subject_line": f"Invitation to join SAGPT.COM",
                "body_html": f"<p>Hi {recipient_name},</p><p>I'd like to invite you to join SAGPT.COM.</p><p>Best regards,<br>{sender_name}</p>"
            }

    async def generate_match_summary(
        self,
        company_name: str,
        industry: str,
        target_country: str,
        service_type: str,
        requirements: str,
        advisor_firm_name: str,
        advisor_country: str,
        advisor_service_type: str,
        advisor_china_experience: str,
        advisor_experience_years: int,
        advisor_specialties: list,
        advisor_has_china_desk: bool,
        advisor_mandarin_speaking: bool
    ) -> dict:
        """
        Generate personalized match summary for a company.

        Returns:
            dict with summary field
        """
        if not self.client:
            return {
                "summary": f"{advisor_firm_name} operates in {advisor_country} and specializes in {advisor_service_type}. With {advisor_experience_years} years of experience, they can help with {requirements[:100]}..."
            }

        specialties_str = ', '.join(advisor_specialties) if advisor_specialties else "general advisory"
        china_team = "has a dedicated China team" if advisor_has_china_desk else "has experience with Chinese clients"
        language_capability = "and speaks Mandarin" if advisor_mandarin_speaking else ""

        prompt = f"""你是一个专业的商务分析师。请为中国企业生成一个个性化的顾问匹配说明。

中国企业信息：
- 公司名称：{company_name}
- 所在行业：{industry}
- 目标国家：{target_country}
- 服务需求：{service_type}
- 具体需求：{requirements}

匹配顾问信息：
- 公司名称：{advisor_firm_name}
- 所在国家：{advisor_country}
- 服务类型：{advisor_service_type}
- 专业领域：{specialties_str}
- 中国经验：{advisor_china_experience}
- 服务年限：{advisor_experience_years}年
- 中国团队：{china_team}
- 语言能力：{language_capability}

请生成一段150-200字的匹配说明，解释为什么这个顾问适合该企业的需求。请具体说明相关的经验和能力。

请返回JSON格式：
{{
    "summary": "个性化匹配说明（150-200字）"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的商务分析师，擅长撰写匹配说明。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            content = response.choices[0].message.content.strip()

            import json
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return the content as summary
                return {"summary": content}

        except Exception as e:
            print(f"[LLM] Match summary error: {e}")
            return {
                "summary": f"{advisor_firm_name} is a good fit for {company_name}'s {target_country} expansion needs. With {advisor_experience_years} years of experience serving Chinese companies, including {advisor_china_experience[:100]}..., they understand the unique challenges Chinese businesses face. Their {china_team} {language_capability} can provide culturally aligned support in both English and Mandarin."
            }

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
        
                # Country match (支持中英文)
        country_score = 0.0
        demand_country = demand.target_country.lower()
        expert_country = expert.country.lower()
        
        # 直接匹配（英文↔英文）
        if demand_country == expert_country:
            country_score = 1.0
        # 中文→英文映射
        elif demand_country in ["沙特阿拉伯", "沙特"] and expert_country in ["saudi arabia", "saudi"]:
            country_score = 1.0
        elif demand_country in ["阿联酋", "迪拜"] and expert_country in ["uae", "dubai"]:
            country_score = 1.0
        elif demand_country in ["卡塔尔"] and expert_country == "qatar":
            country_score = 1.0
        elif demand_country in ["巴林"] and expert_country == "bahrain":
            country_score = 1.0
        elif demand_country in ["阿曼"] and expert_country == "oman":
            country_score = 1.0
        elif demand_country in ["新加坡"] and expert_country == "singapore":
            country_score = 1.0
        elif demand_country in ["马来西亚"] and expert_country == "malaysia":
            country_score = 1.0
        elif demand_country in ["印度尼西亚", "印尼"] and expert_country == "indonesia":
            country_score = 1.0
        elif demand_country in ["美国"] and expert_country == "united states":
            country_score = 1.0
        elif demand_country in ["英国"] and expert_country == "united kingdom":
            country_score = 1.0
        elif demand_country in ["德国"] and expert_country == "germany":
            country_score = 1.0
        elif demand_country in ["法国"] and expert_country == "france":
            country_score = 1.0
        elif demand_country in ["土耳其"] and expert_country == "turkey":
            country_score = 1.0
        elif demand_country in ["日本"] and expert_country == "japan":
            country_score = 1.0
        elif demand_country in ["印度"] and expert_country == "india":
            country_score = 1.0
        elif demand_country in ["墨西哥"] and expert_country == "mexico":
            country_score = 1.0
        elif demand_country in ["尼日利亚"] and expert_country == "nigeria":
            country_score = 1.0
        elif demand_country in ["塞尔维亚"] and expert_country == "serbia":
            country_score = 1.0
        # GCC 区域相似性
        elif expert_country in ["uae", "saudi arabia", "qatar", "bahrain", "oman"] and \
             demand_country in ["uae", "saudi arabia", "qatar", "bahrain", "oman", "阿联酋", "沙特阿拉伯", "卡塔尔", "巴林", "阿曼"]:
            country_score = 0.7
        # SEA 区域相似性
        elif expert_country in ["singapore", "malaysia", "indonesia", "thailand"] and \
             demand_country in ["singapore", "malaysia", "indonesia", "thailand", "vietnam", "philippines", "新加坡", "马来西亚", "印度尼西亚", "印尼", "泰国", "越南", "菲律宾"]:
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
