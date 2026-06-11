import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.auth import (
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    normalize_email,
    verify_password,
)
from app.db.database import get_db
from app.models import schemas
from app.models.models import AuthToken, Membership, User, UserSession
from app.services.email_service import (
    EmailDeliveryError,
    reset_email_html,
    send_auth_email,
    verification_email_html,
)


router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_COOKIE = "sagpt_session"


def _now() -> datetime:
    return datetime.utcnow()


def _public_user(user: User, membership: Membership | None) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "firmName": user.firm_name,
        "country": user.country,
        "avatar": user.avatar,
        "verifiedEmail": user.verified_email,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "membership": {
            "plan": membership.plan if membership else "none",
            "status": membership.status if membership else "none",
            "expiresAt": membership.expires_at.isoformat()
            if membership and membership.expires_at
            else None,
        },
    }


def _create_action_token(db: Session, user_id: str, purpose: str, lifetime: timedelta) -> str:
    raw_token = generate_opaque_token()
    db.add(
        AuthToken(
            user_id=user_id,
            token_hash=hash_opaque_token(raw_token),
            purpose=purpose,
            expires_at=_now() + lifetime,
        )
    )
    return raw_token


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=30 * 24 * 60 * 60,
        secure=True,
        httponly=True,
        samesite="lax",
        domain=os.getenv("AUTH_COOKIE_DOMAIN", ".sagpt.com"),
        path="/",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == hash_opaque_token(raw_token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > _now(),
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_verified_user(user: User = Depends(get_current_user)) -> User:
    if not user.verified_email:
        raise HTTPException(status_code=403, detail="Email verification required")
    return user


@router.post("/register", status_code=201)
def register(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(
        email=email,
        name=request.name.strip(),
        password_hash=hash_password(request.password),
        firm_name=request.firm_name,
        country=request.country,
    )
    db.add(user)
    db.flush()
    token = _create_action_token(db, user.id, "verify_email", timedelta(hours=24))
    try:
        send_auth_email(
            to_email=user.email,
            subject="Verify your SAGPT email",
            html=verification_email_html(token),
        )
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Verification email service is unavailable",
        ) from exc
    db.commit()
    return {"message": "Registration successful. Check your email to verify your account."}


@router.post("/verify-email")
def verify_email(request: schemas.TokenRequest, db: Session = Depends(get_db)):
    token = (
        db.query(AuthToken)
        .filter(
            AuthToken.token_hash == hash_opaque_token(request.token),
            AuthToken.purpose == "verify_email",
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > _now(),
        )
        .first()
    )
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.query(User).filter(User.id == token.user_id).first()
    user.verified_email = True
    token.used_at = _now()
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/login")
def login(request: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == normalize_email(request.email)).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.verified_email:
        raise HTTPException(status_code=403, detail="Email verification required")

    raw_token = generate_opaque_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=_now() + timedelta(days=30),
        )
    )
    db.commit()
    _set_session_cookie(response, raw_token)
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    return {"user": _public_user(user, membership)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        session = db.query(UserSession).filter(
            UserSession.token_hash == hash_opaque_token(raw_token)
        ).first()
        if session:
            session.revoked_at = _now()
            db.commit()
    response.delete_cookie(
        SESSION_COOKIE,
        domain=os.getenv("AUTH_COOKIE_DOMAIN", ".sagpt.com"),
        path="/",
    )
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    return {"user": _public_user(user, membership)}


@router.post("/forgot-password")
def forgot_password(request: schemas.EmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == normalize_email(request.email)).first()
    if user:
        token = _create_action_token(db, user.id, "reset_password", timedelta(minutes=30))
        db.commit()
        send_auth_email(
            to_email=user.email,
            subject="Reset your SAGPT password",
            html=reset_email_html(token),
        )
    return {"message": "If the account exists, a reset email has been sent."}


@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    token = (
        db.query(AuthToken)
        .filter(
            AuthToken.token_hash == hash_opaque_token(request.token),
            AuthToken.purpose == "reset_password",
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > _now(),
        )
        .first()
    )
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.query(User).filter(User.id == token.user_id).first()
    user.password_hash = hash_password(request.password)
    token.used_at = _now()
    db.query(UserSession).filter(
        UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
    ).update({"revoked_at": _now()})
    db.commit()
    return {"message": "Password reset successfully"}
