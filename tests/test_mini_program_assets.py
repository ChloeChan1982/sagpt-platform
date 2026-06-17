import unittest
from pathlib import Path


class MiniProgramAssetTests(unittest.TestCase):
    def test_mini_program_contains_required_pages_and_api_base(self):
        root = Path(__file__).parents[1]
        app_json = (root / "mini-program" / "app.json").read_text(encoding="utf-8")
        config_js = (
            root / "mini-program" / "utils" / "config.js"
        ).read_text(encoding="utf-8")

        for page in (
            "pages/login/index",
            "pages/demand/index",
            "pages/demands/index",
            "pages/demand-detail/index",
        ):
            self.assertIn(page, app_json)

        self.assertIn("https://api.sagpt.com/api/mini", config_js)

    def test_demand_page_supports_core_customer_flow(self):
        root = Path(__file__).parents[1]
        source = (
            root / "mini-program" / "pages" / "demand" / "index.js"
        ).read_text(encoding="utf-8")

        self.assertIn("requestSubscribeMessage", source)
        self.assertIn("uploadAttachment", source)
        self.assertIn('url: "/demands/improve"', source)
        self.assertIn('url: "/demands"', source)


if __name__ == "__main__":
    unittest.main()
