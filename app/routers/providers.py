from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.demands import is_admin_api_key_valid
from app.core.providers import build_provider_csv, provider_to_admin_dict
from app.db.database import get_db
from app.models import schemas
from app.models.models import ProviderApplication

router = APIRouter(prefix="/providers", tags=["providers"])
settings = get_settings()
SUPPORTED_PROVIDER_STATUSES = {"pending", "contacted", "approved", "rejected"}


def require_admin_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if not is_admin_api_key_valid(x_api_key, settings.API_SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return x_api_key


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


def _validate_provider_status(status: Optional[str]) -> Optional[str]:
    if not status:
        return None
    if status not in SUPPORTED_PROVIDER_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported provider status")
    return status


def _contains_list_value(values: Any, expected: Optional[str]) -> bool:
    if not expected:
        return True
    needle = expected.strip().lower()
    if not needle:
        return True
    return any(needle in item.lower() for item in _as_list(values))


def _provider_admin_query(
    db: Session,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    query = db.query(ProviderApplication)
    if status:
        query = query.filter(ProviderApplication.status == status)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ProviderApplication.name.ilike(pattern),
                ProviderApplication.email.ilike(pattern),
                ProviderApplication.bio.ilike(pattern),
                ProviderApplication.portfolio.ilike(pattern),
            )
        )
    return query.order_by(ProviderApplication.created_at.desc())


def _filter_provider_applications(
    applications: list[ProviderApplication],
    country: Optional[str] = None,
    category: Optional[str] = None,
) -> list[ProviderApplication]:
    return [
        application
        for application in applications
        if _contains_list_value(application.target_countries, country)
        and _contains_list_value(application.service_categories, category)
    ]


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


@router.get("/admin/list")
async def admin_list_provider_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    status = _validate_provider_status(status)
    applications = _provider_admin_query(db, status=status, search=search).all()
    applications = _filter_provider_applications(applications, country=country, category=category)
    total = len(applications)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "applications": [provider_to_admin_dict(app) for app in applications[start:end]],
    }


@router.get("/admin/stats")
async def admin_provider_stats(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    stats = {
        status: db.query(func.count(ProviderApplication.id))
        .filter(ProviderApplication.status == status)
        .scalar()
        or 0
        for status in SUPPORTED_PROVIDER_STATUSES
    }
    stats["total"] = db.query(func.count(ProviderApplication.id)).scalar() or 0
    return stats


@router.get("/admin/export.csv")
async def admin_export_provider_applications(
    status: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    status = _validate_provider_status(status)
    applications = _provider_admin_query(db, status=status, search=search).all()
    applications = _filter_provider_applications(applications, country=country, category=category)
    filename = f"sagpt-providers-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
    return Response(
        content=build_provider_csv(applications),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/admin/{application_id}/status")
async def admin_update_provider_status(
    application_id: str,
    status_update: schemas.ProviderStatusUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    _validate_provider_status(status_update.status)
    application = (
        db.query(ProviderApplication)
        .filter(ProviderApplication.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Provider application not found")

    application.status = status_update.status
    if status_update.reviewed_by is not None:
        application.reviewed_by = status_update.reviewed_by
    if status_update.review_notes is not None:
        application.review_notes = status_update.review_notes
    db.commit()
    db.refresh(application)
    return provider_to_admin_dict(application)
