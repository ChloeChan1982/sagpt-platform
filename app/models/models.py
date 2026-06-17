from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

class Demand(Base):
    __tablename__ = "demands"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_country = Column(String(100), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    scenario = Column(String(100), nullable=False)
    budget_range = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False, default="normal")
    description = Column(Text, nullable=False)
    
    email = Column(String(255), nullable=False, index=True)
    wechat_phone = Column(String(100))
    company_name = Column(String(200))
    phone = Column(String(50))
    attachments = Column(JSON, default=list)
    
    description_embedding = Column(JSON, nullable=True)
    ai_match_score = Column(Float, default=0.0)
    matched_expert_ids = Column(JSON, default=list)
    status = Column(String(50), default="pending", index=True)

    mini_user_id = Column(String(36), index=True)
    client_request_id = Column(String(100), unique=True, index=True)
    
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Expert(Base):
    __tablename__ = "experts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    company = Column(String(300))
    country = Column(String(100), nullable=False, index=True)
    country_code = Column(String(10))
    photo_url = Column(Text)
    
    specialties = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    bio = Column(Text)
    
    rating = Column(Float, default=5.0)
    experience_years = Column(Integer, default=0)
    projects_count = Column(Integer, default=0)
    
    profile_embedding = Column(JSON, nullable=True)
    
    membership_tier = Column(String(50), default="basic")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProviderApplication(Base):
    __tablename__ = "provider_applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    target_countries = Column(JSON, default=list)
    service_categories = Column(JSON, default=list)
    bio = Column(Text)
    experience_years = Column(Integer)
    portfolio = Column(Text)
    
    status = Column(String(50), default="pending")
    reviewed_by = Column(String(200))
    review_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fingerprint = Column(String(100), index=True)
    messages = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    password_hash = Column(Text, nullable=False)
    firm_name = Column(String(200))
    country = Column(String(100))
    avatar = Column(Text)
    verified_email = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MiniUser(Base):
    __tablename__ = "mini_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    openid = Column(String(128), nullable=False, unique=True, index=True)
    unionid = Column(String(128), unique=True, index=True)
    phone = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MiniSession(Base):
    __tablename__ = "mini_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MiniSubscriptionGrant(Base):
    __tablename__ = "mini_subscription_grants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    template_id = Column(String(255), nullable=False, index=True)
    remaining_uses = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DemandAttachment(Base):
    __tablename__ = "demand_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mini_user_id = Column(String(36), nullable=False, index=True)
    demand_id = Column(String(36), index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(150), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    purpose = Column(String(30), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    plan = Column(String(100), nullable=False, default="none")
    status = Column(String(30), nullable=False, default="none", index=True)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_price_id = Column(String(255))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    event_id = Column(String(255), primary_key=True)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
