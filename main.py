from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from app.core.config import get_settings, PROVIDER_PRESETS
from app.db.database import init_db, Base, engine
from app.routers import demands, chat, experts, providers

settings = get_settings()

# Create tables
try:
    init_db()# 自动初始化专家数据（如果表为空）
from sqlalchemy import text
from app.models.models import Expert

def seed_experts_if_empty():
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        count = db.query(Expert).count()
        if count == 0:
            print("[INIT] Seeding experts...")
            experts = [
                Expert(
                    id="1", name="Mohammed Al-Farsi", company="Riyadh Business Development Center",
                    country="Saudi Arabia", country_code="SA",
                    photo_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face",
                    specialties=["Government Relations", "Market Entry", "Compliance"],
                    languages=["Arabic", "English"],
                    bio="Saudi government relations expert with deep connections in SAGIA, MISA, and local chambers.",
                    rating=4.9, experience_years=19, projects_count=201,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="2", name="Aisha Al-Rashidi", company="Gulf Business Advisory Group",
                    country="UAE", country_code="AE",
                    photo_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&h=200&fit=crop&crop=face",
                    specialties=["Tax & Finance", "Market Entry", "Government Relations"],
                    languages=["Arabic", "English", "Hindi"],
                    bio="Tax advisor and market entry specialist for GCC region.",
                    rating=4.8, experience_years=12, projects_count=178,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="3", name="Wei-Ming Chen", company="Chen & Associates Law Firm",
                    country="Singapore", country_code="SG",
                    photo_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face",
                    specialties=["Legal Services", "Compliance", "Company Registration"],
                    languages=["English", "Mandarin", "Malay"],
                    bio="Leading corporate lawyer in Southeast Asia with 18 years of experience.",
                    rating=4.9, experience_years=18, projects_count=234,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="4", name="Thomas Müller", company="Munich Financial Advisory GmbH",
                    country="Germany", country_code="DE",
                    photo_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face",
                    specialties=["Tax & Finance", "Accounting", "M&A"],
                    languages=["German", "English", "Mandarin"],
                    bio="German tax and M&A specialist with expertise in cross-border transactions.",
                    rating=4.9, experience_years=20, projects_count=156,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="5", name="Priya Sharma", company="South Asia HR Solutions",
                    country="India", country_code="IN",
                    photo_url="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&h=200&fit=crop&crop=face",
                    specialties=["Human Resources", "Compensation & Benefits", "Training"],
                    languages=["English", "Hindi", "Tamil"],
                    bio="HR consulting expert specializing in Indian labor law compliance.",
                    rating=4.7, experience_years=15, projects_count=203,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="6", name="Sophie Laurent", company="Laurent & Picard Law Paris",
                    country="France", country_code="FR",
                    photo_url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face",
                    specialties=["Legal Services", "Intellectual Property", "Compliance"],
                    languages=["French", "English", "Mandarin"],
                    bio="Paris-based IP and compliance lawyer.",
                    rating=4.9, experience_years=15, projects_count=142,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="7", name="Kenji Tanaka", company="Tokyo Business Strategy Consulting K.K.",
                    country="Japan", country_code="JP",
                    photo_url="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200&h=200&fit=crop&crop=face",
                    specialties=["Market Entry", "Marketing", "Government Relations"],
                    languages=["Japanese", "English", "Mandarin"],
                    bio="Japan market entry strategist with 22 years helping Chinese brands localize.",
                    rating=4.8, experience_years=22, projects_count=118,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="8", name="Budi Santoso", company="Jakarta Cross-Border Business Advisors",
                    country="Indonesia", country_code="ID",
                    photo_url="https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=200&h=200&fit=crop&crop=face",
                    specialties=["Company Registration", "Tax & Finance", "Market Entry"],
                    languages=["Indonesian", "English", "Mandarin"],
                    bio="Indonesia company formation and tax specialist.",
                    rating=4.7, experience_years=13, projects_count=156,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="9", name="Carlos Mendoza", company="LatAm Digital Marketing Institute",
                    country="Mexico", country_code="MX",
                    photo_url="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=200&h=200&fit=crop&crop=face",
                    specialties=["Marketing", "E-commerce", "Brand Strategy"],
                    languages=["Spanish", "English", "Portuguese"],
                    bio="Latin America digital marketing expert.",
                    rating=4.8, experience_years=13, projects_count=167,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="10", name="Jennifer Walsh", company="SF Tech Marketing Consulting",
                    country="United States", country_code="US",
                    photo_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&h=200&fit=crop&crop=face",
                    specialties=["Marketing", "Brand Strategy", "E-commerce"],
                    languages=["English", "Mandarin"],
                    bio="Silicon Valley marketing strategist helping Chinese SaaS companies launch in US.",
                    rating=4.8, experience_years=14, projects_count=189,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="11", name="Ana Kovačević", company="Eastern Europe Logistics & Supply Chain Institute",
                    country="Serbia", country_code="RS",
                    photo_url="https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=200&h=200&fit=crop&crop=face",
                    specialties=["Logistics & Supply Chain", "Compliance", "Market Entry"],
                    languages=["Serbian", "English", "Russian"],
                    bio="Balkans logistics and supply chain expert.",
                    rating=4.6, experience_years=11, projects_count=89,
                    is_verified=True, is_active=True
                ),
                Expert(
                    id="12", name="Oluwaseun Adeyemi", company="West Africa Business Consulting Group",
                    country="Nigeria", country_code="NG",
                    photo_url="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=200&h=200&fit=crop&crop=face",
                    specialties=["Cross-border Payments", "Tax & Finance", "Market Entry"],
                    languages=["English", "Yoruba", "French"],
                    bio="Nigeria and West Africa business consultant.",
                    rating=4.7, experience_years=16, projects_count=145,
                    is_verified=True, is_active=True
                ),
            ]
            for expert in experts:
                db.add(expert)
            db.commit()
            print(f"[INIT] Seeded {len(experts)} experts")
        else:
            print(f"[INIT] Experts already exist: {count}")
    except Exception as e:
        print(f"[INIT] Error seeding experts: {e}")
    finally:
        db.close()

# 启动时执行
seed_experts_if_empty()
except Exception as e:
    print(f"Database init warning: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description="SAGPT AI Backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS - allow Readdy frontend
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "ai_available": True,
    }

# Debug endpoint - check environment variables
@app.get("/debug")
async def debug():
    key = os.getenv("OPENAI_API_KEY", "")
    return {
        "env_has_key": "OPENAI_API_KEY" in os.environ,
        "key_length": len(key),
        "key_prefix": key[:5] if key else "NONE",
        "all_env_vars": sorted(os.environ.keys()),
    }

# API routes
app.include_router(demands.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(experts.router, prefix="/api")
app.include_router(providers.router, prefix="/api")

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
