import os

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.payments import (
    DEFAULT_ALLOWED_PRICE_IDS,
    build_checkout_session_params,
    get_checkout_email,
    get_invoice_subscription_id,
    get_line_item_price_id,
    get_plan_name,
    has_active_membership,
    parse_allowed_price_ids,
)
from app.core.auth import map_stripe_membership_status
from app.db.database import get_db
from app.models.schemas import CheckoutSessionRequest, CheckoutSessionResponse
from app.models.models import Membership, StripeWebhookEvent, User
from app.routers.auth import require_verified_user


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe payments are not configured")

    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if membership and has_active_membership(membership.status):
        raise HTTPException(
            status_code=409,
            detail="This account already has an active membership",
        )

    configured_price_ids = parse_allowed_price_ids(os.getenv("STRIPE_ALLOWED_PRICE_IDS", ""))
    allowed_price_ids = configured_price_ids or DEFAULT_ALLOWED_PRICE_IDS
    try:
        params = build_checkout_session_params(
            price_id=request.price_id,
            allowed_price_ids=allowed_price_ids,
            success_url=os.getenv(
                "STRIPE_SUCCESS_URL",
                "https://www.sagpt.com/pricing?success=true",
            ),
            cancel_url=os.getenv(
                "STRIPE_CANCEL_URL",
                "https://www.sagpt.com/pricing?canceled=true",
            ),
            user_id=user.id,
            customer_email=user.email,
            plan_name=get_plan_name(request.price_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        import stripe

        session = stripe.checkout.Session.create(api_key=stripe_secret_key, **params)
    except Exception as exc:
        print(f"Stripe Checkout error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="Unable to initialize payment") from exc

    return CheckoutSessionResponse(url=session.url)


def _upsert_membership(
    db: Session,
    *,
    user_id: str,
    plan: str | None = None,
    status: str | None = None,
    customer_id: str | None = None,
    subscription_id: str | None = None,
    price_id: str | None = None,
    expires_at: datetime | None = None,
) -> Membership:
    membership = db.query(Membership).filter(Membership.user_id == user_id).first()
    if not membership:
        membership = Membership(user_id=user_id)
        db.add(membership)
    if plan:
        membership.plan = plan
    membership.status = map_stripe_membership_status(status)
    if customer_id:
        membership.stripe_customer_id = customer_id
    if subscription_id:
        membership.stripe_subscription_id = subscription_id
    if price_id:
        membership.stripe_price_id = price_id
    membership.expires_at = expires_at
    return membership


def _metadata_value(obj, key: str):
    metadata = obj.get("metadata") or {}
    return metadata.get(key)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        import stripe

        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature") from exc

    existing_event = db.query(StripeWebhookEvent).filter(
        StripeWebhookEvent.event_id == event["id"]
    ).first()

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = _metadata_value(obj, "user_id") or obj.get("client_reference_id")
        price_id = _metadata_value(obj, "price_id")
        if not price_id and obj.get("id"):
            line_items = stripe.checkout.Session.list_line_items(
                obj["id"],
                limit=1,
                api_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
            )
            price_id = get_line_item_price_id(line_items)
        if not user_id:
            checkout_email = get_checkout_email(obj)
            if checkout_email:
                matched_user = db.query(User).filter(
                    User.email == checkout_email,
                    User.verified_email.is_(True),
                ).first()
                if matched_user:
                    user_id = matched_user.id
        if user_id and price_id in DEFAULT_ALLOWED_PRICE_IDS:
            _upsert_membership(
                db,
                user_id=user_id,
                plan=_metadata_value(obj, "plan") or get_plan_name(price_id),
                status="active" if obj.get("payment_status") == "paid" else "incomplete",
                customer_id=obj.get("customer"),
                subscription_id=obj.get("subscription"),
                price_id=price_id,
            )
    elif event_type.startswith("customer.subscription."):
        user_id = _metadata_value(obj, "user_id")
        membership = None
        if user_id:
            membership = _upsert_membership(
                db,
                user_id=user_id,
                plan=_metadata_value(obj, "plan"),
                status=obj.get("status"),
                customer_id=obj.get("customer"),
                subscription_id=obj.get("id"),
                price_id=_metadata_value(obj, "price_id"),
                expires_at=datetime.utcfromtimestamp(obj["current_period_end"])
                if obj.get("current_period_end")
                else None,
            )
        elif obj.get("id"):
            membership = db.query(Membership).filter(
                Membership.stripe_subscription_id == obj.get("id")
            ).first()
            if membership:
                membership.status = map_stripe_membership_status(obj.get("status"))
    elif event_type in {"invoice.paid", "invoice.payment_failed"}:
        subscription_id = get_invoice_subscription_id(obj)
        membership = db.query(Membership).filter(
            Membership.stripe_subscription_id == subscription_id
        ).first()
        if membership:
            membership.status = "active" if event_type == "invoice.paid" else "expired"

    if existing_event is None:
        db.add(StripeWebhookEvent(event_id=event["id"], event_type=event_type))
    db.commit()
    return {"received": True, "duplicate": existing_event is not None}
