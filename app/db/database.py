from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 使用 SQLite（Render 免费版没有 PostgreSQL）
# 生产环境可以升级到 PostgreSQL
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./sagpt.db")
if DB_PATH.startswith("postgresql"):
    # 如果有 PostgreSQL，使用它
    engine = create_engine(DB_PATH, pool_pre_ping=True)
else:
    # 否则用 SQLite（本地文件）
    engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database - create tables"""
    try:
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
