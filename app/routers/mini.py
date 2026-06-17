from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.mini_auth import create_mini_session, get_current_mini_user
from app.db.database import get_db
from app.models import schemas
from app.models.models import MiniUser
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
