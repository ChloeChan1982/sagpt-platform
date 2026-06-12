import unittest
from pathlib import Path

from app.core.payments import (
    DEFAULT_ALLOWED_PRICE_IDS,
    build_checkout_session_params,
    get_checkout_email,
    get_invoice_subscription_id,
    get_line_item_price_id,
    get_plan_name,
    get_stripe_id,
    has_active_membership,
    normalize_stripe_object,
    parse_allowed_price_ids,
)


class PaymentConfigurationTests(unittest.TestCase):
    def test_default_allowlist_contains_live_pricing_page_plans(self):
        self.assertIn("price_1TYjBgABXtDkfWuyIfvwPG96", DEFAULT_ALLOWED_PRICE_IDS)
        self.assertEqual(len(DEFAULT_ALLOWED_PRICE_IDS), 6)

    def test_derives_plan_name_from_trusted_price_id(self):
        self.assertEqual(get_plan_name("price_1TYjBgABXtDkfWuyIfvwPG96"), "Growth Plan")

    def test_identifies_active_membership_statuses(self):
        self.assertTrue(has_active_membership("active"))
        self.assertTrue(has_active_membership("trial"))
        self.assertFalse(has_active_membership("expired"))
        self.assertFalse(has_active_membership(None))

    def test_parses_price_id_allowlist(self):
        self.assertEqual(
            parse_allowed_price_ids("price_basic, price_growth,price_pro"),
            {"price_basic", "price_growth", "price_pro"},
        )

    def test_builds_subscription_checkout_for_allowed_price(self):
        params = build_checkout_session_params(
            price_id="price_growth",
            allowed_price_ids={"price_basic", "price_growth"},
            success_url="https://www.sagpt.com/pricing?success=true",
            cancel_url="https://www.sagpt.com/pricing?canceled=true",
            user_id="user-123",
            customer_email="member@example.com",
            plan_name="Growth Plan",
        )

        self.assertEqual(params["mode"], "subscription")
        self.assertEqual(params["line_items"], [{"price": "price_growth", "quantity": 1}])
        self.assertEqual(params["success_url"], "https://www.sagpt.com/pricing?success=true")
        self.assertEqual(params["cancel_url"], "https://www.sagpt.com/pricing?canceled=true")
        self.assertEqual(params["client_reference_id"], "user-123")
        self.assertEqual(params["customer_email"], "member@example.com")
        self.assertEqual(params["metadata"]["user_id"], "user-123")
        self.assertEqual(params["subscription_data"]["metadata"]["plan"], "Growth Plan")

    def test_rejects_price_not_in_allowlist(self):
        with self.assertRaisesRegex(ValueError, "Unsupported Stripe price ID"):
            build_checkout_session_params(
                price_id="price_attacker",
                allowed_price_ids={"price_basic"},
                success_url="https://www.sagpt.com/pricing?success=true",
                cancel_url="https://www.sagpt.com/pricing?canceled=true",
                user_id="user-123",
                customer_email="member@example.com",
                plan_name="Basic Plan",
            )

    def test_reads_subscription_id_from_current_invoice_shape(self):
        invoice = {
            "parent": {
                "subscription_details": {
                    "subscription": "sub_current",
                }
            }
        }

        self.assertEqual(get_invoice_subscription_id(invoice), "sub_current")

    def test_reads_subscription_id_from_legacy_invoice_shape(self):
        self.assertEqual(
            get_invoice_subscription_id({"subscription": "sub_legacy"}),
            "sub_legacy",
        )

    def test_reads_checkout_email_from_customer_details(self):
        session = {
            "customer_email": "fallback@example.com",
            "customer_details": {"email": "Member@Example.COM"},
        }

        self.assertEqual(get_checkout_email(session), "member@example.com")

    def test_reads_price_id_from_checkout_line_items(self):
        line_items = {
            "data": [
                {
                    "price": {
                        "id": "price_basic",
                    }
                }
            ]
        }

        self.assertEqual(get_line_item_price_id(line_items), "price_basic")

    def test_webhook_can_reprocess_previously_recorded_events(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "payments.py"
        ).read_text(encoding="utf-8")

        self.assertIn("existing_event =", source)
        self.assertIn('"duplicate": existing_event is not None', source)

    def test_normalizes_stripe_objects_before_using_dict_helpers(self):
        class FakeStripeObject:
            def to_dict_recursive(self):
                return {"parent": {"subscription_details": {"subscription": "sub_123"}}}

        normalized = normalize_stripe_object(FakeStripeObject())

        self.assertEqual(get_invoice_subscription_id(normalized), "sub_123")

    def test_normalizes_nested_stripe_objects_inside_plain_dicts(self):
        class FakeStripeObject:
            def to_dict_recursive(self):
                return {"metadata": {"user_id": "user-123"}}

        normalized = normalize_stripe_object(
            {"data": {"object": FakeStripeObject()}}
        )

        self.assertEqual(
            normalized["data"]["object"]["metadata"]["user_id"],
            "user-123",
        )

    def test_reads_id_from_expanded_stripe_object(self):
        self.assertEqual(get_stripe_id({"id": "sub_123"}), "sub_123")
        self.assertEqual(get_stripe_id("sub_456"), "sub_456")
        self.assertIsNone(get_stripe_id(None))


if __name__ == "__main__":
    unittest.main()
