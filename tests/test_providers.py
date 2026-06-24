import unittest
from pathlib import Path


class ProviderApplicationTests(unittest.TestCase):
    def test_readdy_payload_is_normalised_to_provider_application(self):
        from app.routers.providers import _normalise_readdy_payload

        application = _normalise_readdy_payload(
            {
                "name": "Chen Lawyer",
                "firmName": "Helix Advisory",
                "country": "USA",
                "email": "provider@example.com",
                "languages": ["Chinese", "English"],
                "expertise": {
                    "category": "Legal",
                    "years": "10 years",
                    "city": "Shenzhen",
                    "linkedin": "https://linkedin.com/in/example",
                    "website": "https://example.com",
                },
                "profileText": "Cross-border legal and tax services.",
            }
        )

        self.assertEqual(application.name, "Chen Lawyer")
        self.assertEqual(application.email, "provider@example.com")
        self.assertEqual(application.target_countries, ["USA"])
        self.assertEqual(application.service_categories, ["Legal"])
        self.assertEqual(application.bio, "Cross-border legal and tax services.")
        self.assertEqual(application.experience_years, 10)
        self.assertIn("https://linkedin.com/in/example", application.portfolio)
        self.assertIn("https://example.com", application.portfolio)

    def test_provider_router_accepts_readdy_and_legacy_paths(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "providers.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '@router.post("", response_model=schemas.ProviderApplicationResponse)',
            source,
        )
        self.assertIn(
            '@router.post("/apply", response_model=schemas.ProviderApplicationResponse)',
            source,
        )
        self.assertIn("_normalise_readdy_payload", source)


if __name__ == "__main__":
    unittest.main()
