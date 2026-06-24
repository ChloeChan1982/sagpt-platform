import csv
import io
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


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

    def test_provider_admin_serialisation_and_csv_export(self):
        from app.core.providers import build_provider_csv, provider_to_admin_dict

        application = SimpleNamespace(
            id="provider-123",
            created_at=datetime(2026, 6, 24, 9, 30, tzinfo=timezone.utc),
            updated_at=None,
            status="pending",
            name="Chen Lawyer",
            email="provider@example.com",
            target_countries=["USA", "Singapore"],
            service_categories=["Legal", "Tax"],
            bio="Cross-border legal and tax services.",
            experience_years=10,
            portfolio="https://example.com",
            reviewed_by=None,
            review_notes=None,
        )

        output = provider_to_admin_dict(application)
        csv_output = build_provider_csv([application])

        self.assertEqual(output["target_countries"], ["USA", "Singapore"])
        self.assertEqual(output["service_categories"], ["Legal", "Tax"])
        self.assertEqual(output["experience_years"], 10)
        self.assertTrue(csv_output.startswith("\ufeff"))
        self.assertIn("provider@example.com", csv_output)

        rows = list(csv.DictReader(io.StringIO(csv_output.lstrip("\ufeff"))))
        self.assertEqual(rows[0]["target_countries"], '["USA", "Singapore"]')
        self.assertEqual(rows[0]["service_categories"], '["Legal", "Tax"]')

    def test_provider_admin_routes_and_dashboard_exist(self):
        root = Path(__file__).parents[1]
        router_source = (root / "app" / "routers" / "providers.py").read_text(
            encoding="utf-8"
        )
        main_source = (root / "main.py").read_text(encoding="utf-8")
        html = (root / "frontend" / "admin" / "providers.html").read_text(
            encoding="utf-8"
        )
        script = (root / "frontend" / "admin" / "providers.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('@router.get("/admin/list")', router_source)
        self.assertIn('@router.get("/admin/stats")', router_source)
        self.assertIn('@router.get("/admin/export.csv")', router_source)
        self.assertIn('@router.patch("/admin/{application_id}/status")', router_source)
        self.assertIn("SUPPORTED_PROVIDER_STATUSES", router_source)
        self.assertIn("Depends(require_admin_api_key)", router_source)
        self.assertIn('@app.get("/admin/providers"', main_source)
        self.assertIn("providers.js", html)
        self.assertIn("/api/providers/admin/list", script)
        self.assertIn("/api/providers/admin/export.csv", script)
        self.assertIn("/api/providers/admin/stats", script)


if __name__ == "__main__":
    unittest.main()
