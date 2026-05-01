from sqlalchemy import create_engine, event, text as sa_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Support both local Docker and cloud PostgreSQL (Render/Neon/Supabase)
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
        # Try to enable pgvector if available (Neon/Supabase support it)
        with engine.connect() as conn:
            try:
                conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("[DB] pgvector extension enabled")
            except Exception:
                print("[DB] pgvector not available, using JSONB for embeddings")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("[DB] Tables created successfully")
    except Exception as e:
        print(f"[DB] Init error: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
