import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.mini_auth import create_mini_session, get_current_mini_user
from app.db.database import get_db
from app.models import schemas
from app.models.models import Demand, DemandAttachment, MiniUser
from app.routers.demands import schedule_demand_matching
from app.services.wechat_service import WeChatAPIError, WeChatService


router = APIRouter(prefix="/mini", tags=["mini"])


@router.post("/auth/login", response_model=schemas.MiniLoginResponse)
async def mini_login(
    request: schemas.MiniLoginRequest,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    service = WeChatService(
        app_id=settings.WECHAT_APP_ID,
        app_secret=settings.WECHAT_APP_SECRET,
    )
    try:
        payload = await service.exchange_code(request.code)
    except WeChatAPIError as exc:
        raise HTTPException(status_code=502, detail="WeChat login failed") from exc

    openid = payload.get("openid")
    if not openid:
        raise HTTPException(status_code=502, detail="WeChat login failed")

    user = db.query(MiniUser).filter(MiniUser.openid == openid).first()
    if not user:
        user = MiniUser(openid=openid, unionid=payload.get("unionid"))
        db.add(user)
        db.flush()
    elif payload.get("unionid") and not user.unionid:
        user.unionid = payload["unionid"]

    token, expires_at = create_mini_session(db, user.id)
    db.commit()
    return {
        "token": token,
        "user_id": user.id,
        "expires_at": expires_at,
    }


@router.get("/me")
def mini_me(user: MiniUser = Depends(get_current_mini_user)):
    return {"user_id": user.id, "phone": user.phone}


def _mini_demand_response(demand: Demand) -> schemas.MiniDemandResponse:
    attachment_ids = demand.attachments or []
    return schemas.MiniDemandResponse(
        id=demand.id,
        target_country=demand.target_country,
        industry=demand.industry,
        scenario=demand.scenario,
        budget_range=demand.budget_range,
        urgency=demand.urgency,
        description=demand.description,
        company_name=demand.company_name or "",
        wechat_phone=demand.wechat_phone or "",
        phone=demand.phone or "",
        email=demand.email or None,
        status=demand.status,
        attachment_ids=attachment_ids,
        created_at=demand.created_at,
        updated_at=demand.updated_at,
    )


@router.post("/demands")
async def create_mini_demand(
    request: Request,
    demand_data: schemas.MiniDemandCreate,
    db: Session = Depends(get_db),
    mini_user: MiniUser = Depends(get_current_mini_user),
):
    existing = (
        db.query(Demand)
        .filter(Demand.client_request_id == demand_data.client_request_id)
        .first()
    )
    if existing:
        if existing.mini_user_id != mini_user.id:
            raise HTTPException(status_code=409, detail="Duplicate request id")
        return _mini_demand_response(existing)

    attachment_ids = [str(attachment_id) for attachment_id in demand_data.attachment_ids]
    if attachment_ids:
        attachments = (
            db.query(DemandAttachment)
            .filter(
                DemandAttachment.id.in_(attachment_ids),
                DemandAttachment.mini_user_id == mini_user.id,
                DemandAttachment.demand_id.is_(None),
            )
            .all()
        )
        if len(attachments) != len(attachment_ids):
            raise HTTPException(status_code=400, detail="Invalid attachment")
    else:
        attachments = []

    demand = Demand(
        mini_user_id=mini_user.id,
        client_request_id=demand_data.client_request_id,
        target_country=demand_data.target_country,
        industry=demand_data.industry,
        scenario=demand_data.scenario,
        budget_range=demand_data.budget_range,
        urgency=demand_data.urgency,
        description=demand_data.description,
        email=str(demand_data.email) if demand_data.email else "",
        wechat_phone=demand_data.wechat_phone,
        company_name=demand_data.company_name,
        phone=demand_data.phone,
        attachments=attachment_ids,
        status="pending",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(demand)
    db.flush()
    for attachment in attachments:
        attachment.demand_id = demand.id
    db.commit()
    db.refresh(demand)

    schedule_demand_matching(str(demand.id))
    return _mini_demand_response(demand)


@router.get("/demands")
def list_mini_demands(
    db: Session = Depends(get_db),
    mini_user: MiniUser = Depends(get_current_mini_user),
):
    demands = (
        db.query(Demand)
        .filter(Demand.mini_user_id == mini_user.id)
        .order_by(Demand.created_at.desc())
        .all()
    )
    return [_mini_demand_response(demand) for demand in demands]


@router.get("/demands/{demand_id}")
def get_mini_demand(
    demand_id: uuid.UUID,
    db: Session = Depends(get_db),
    mini_user: MiniUser = Depends(get_current_mini_user),
):
    demand = (
        db.query(Demand)
        .filter(Demand.id == str(demand_id), Demand.mini_user_id == mini_user.id)
        .first()
    )
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    return _mini_demand_response(demand)
