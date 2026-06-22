from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.demands import build_demand_csv, demand_to_admin_dict, is_admin_api_key_valid
from app.db.database import get_db, SessionLocal
from app.models import schemas
from app.models.models import Demand, MiniSubscriptionGrant, MiniUser
from app.services.ai_service import get_llm_service, get_matching_service
from app.services.wechat_service import WeChatAPIError, WeChatService

router = APIRouter(prefix="/demands", tags=["demands"])
settings = get_settings()
matching_tasks = set()
SUPPORTED_DEMAND_STATUSES = {
    "pending",
    "matching",
    "contacted",
    "completed",
    "closed",
}
NOTIFIABLE_DEMAND_STATUSES = {"contacted", "completed"}


def require_admin_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not is_admin_api_key_valid(x_api_key, settings.API_SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return x_api_key


async def process_demand_matching(demand_id: str):
    db = SessionLocal()
    try:
        demand = db.query(Demand).filter(Demand.id == demand_id).first()
        if not demand:
            return

        llm = get_llm_service()
        embedding = await llm.get_embedding(
            f"Country: {demand.target_country}. Industry: {demand.industry}. "
            f"Scenario: {demand.scenario}. Budget: {demand.budget_range}. "
            f"Need: {demand.description}"
        )
        if embedding:
            demand.description_embedding = embedding
            db.commit()

        matcher = get_matching_service()
        matches = await matcher.find_matches(db, demand, top_k=5, min_score=0.2)
        demand.matched_expert_ids = [str(match.expert_id) for match in matches[:3]]
        demand.ai_match_score = matches[0].match_score if matches else 0.0
        demand.status = "matching"
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Demand matching error for {demand_id}: {type(exc).__name__}: {exc}")
    finally:
        db.close()


def run_demand_matching(demand_id: str):
    asyncio.run(process_demand_matching(demand_id))


def schedule_demand_matching(demand_id: str):
    task = asyncio.create_task(asyncio.to_thread(run_demand_matching, demand_id))
    matching_tasks.add(task)
    task.add_done_callback(matching_tasks.discard)


def apply_demand_filters(query, status=None, country=None, search=None):
    if status:
        query = query.filter(Demand.status == status)
    if country:
        query = query.filter(Demand.target_country == country)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Demand.company_name.ilike(pattern),
                Demand.email.ilike(pattern),
                Demand.description.ilike(pattern),
            )
        )
    return query


def _template_id_for_status(status: str) -> str:
    if status == "contacted":
        return settings.WECHAT_CONTACTED_TEMPLATE_ID
    if status == "completed":
        return settings.WECHAT_COMPLETED_TEMPLATE_ID
    return ""


async def send_demand_status_notification(db: Session, demand: Demand):
    if demand.status not in NOTIFIABLE_DEMAND_STATUSES or not demand.mini_user_id:
        return

    template_id = _template_id_for_status(demand.status)
    if not template_id:
        return

    mini_user = db.query(MiniUser).filter(MiniUser.id == demand.mini_user_id).first()
    if not mini_user:
        return

    grant = (
        db.query(MiniSubscriptionGrant)
        .filter(
            MiniSubscriptionGrant.mini_user_id == mini_user.id,
            MiniSubscriptionGrant.template_id == template_id,
            MiniSubscriptionGrant.remaining_uses > 0,
        )
        .first()
    )
    if not grant:
        return

    service = WeChatService(
        app_id=settings.WECHAT_APP_ID,
        app_secret=settings.WECHAT_APP_SECRET,
    )
    status_label = "已联系" if demand.status == "contacted" else "已完成"
    await service.send_subscription_message(
        openid=mini_user.openid,
        template_id=template_id,
        page=f"pages/demands/detail?id={demand.id}",
        data={
            "thing1": {"value": (demand.company_name or "您的需求")[:20]},
            "phrase2": {"value": status_label},
            "thing3": {"value": (demand.target_country or "目标国家")[:20]},
        },
    )
    grant.remaining_uses -= 1
    if grant.remaining_uses <= 0:
        db.delete(grant)
    db.commit()

