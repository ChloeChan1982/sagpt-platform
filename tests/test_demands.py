import unittest
from pathlib import Path
from types import SimpleNamespace


class DemandAdministrationTests(unittest.TestCase):
    def test_admin_api_key_rejects_missing_or_invalid_key(self):
        from app.core.demands import is_admin_api_key_valid

        self.assertFalse(is_admin_api_key_valid(None, "admin-secret"))
        self.assertFalse(is_admin_api_key_valid("wrong-secret", "admin-secret"))
        self.assertFalse(
            is_admin_api_key_valid(
                "sagpt-dev-secret-key-change-in-production",
                "sagpt-dev-secret-key-change-in-production",
            )
        )

    def test_admin_api_key_accepts_matching_key(self):
        from app.core.demands import is_admin_api_key_valid

        self.assertTrue(is_admin_api_key_valid("admin-secret", "admin-secret"))

    def test_csv_export_is_excel_compatible_and_contains_demand_details(self):
        from app.core.demands import build_demand_csv, demand_to_admin_dict

        demand = SimpleNamespace(
            id="demand-123",
            created_at="2026-06-13T12:00:00+08:00",
            status="pending",
            company_name="SAGPT QA Test Company",
            email="qa@example.com",
            phone="+1 555 0100",
            wechat_phone="qa-wechat",
            target_country="Singapore",
            industry="Technology",
            scenario="Market entry",
            budget_range="USD 10,000-20,000",
            urgency="urgent",
            description="Need a Singapore market-entry advisor.",
            attachments=["https://example.com/brief.pdf"],
            ai_match_score=0.0,
            matched_expert_ids=[],
        )

        output = build_demand_csv([demand])

        self.assertTrue(output.startswith("\ufeff"))
        self.assertIn("SAGPT QA Test Company", output)
        self.assertIn("qa@example.com", output)
        self.assertIn("https://example.com/brief.pdf", output)
        self.assertEqual(
            demand_to_admin_dict(demand)["attachments"],
            ["https://example.com/brief.pdf"],
        )

    def test_routes_detach_matching_and_expose_protected_admin_endpoints(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "demands.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "asyncio.create_task(asyncio.to_thread(run_demand_matching, demand_id))",
            source,
        )
        self.assertIn("schedule_demand_matching(str(demand.id))", source)
        self.assertNotIn("background_tasks.add_task", source)
        self.assertIn('@router.get("/admin/list")', source)
        self.assertIn('@router.get("/admin/export.csv")', source)
        self.assertGreaterEqual(source.count("Depends(require_admin_api_key)"), 2)

    def test_admin_status_update_contract_is_protected_and_validated(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "demands.py"
        ).read_text(encoding="utf-8")

        self.assertIn('@router.patch("/admin/{demand_id}/status")', source)
        self.assertIn("Depends(require_admin_api_key)", source)
        self.assertIn("SUPPORTED_DEMAND_STATUSES", source)
        self.assertIn("Unsupported demand status", source)

    def test_admin_stats_contract_is_protected_and_counts_operational_statuses(self):
        source = (
            Path(__file__).parents[1] / "app" / "routers" / "demands.py"
        ).read_text(encoding="utf-8")

        self.assertIn('@router.get("/admin/stats")', source)
        for status in ("pending", "matching", "contacted", "completed", "closed"):
            self.assertIn(f'"{status}"', source)


if __name__ == "__main__":
    unittest.main()
