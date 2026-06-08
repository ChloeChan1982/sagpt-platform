from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import get_settings, PROVIDER_PRESETS
from app.db.database import init_db, Base, engine
from app.routers import demands, chat, experts, payments, providers

settings = get_settings()

# Create tables + auto-seed experts
try:
    init_db()
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

# API routes
app.include_router(demands.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(experts.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
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
