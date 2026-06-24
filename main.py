from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from app.core.config import get_settings, PROVIDER_PRESETS
from app.db.database import init_db, Base, engine
from app.routers import auth, demands, chat, experts, mini, payments, providers

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

admin_dir = Path(__file__).parent / "frontend" / "admin"
app.mount("/admin-assets", StaticFiles(directory=admin_dir), name="admin-assets")

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


@app.get("/admin/demands", include_in_schema=False)
async def demand_admin_dashboard():
    return FileResponse(admin_dir / "index.html")


@app.get("/admin/providers", include_in_schema=False)
async def provider_admin_dashboard():
    return FileResponse(admin_dir / "providers.html")

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(demands.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(experts.router, prefix="/api")
app.include_router(mini.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(providers.router, prefix="/api")

# Global error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "type": error["type"],
            "loc": error["loc"],
            "msg": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "message": errors[0]["msg"] if errors else "Invalid request",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "message": detail if isinstance(detail, str) else "Request failed",
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
