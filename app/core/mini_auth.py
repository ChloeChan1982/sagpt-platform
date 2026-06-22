from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import generate_opaque_token, hash_opaque_token
from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import MiniSession, MiniUser


def _now() -> datetime:
    return datetime.utcnow()


def parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return token.strip()


def create_mini_session(db: Session, mini_user_id: str) -> tuple[str, datetime]:
    settings = get_settings()
    raw_token = generate_opaque_token()
    expires_at = _now() + timedelta(days=settings.MINI_SESSION_DAYS)
    db.add(
        MiniSession(
            mini_user_id=mini_user_id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=expires_at,
        )
    )
    return raw_token, expires_at


def get_current_mini_user(
    request: Request, db: Session = Depends(get_db)
) -> MiniUser:
    raw_token = parse_bearer_token(request.headers.get("Authorization"))
    session = (
        db.query(MiniSession)
        .filter(
            MiniSession.token_hash == hash_opaque_token(raw_token),
            MiniSession.revoked_at.is_(None),
            MiniSession.expires_at > _now(),
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.query(MiniUser).filter(MiniUser.id == session.mini_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
