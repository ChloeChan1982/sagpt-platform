import unittest
from pathlib import Path

from app.core.auth import (
    hash_opaque_token,
    hash_password,
    map_stripe_membership_status,
    normalize_email,
    verify_password,
)


class AuthenticationTests(unittest.TestCase):
    def test_normalizes_email(self):
        self.assertEqual(normalize_email("  Person@Example.COM "), "person@example.com")

    def test_hashes_and_verifies_password(self):
        encoded = hash_password("correct horse battery staple")

        self.assertNotIn("correct horse battery staple", encoded)
        self.assertTrue(verify_password("correct horse battery staple", encoded))
        self.assertFalse(verify_password("wrong password", encoded))

    def test_hashes_opaque_tokens_deterministically(self):
        self.assertEqual(hash_opaque_token("secret"), hash_opaque_token("secret"))
        self.assertNotEqual(hash_opaque_token("secret"), hash_opaque_token("other"))

    def test_maps_stripe_membership_status(self):
        self.assertEqual(map_stripe_membership_status("trialing"), "active")
        self.assertEqual(map_stripe_membership_status("active"), "active")
        self.assertEqual(map_stripe_membership_status("past_due"), "expired")
        self.assertEqual(map_stripe_membership_status("canceled"), "expired")
        self.assertEqual(map_stripe_membership_status(None), "none")

    def test_registration_converts_email_delivery_failure_to_service_unavailable(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "auth.py"
        ).read_text(encoding="utf-8")

        self.assertIn("except EmailDeliveryError", source)
        self.assertIn("Verification email service is unavailable", source)

    def test_resend_request_identifies_the_application(self):
        source = (
            Path(__file__).parents[1] / "app" / "services" / "email_service.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"User-Agent": "SAGPT-Backend/1.0"', source)


if __name__ == "__main__":
    unittest.main()
