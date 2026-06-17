import unittest
from pathlib import Path


class MiniDemandContractTests(unittest.TestCase):
    def test_public_mini_demand_never_contains_internal_matching_data(self):
        from app.models.schemas import MiniDemandResponse

        self.assertNotIn("matched_expert_ids", MiniDemandResponse.model_fields)
        self.assertNotIn("ai_match_score", MiniDemandResponse.model_fields)

    def test_routes_require_current_mini_user(self):
        source = Path("app/routers/mini.py").read_text(encoding="utf-8")
        self.assertIn('@router.post("/demands")', source)
        self.assertIn('@router.get("/demands")', source)
        self.assertIn('@router.get("/demands/{demand_id}")', source)
        self.assertGreaterEqual(source.count("Depends(get_current_mini_user)"), 3)

    def test_improve_endpoint_is_authenticated_and_returns_suggestion(self):
        source = Path("app/routers/mini.py").read_text(encoding="utf-8")
        self.assertIn('@router.post("/demands/improve")', source)
        self.assertIn("Depends(get_current_mini_user)", source)
        self.assertIn("improve_demand_description", source)


if __name__ == "__main__":
    unittest.main()
