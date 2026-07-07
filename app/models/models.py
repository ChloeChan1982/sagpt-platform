from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Index, Date, CheckConstraint
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

# ============================================================================
# NEW TABLES FOR AUTOMATION (Phase 2)
# ============================================================================

class Lead(Base):
    """
    Advisor leads discovered from automated discovery process.
    Stores information from sagpt-advisor-mvp discovery workflow.
    """
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firm_name = Column(String(300), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    website = Column(Text, nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_title = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    linkedin = Column(Text, nullable=True)
    china_experience_evidence = Column(Text, nullable=True)
    evidence_url = Column(Text, nullable=True)
    reason_for_fit = Column(Text, nullable=True)

    # Scoring fields
    china_experience_years = Column(Integer, default=0)
    has_china_desk = Column(Boolean, default=False)
    mandarin_speaking = Column(Boolean, default=False)
    chinese_content_available = Column(Boolean, default=False)
    score = Column(Integer, default=0, index=True)
    qualification_status = Column(String(50), default="pending", index=True)
    outreach_status = Column(String(50), default="not_started", index=True)
    email_sequence_step = Column(Integer, default=0)
    last_email_date = Column(DateTime(timezone=True))
    next_followup_date = Column(DateTime(timezone=True))
    emails_sent = Column(Integer, default=0)
    email_opens = Column(Integer, default=0)
    email_clicks = Column(Integer, default=0)
    unsubscribed = Column(Boolean, default=False)

    # Conversion tracking
    conversion_status = Column(String(50), default="lead")
    registration_date = Column(DateTime(timezone=True))
    payment_date = Column(DateTime(timezone=True))

    # Metadata
    ai_generated = Column(Boolean, default=True)
    extra_metadata = Column("metadata", JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("score >= 0", name="ck_leads_score_positive"),
    )


class EmailTemplate(Base):
    """
    Email templates for advisor outreach automation.
    Stores email templates with personalization fields.
    """
    __tablename__ = "email_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    sequence_step = Column(Integer, nullable=False)
    days_after_previous = Column(Integer, default=0)
    variant = Column(String(10), default="a")

    # Email content
    subject_line = Column(Text, nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=False)

    # Personalization
    personalization_fields = Column(JSON, default=list)

    # Performance tracking
    total_sent = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    conversion_rate = Column(Float)

    # A/B testing
    is_active = Column(Boolean, default=True)
    is_winner = Column(Boolean, nullable=True)

    # Metadata
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EmailLog(Base):
    """
    Email sending and tracking logs.
    Records each email sent, tracking opens, clicks, replies.
    """
    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), nullable=True)
    template_id = Column(String(100), nullable=True)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(200), nullable=True)
    subject_line = Column(Text, nullable=True)

    # Tracking
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))

    # Status
    delivery_status = Column(String(50), default="sent")
    error_message = Column(Text)

    # Metadata
    variant = Column(String(10), default="a")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyRunLog(Base):
    """
    Daily discovery workflow metrics and logs.
    Tracks the results of each scheduled discovery run.
    """
    __tablename__ = "daily_run_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_date = Column(Date, unique=True, nullable=False, index=True)

    # Workflow metrics
    workflow_name = Column(String(100), nullable=False)
    workflow_version = Column(String(50), nullable=False)

    # Discovery metrics
    leads_found = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    leads_flagged = Column(Integer, default=0)
    leads_rejected = Column(Integer, default=0)

    # Outreach metrics
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)

    # Performance metrics
    runtime_seconds = Column(Float, default=0)
    error_count = Column(Integer, default=0)

    # Error tracking
    errors = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("leads_found >= 0", name="ck_dailyrun_metrics_positive"),
    )


# ============================================================================
# EXTEND EXISTING TABLES
# ============================================================================
# Add these columns to existing tables for automation enhancement
# ============================================================================

# Extend demands table with qualification and AI analysis
# These additions should be done via ALTER TABLE in a migration script
# See: database/migrations/003_extend_demands_table.sql
