from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

class Demand(Base):
    __tablename__ = "demands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_country = Column(String(100), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    scenario = Column(String(100), nullable=False)
    budget_range = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False, default="normal")
    description = Column(Text, nullable=False)
    
    # Contact info
    email = Column(String(255), nullable=False, index=True)
    wechat_phone = Column(String(100))
    company_name = Column(String(200))
    phone = Column(String(50))
    attachments = Column(JSON, default=list)
    
    # AI matching - use JSONB for embeddings (works on all PostgreSQL providers)
    description_embedding = Column(JSONB, nullable=True)
    ai_match_score = Column(Float, default=0.0)
    matched_expert_ids = Column(JSON, default=list)
    status = Column(String(50), default="pending", index=True)
    
    # Metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Expert(Base):
    __tablename__ = "experts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    company = Column(String(300))
    country = Column(String(100), nullable=False, index=True)
    country_code = Column(String(10))
    photo_url = Column(Text)
    
    # Expert profile
    specialties = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    bio = Column(Text)
    
    # Stats
    rating = Column(Float, default=5.0)
    experience_years = Column(Integer, default=0)
    projects_count = Column(Integer, default=0)
    
    # AI matching - JSONB for embeddings
    profile_embedding = Column(JSONB, nullable=True)
    
    # Membership
    membership_tier = Column(String(50), default="basic")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProviderApplication(Base):
    __tablename__ = "provider_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint = Column(String(100), index=True)
    messages = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_chat_fingerprint_created', 'fingerprint', 'created_at'),
    )
