PRICE_PLAN_NAMES = {
    "price_1TYj5JABXtDkfWuyQ4FD7AxQ": "Basic Plan",
    "price_1TYj6KABXtDkfWuyfS7nqBG6": "Basic Plan",
    "price_1TYjBgABXtDkfWuyIfvwPG96": "Growth Plan",
    "price_1TYjDAABXtDkfWuyuVp5Slhz": "Growth Plan",
    "price_1TYjEmABXtDkfWuyzVy2tFmM": "Pro Plan",
    "price_1TYjFfABXtDkfWuyv9p5AvoC": "Pro Plan",
}
DEFAULT_ALLOWED_PRICE_IDS = set(PRICE_PLAN_NAMES)


def normalize_stripe_object(value):
    if hasattr(value, "to_dict_recursive"):
        value = value.to_dict_recursive()
    if isinstance(value, dict):
        return {
            key: normalize_stripe_object(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalize_stripe_object(item) for item in value]
    return value


def get_stripe_value(value, key: str, default=None):
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    try:
        return value[key]
    except (KeyError, TypeError, AttributeError):
        return default


def get_stripe_id(value) -> str | None:
    if isinstance(value, str):
        return value
    return get_stripe_value(value, "id")


def parse_allowed_price_ids(raw_price_ids: str) -> set[str]:
    return {price_id.strip() for price_id in raw_price_ids.split(",") if price_id.strip()}


def get_invoice_subscription_id(invoice: dict) -> str | None:
    parent = get_stripe_value(invoice, "parent") or {}
    subscription_details = get_stripe_value(parent, "subscription_details") or {}
    return get_stripe_id(
        get_stripe_value(subscription_details, "subscription")
        or get_stripe_value(invoice, "subscription")
    )


def get_checkout_email(session: dict) -> str | None:
    customer_details = get_stripe_value(session, "customer_details") or {}
    email = get_stripe_value(customer_details, "email") or get_stripe_value(
        session, "customer_email"
    )
    return email.strip().lower() if email else None


def get_line_item_price_id(line_items: dict) -> str | None:
    items = get_stripe_value(line_items, "data") or []
    if not items:
        return None
    price = get_stripe_value(items[0], "price")
    if isinstance(price, str):
        return price
    return get_stripe_id(price)


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
