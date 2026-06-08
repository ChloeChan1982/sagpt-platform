DEFAULT_ALLOWED_PRICE_IDS = {
    "price_1TYj5JABXtDkfWuyQ4FD7AxQ",
    "price_1TYj6KABXtDkfWuyfS7nqBG6",
    "price_1TYjBgABXtDkfWuyIfvwPG96",
    "price_1TYjDAABXtDkfWuyuVp5Slhz",
    "price_1TYjEmABXtDkfWuyzVy2tFmM",
    "price_1TYjFfABXtDkfWuyv9p5AvoC",
}


def parse_allowed_price_ids(raw_price_ids: str) -> set[str]:
    return {price_id.strip() for price_id in raw_price_ids.split(",") if price_id.strip()}


def build_checkout_session_params(
    *,
    price_id: str,
    allowed_price_ids: set[str],
    success_url: str,
    cancel_url: str,
) -> dict:
    if price_id not in allowed_price_ids:
        raise ValueError("Unsupported Stripe price ID")

    return {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "allow_promotion_codes": True,
    }
