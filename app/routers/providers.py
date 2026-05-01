from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import schemas
from app.models.models import ProviderApplication

router = APIRouter(prefix="/providers", tags=["providers"])

@router.post("/apply", response_model=schemas.ProviderApplicationResponse)
async def apply_provider(
    application: schemas.ProviderApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Submit provider application.
    """
    app = ProviderApplication(
        name=application.name,
        email=application.email,
        target_countries=application.target_countries,
        service_categories=application.service_categories,
        bio=application.bio,
        experience_years=application.experience_years,
        portfolio=application.portfolio,
        status="pending"
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

@router.get("/applications")
async def list_applications(
    status: str = "pending",
    db: Session = Depends(get_db)
):
    apps = db.query(ProviderApplication).filter(
        ProviderApplication.status == status
    ).order_by(ProviderApplication.created_at.desc()).all()
    return apps
