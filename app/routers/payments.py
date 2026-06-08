import os

from fastapi import APIRouter, HTTPException

from app.core.payments import (
    DEFAULT_ALLOWED_PRICE_IDS,
    build_checkout_session_params,
    parse_allowed_price_ids,
)
from app.models.schemas import CheckoutSessionRequest, CheckoutSessionResponse


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(request: CheckoutSessionRequest):
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe payments are not configured")

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
