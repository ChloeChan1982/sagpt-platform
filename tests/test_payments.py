import unittest

from app.core.payments import build_checkout_session_params, parse_allowed_price_ids


class PaymentConfigurationTests(unittest.TestCase):
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
        )

        self.assertEqual(params["mode"], "subscription")
        self.assertEqual(params["line_items"], [{"price": "price_growth", "quantity": 1}])
        self.assertEqual(params["success_url"], "https://www.sagpt.com/pricing?success=true")
        self.assertEqual(params["cancel_url"], "https://www.sagpt.com/pricing?canceled=true")

    def test_rejects_price_not_in_allowlist(self):
        with self.assertRaisesRegex(ValueError, "Unsupported Stripe price ID"):
            build_checkout_session_params(
                price_id="price_attacker",
                allowed_price_ids={"price_basic"},
                success_url="https://www.sagpt.com/pricing?success=true",
                cancel_url="https://www.sagpt.com/pricing?canceled=true",
            )


if __name__ == "__main__":
    unittest.main()
