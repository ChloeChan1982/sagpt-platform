from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ========== Demand Schemas ==========
class DemandCreate(BaseModel):
    target_country: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    scenario: str = Field(..., min_length=1, max_length=100)
    budget_range: str = Field(..., min_length=1, max_length=100)
    urgency: str = Field(default="normal", pattern="^(normal|urgent)$")
    description: str = Field(..., min_length=10, max_length=2000)
    email: EmailStr
    wechat_phone: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=50)
    attachments: Optional[List[str]] = Field(default_factory=list)

class DemandResponse(BaseModel):
    id: UUID
    target_country: str
    industry: str
    scenario: str
    budget_range: str
    urgency: str
    description: str
    email: str
    company_name: Optional[str]
    status: str
    ai_match_score: float
    matched_expert_ids: List[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchPreview(BaseModel):
    expert_id: UUID
    name: str
    company: Optional[str]
    country: str
    rating: float
    experience_years: int
    projects_count: int
    specialties: List[str]
    match_score: float
    match_reason: str
    photo_url: Optional[str] = None

class DemandSubmitResponse(BaseModel):
    success: bool
    demand_id: UUID
    message: str
    estimated_match_time: str = "within 24 hours"
    preview_matches: List[MatchPreview] = Field(default_factory=list)

class DemandStatusUpdate(BaseModel):
    status: str

# ========== Expert Schemas ==========
class ExpertFilter(BaseModel):
    country: Optional[str] = None
    specialty: Optional[str] = None
    language: Optional[str] = None
    min_rating: Optional[float] = None
    query: Optional[str] = None  # semantic search query
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=100)

class ExpertResponse(BaseModel):
    id: UUID
    name: str
    company: Optional[str]
    country: str
    country_code: Optional[str]
    photo_url: Optional[str]
    specialties: List[str]
    languages: List[str]
    bio: Optional[str]
    rating: float
    experience_years: int
    projects_count: int
    membership_tier: str
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExpertListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    experts: List[ExpertResponse]

# ========== Chat Schemas ==========
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    fingerprint: Optional[str] = None
    history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatStreamChunk(BaseModel):
    chunk: str
    done: bool = False
    message_id: Optional[str] = None

class ChatSessionResponse(BaseModel):
    session_id: UUID
    messages: List[ChatMessage]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== Payment Schemas ==========
class CheckoutSessionRequest(BaseModel):
    price_id: str = Field(..., alias="priceId", min_length=1, max_length=200)
    plan_name: Optional[str] = Field(default=None, alias="planName", max_length=100)
    billing_cycle: Optional[str] = Field(default=None, alias="billingCycle", max_length=20)

class CheckoutSessionResponse(BaseModel):
    url: str

# ========== Authentication Schemas ==========
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=200)
    firm_name: Optional[str] = Field(default=None, alias="firmName", max_length=200)
    country: Optional[str] = Field(default=None, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)

class EmailRequest(BaseModel):
    email: EmailStr

class TokenRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=500)

class ResetPasswordRequest(TokenRequest):
    password: str = Field(..., min_length=10, max_length=200)

# ========== WeChat Mini Program Schemas ==========
class MiniLoginRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=500)

class MiniLoginResponse(BaseModel):
    token: str
    user_id: UUID
    expires_at: datetime

class MiniDemandCreate(BaseModel):
    client_request_id: str = Field(..., min_length=8, max_length=100)
    target_country: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    scenario: str = Field(..., min_length=1, max_length=100)
    budget_range: str = Field(..., min_length=1, max_length=100)
    urgency: str = Field(default="normal", pattern="^(normal|urgent)$")
    description: str = Field(..., min_length=10, max_length=2000)
    company_name: str = Field(..., min_length=1, max_length=200)
    wechat_phone: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=5, max_length=50)
    email: Optional[EmailStr] = None
    attachment_ids: List[UUID] = Field(default_factory=list, max_length=3)

class MiniDemandResponse(BaseModel):
    id: UUID
    target_country: str
    industry: str
    scenario: str
    budget_range: str
    urgency: str
    description: str
    company_name: str
    wechat_phone: str
    phone: str
    email: Optional[str]
    status: str
    attachment_ids: List[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

# ========== Provider Application Schemas ==========
class ProviderApplyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    target_countries: List[str] = Field(..., min_length=1)
    service_categories: List[str] = Field(..., min_length=1)
    bio: Optional[str] = Field(default=None, max_length=1000)
    experience_years: Optional[int] = Field(default=None, ge=0)
    portfolio: Optional[str] = None

class ProviderApplicationResponse(BaseModel):
    id: UUID
    name: str
    email: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== AI Matching Schemas ==========
class MatchRequest(BaseModel):
    demand_id: UUID
    top_k: Optional[int] = 5

class MatchResult(BaseModel):
    expert: ExpertResponse
    score: float
    reason: str

class MatchResponse(BaseModel):
    demand_id: UUID
    matches: List[MatchResult]
    generated_at: datetime
