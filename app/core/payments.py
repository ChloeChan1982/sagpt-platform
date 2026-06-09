PRICE_PLAN_NAMES = {
    "price_1TYj5JABXtDkfWuyQ4FD7AxQ": "Basic Plan",
    "price_1TYj6KABXtDkfWuyfS7nqBG6": "Basic Plan",
    "price_1TYjBgABXtDkfWuyIfvwPG96": "Growth Plan",
    "price_1TYjDAABXtDkfWuyuVp5Slhz": "Growth Plan",
    "price_1TYjEmABXtDkfWuyzVy2tFmM": "Pro Plan",
    "price_1TYjFfABXtDkfWuyv9p5AvoC": "Pro Plan",
}
DEFAULT_ALLOWED_PRICE_IDS = set(PRICE_PLAN_NAMES)


def parse_allowed_price_ids(raw_price_ids: str) -> set[str]:
    return {price_id.strip() for price_id in raw_price_ids.split(",") if price_id.strip()}


def get_invoice_subscription_id(invoice: dict) -> str | None:
    parent = invoice.get("parent") or {}
    subscription_details = parent.get("subscription_details") or {}
    return subscription_details.get("subscription") or invoice.get("subscription")


def get_plan_name(price_id: str) -> str:
    return PRICE_PLAN_NAMES.get(price_id, "SAGPT Membership")


def has_active_membership(status: str | None) -> bool:
    return status in {"active", "trial"}


def build_checkout_session_params(
    *,
    price_id: str,
    allowed_price_ids: set[str],
    success_url: str,
    cancel_url: str,
    user_id: str,
    customer_email: str,
    plan_name: str,
) -> dict:
    if price_id not in allowed_price_ids:
        raise ValueError("Unsupported Stripe price ID")

    return {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "allow_promotion_codes": True,
        "client_reference_id": user_id,
        "customer_email": customer_email,
        "metadata": {
            "user_id": user_id,
            "plan": plan_name,
            "price_id": price_id,
        },
        "subscription_data": {
            "metadata": {
                "user_id": user_id,
                "plan": plan_name,
                "price_id": price_id,
            }
        },
    }
