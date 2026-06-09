import unittest

from app.core.payments import (
    DEFAULT_ALLOWED_PRICE_IDS,
    build_checkout_session_params,
    get_invoice_subscription_id,
    get_plan_name,
    has_active_membership,
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


if __name__ == "__main__":
    unittest.main()
