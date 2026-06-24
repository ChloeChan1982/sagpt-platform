from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import Any

from app.db.database import get_db
from app.models import schemas
from app.models.models import ProviderApplication

router = APIRouter(prefix="/providers", tags=["providers"])


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _parse_experience_years(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = "".join(char for char in value if char.isdigit())
        return int(digits) if digits else None
    return None


def _normalise_readdy_payload(payload: dict[str, Any]) -> schemas.ProviderApplyRequest:
    expertise = payload.get("expertise") or {}
    if not isinstance(expertise, dict):
        expertise = {}

    country = payload.get("country") or payload.get("target_country")
    category = (
        expertise.get("category")
        or payload.get("serviceCategory")
        or payload.get("service_category")
    )

    portfolio_items = [
        payload.get("portfolio"),
        payload.get("website"),
        payload.get("linkedin"),
        expertise.get("website"),
        expertise.get("linkedin"),
    ]
    portfolio = "\n".join(str(item).strip() for item in portfolio_items if item)

    normalised = {
        "name": payload.get("name")
        or payload.get("firmName")
        or payload.get("organization"),
        "email": payload.get("email"),
        "target_countries": payload.get("target_countries")
        or payload.get("targetCountries")
        or _as_list(country),
        "service_categories": payload.get("service_categories")
        or payload.get("serviceCategories")
        or _as_list(category),
        "bio": payload.get("bio")
        or payload.get("profileText")
        or payload.get("introduction"),
        "experience_years": payload.get("experience_years")
        or payload.get("experienceYears")
        or _parse_experience_years(expertise.get("years")),
        "portfolio": portfolio or None,
    }

    try:
        return schemas.ProviderApplyRequest.model_validate(normalised)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _save_provider_application(
    application: schemas.ProviderApplyRequest, db: Session
) -> ProviderApplication:
    app = ProviderApplication(
        name=application.name,
        email=application.email,
        target_countries=application.target_countries,
        service_categories=application.service_categories,
        bio=application.bio,
        experience_years=application.experience_years,
        portfolio=application.portfolio,
        status="pending",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.post("", response_model=schemas.ProviderApplicationResponse)
@router.post("/", response_model=schemas.ProviderApplicationResponse)
async def apply_provider_from_readdy(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    application = _normalise_readdy_payload(payload)
    return _save_provider_application(application, db)


@router.post("/apply", response_model=schemas.ProviderApplicationResponse)
async def apply_provider(
    application: schemas.ProviderApplyRequest,
    db: Session = Depends(get_db),
):
    """
    Submit provider application.
    """
    return _save_provider_application(application, db)


@router.get("/applications")
async def list_applications(
    status: str = "pending",
    db: Session = Depends(get_db),
):
    apps = (
        db.query(ProviderApplication)
        .filter(ProviderApplication.status == status)
        .order_by(ProviderApplication.created_at.desc())
        .all()
    )
    return apps
