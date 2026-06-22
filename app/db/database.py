from sqlalchemy import create_engine, event, inspect, text as sa_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database - create tables if not exist"""
    try:
        with engine.connect() as conn:
            try:
                conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("[DB] pgvector extension enabled")
            except Exception:
                print("[DB] pgvector not available, using JSON for embeddings")
        
        Base.metadata.create_all(bind=engine)
        ensure_mini_schema(engine)
        print("[DB] Tables created successfully")
        _seed_experts_if_empty()
    except Exception as e:
        print(f"[DB] Init error: {e}")

def ensure_mini_schema(target_engine=engine):
    """Add mini-program columns to existing deployments.

    SQLAlchemy create_all creates new tables but does not alter existing ones,
    so old Render databases need these additive columns explicitly.
    """
    inspector = inspect(target_engine)
    if "demands" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("demands")
    }

    statements = []
    if "mini_user_id" not in existing_columns:
        statements.append("ALTER TABLE demands ADD COLUMN mini_user_id VARCHAR(36)")
    if "client_request_id" not in existing_columns:
        statements.append("ALTER TABLE demands ADD COLUMN client_request_id VARCHAR(100)")

    statements.extend(
        [
            "CREATE INDEX IF NOT EXISTS ix_demands_mini_user_id ON demands (mini_user_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_demands_client_request_id ON demands (client_request_id)",
        ]
    )

    with target_engine.begin() as conn:
        for statement in statements:
            conn.execute(sa_text(statement))

def _seed_experts_if_empty():
    from app.models.models import Expert
    db = SessionLocal()
    try:
        count = db.query(Expert).count()
        if count > 0:
            print(f"[DB] Experts already exist: {count}")
            return
        print("[DB] Seeding 12 default experts...")
        experts = [
            Expert(id="11111111-1111-1111-1111-111111111111", name="Mohammed Al-Farsi", company="Riyadh Business Development Center", country="Saudi Arabia", country_code="SA", photo_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face", specialties=["Government Relations", "Market Entry", "Compliance"], languages=["Arabic", "English"], bio="Saudi government relations expert with deep connections in SAGIA, MISA, and local chambers. Specializes in helping Chinese firms navigate Saudi Vision 2030 opportunities.", rating=4.9, experience_years=19, projects_count=201, is_verified=True, is_active=True),
            Expert(id="22222222-2222-2222-2222-222222222222", name="Aisha Al-Rashidi", company="Gulf Business Advisory Group", country="UAE", country_code="AE", photo_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&h=200&fit=crop&crop=face", specialties=["Tax & Finance", "Market Entry", "Government Relations"], languages=["Arabic", "English", "Hindi"], bio="Tax advisor and market entry specialist for GCC region. Expert in UAE corporate tax, VAT compliance, and SAGIA licensing.", rating=4.8, experience_years=12, projects_count=178, is_verified=True, is_active=True),
            Expert(id="33333333-3333-3333-3333-333333333333", name="Wei-Ming Chen", company="Chen & Associates Law Firm", country="Singapore", country_code="SG", photo_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face", specialties=["Legal Services", "Compliance", "Company Registration"], languages=["English", "Mandarin", "Malay"], bio="Leading corporate lawyer in Southeast Asia with 18 years of experience helping Chinese enterprises establish operations in Singapore and ASEAN markets.", rating=4.9, experience_years=18, projects_count=234, is_verified=True, is_active=True),
            Expert(id="44444444-4444-4444-4444-444444444444", name="Thomas Müller", company="Munich Financial Advisory GmbH", country="Germany", country_code="DE", photo_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face", specialties=["Tax & Finance", "Accounting", "M&A"], languages=["German", "English", "Mandarin"], bio="German tax and M&A specialist with expertise in cross-border transactions between China and EU markets.", rating=4.9, experience_years=20, projects_count=156, is_verified=True, is_active=True),
            Expert(id="55555555-5555-5555-5555-555555555555", name="Priya Sharma", company="South Asia HR Solutions", country="India", country_code="IN", photo_url="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&h=200&fit=crop&crop=face", specialties=["Human Resources", "Compensation & Benefits", "Training"], languages=["English", "Hindi", "Tamil"], bio="HR consulting expert specializing in Indian labor law compliance, talent acquisition, and cross-cultural team management for Chinese companies.", rating=4.7, experience_years=15, projects_count=203, is_verified=True, is_active=True),
            Expert(id="66666666-6666-6666-6666-666666666666", name="Sophie Laurent", company="Laurent & Picard Law Paris", country="France", country_code="FR", photo_url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face", specialties=["Legal Services", "Intellectual Property", "Compliance"], languages=["French", "English", "Mandarin"], bio="Paris-based IP and compliance lawyer. Expert in EU GDPR, trademark registration, and French corporate law for Asian tech companies.", rating=4.9, experience_years=15, projects_count=142, is_verified=True, is_active=True),
            Expert(id="77777777-7777-7777-7777-777777777777", name="Kenji Tanaka", company="Tokyo Business Strategy Consulting K.K.", country="Japan", country_code="JP", photo_url="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200&h=200&fit=crop&crop=face", specialties=["Market Entry", "Marketing", "Government Relations"], languages=["Japanese", "English", "Mandarin"], bio="Japan market entry strategist with 22 years helping Chinese brands localize for Japanese consumers. Expert in JETRO programs and Keiretsu partnerships.", rating=4.8, experience_years=22, projects_count=118, is_verified=True, is_active=True),
            Expert(id="88888888-8888-8888-8888-888888888888", name="Budi Santoso", company="Jakarta Cross-Border Business Advisors", country="Indonesia", country_code="ID", photo_url="https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=200&h=200&fit=crop&crop=face", specialties=["Company Registration", "Tax & Finance", "Market Entry"], languages=["Indonesian", "English", "Mandarin"], bio="Indonesia company formation and tax specialist. Helps Chinese e-commerce and manufacturing firms navigate BKPM regulations and local partnership structures.", rating=4.7, experience_years=13, projects_count=156, is_verified=True, is_active=True),
            Expert(id="99999999-9999-9999-9999-999999999999", name="Carlos Mendoza", company="LatAm Digital Marketing Institute", country="Mexico", country_code="MX", photo_url="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=200&h=200&fit=crop&crop=face", specialties=["Marketing", "E-commerce", "Brand Strategy"], languages=["Spanish", "English", "Portuguese"], bio="Latin America digital marketing expert. Specializes in TikTok, Instagram, and local e-commerce platform strategies for Chinese brands entering Mexico and Brazil.", rating=4.8, experience_years=13, projects_count=167, is_verified=True, is_active=True),
            Expert(id="10101010-1010-1010-1010-101010101010", name="Jennifer Walsh", company="SF Tech Marketing Consulting", country="United States", country_code="US", photo_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&h=200&fit=crop&crop=face", specialties=["Marketing", "Brand Strategy", "E-commerce"], languages=["English", "Mandarin"], bio="Silicon Valley marketing strategist helping Chinese SaaS and hardware companies launch in US market. Expert in product-market fit and GTM strategy.", rating=4.8, experience_years=14, projects_count=189, is_verified=True, is_active=True),
            Expert(id="11111112-1112-1112-1112-111211121112", name="Ana Kovačević", company="Eastern Europe Logistics & Supply Chain Institute", country="Serbia", country_code="RS", photo_url="https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=200&h=200&fit=crop&crop=face", specialties=["Logistics & Supply Chain", "Compliance", "Market Entry"], languages=["Serbian", "English", "Russian"], bio="Balkans logistics and supply chain expert. Specializes in cross-border warehousing, customs clearance, and EU-Asia trade corridor optimization.", rating=4.6, experience_years=11, projects_count=89, is_verified=True, is_active=True),
            Expert(id="12121212-1212-1212-1212-121212121212", name="Oluwaseun Adeyemi", company="West Africa Business Consulting Group", country="Nigeria", country_code="NG", photo_url="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=200&h=200&fit=crop&crop=face", specialties=["Cross-border Payments", "Tax & Finance", "Market Entry"], languages=["English", "Yoruba", "French"], bio="Nigeria and West Africa business consultant. Expert in Naira currency hedging, local distributor networks, and AFCFTA trade compliance.", rating=4.7, experience_years=16, projects_count=145, is_verified=True, is_active=True),
        ]
        for expert in experts:
            db.add(expert)
        db.commit()
        print(f"[DB] Seeded {len(experts)} experts successfully")
    except Exception as e:
        print(f"[DB] Seed error: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