@router.post("/submit", response_model=schemas.DemandSubmitResponse)
async def submit_demand(
    request: Request,
    demand_data: schemas.DemandCreate,
    db: Session = Depends(get_db)
):
    demand = Demand(
        target_country=demand_data.target_country,
        industry=demand_data.industry,
        scenario=demand_data.scenario,
        budget_range=demand_data.budget_range,
        urgency=demand_data.urgency,
        description=demand_data.description,
        email=demand_data.email,
        wechat_phone=demand_data.wechat_phone,
        company_name=demand_data.company_name,
        phone=demand_data.phone,
        attachments=demand_data.attachments or [],
        status="pending",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    db.add(demand)
    db.commit()
    db.refresh(demand)

    schedule_demand_matching(str(demand.id))

    return schemas.DemandSubmitResponse(
        success=True,
        demand_id=uuid.UUID(str(demand.id)),
        message="Your demand has been submitted successfully! Our AI is analyzing your needs.",
        estimated_match_time="within 24 hours",
        preview_matches=[]
    )


@router.get("/admin/list")
async def list_demands_for_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    query = apply_demand_filters(db.query(Demand), status, country, search)
    total = query.count()
    demands = (
        query.order_by(Demand.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "demands": [demand_to_admin_dict(demand) for demand in demands],
    }


@router.get("/admin/export.csv")
async def export_demands_for_admin(
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    query = apply_demand_filters(db.query(Demand), status, country, search)
    demands = query.order_by(Demand.created_at.desc()).all()
    filename = f"sagpt-demands-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
    return Response(
        content=build_demand_csv(demands),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/admin/stats")
async def get_admin_demand_stats(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    counts = {
        status: db.query(func.count(Demand.id))
        .filter(Demand.status == status)
        .scalar()
        or 0
        for status in SUPPORTED_DEMAND_STATUSES
    }
    return {
        "total": db.query(func.count(Demand.id)).scalar() or 0,
        **counts,
    }


@router.patch("/admin/{demand_id}/status")
async def update_demand_status_for_admin(
    demand_id: uuid.UUID,
    status_update: schemas.DemandStatusUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_api_key),
):
    if status_update.status not in SUPPORTED_DEMAND_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported demand status")

    demand = db.query(Demand).filter(Demand.id == str(demand_id)).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")

    demand.status = status_update.status
    db.commit()
    db.refresh(demand)
    if status_update.status in NOTIFIABLE_DEMAND_STATUSES:
        try:
            await send_demand_status_notification(db, demand)
        except WeChatAPIError as exc:
            db.rollback()
            print(
                f"WeChat demand notification failed for {demand.id}: "
                f"{type(exc).__name__}: {exc}"
            )
    return demand_to_admin_dict(demand)


@router.get("/{demand_id}", response_model=schemas.DemandResponse)
async def get_demand(demand_id: uuid.UUID, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == str(demand_id)).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    return demand

@router.get("/{demand_id}/matches", response_model=List[schemas.MatchPreview])
async def get_demand_matches(
    demand_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    demand = db.query(Demand).filter(Demand.id == str(demand_id)).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")

    matcher = get_matching_service()
    matches = await matcher.find_matches(db, demand, top_k=8, min_score=0.2)
    return matches

@router.post("/{demand_id}/rematch")
async def rematch_demand(
    demand_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    demand = db.query(Demand).filter(Demand.id == str(demand_id)).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")

    llm = get_llm_service()
    embedding = await llm.get_embedding(
        f"Country: {demand.target_country}. Industry: {demand.industry}. "
        f"Scenario: {demand.scenario}. Need: {demand.description}"
    )
    if embedding:
        demand.description_embedding = embedding

    matcher = get_matching_service()
    matches = await matcher.find_matches(db, demand, top_k=5)

    demand.matched_expert_ids = [str(m.expert_id) for m in matches[:3]]
    demand.status = "matching"
    db.commit()

    return {"success": True, "matches_count": len(matches), "matches": matches}

@router.get("/stats/summary")
async def get_demand_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Demand.id)).scalar()
    pending = db.query(func.count(Demand.id)).filter(Demand.status == "pending").scalar()
    matched = db.query(func.count(Demand.id)).filter(Demand.status == "matched").scalar()

    top_countries = db.query(
        Demand.target_country,
        func.count(Demand.id).label("count")
    ).group_by(Demand.target_country).order_by(func.count(Demand.id).desc()).limit(5).all()

    return {
        "total_demands": total,
        "pending": pending,
        "matched": matched,
        "top_countries": [{"country": c[0], "count": c[1]} for c in top_countries]
    }
