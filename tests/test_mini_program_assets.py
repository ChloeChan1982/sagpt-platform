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

    def test_mini_program_text_is_readable_and_privacy_page_is_registered(self):
        root = Path(__file__).parents[1]
        files = [
            root / "mini-program" / "app.json",
            root / "mini-program" / "pages" / "demand" / "index.js",
            root / "mini-program" / "pages" / "demand" / "index.wxml",
            root / "mini-program" / "pages" / "privacy" / "index.wxml",
            root / "mini-program" / "pages" / "demands" / "index.wxml",
            root / "docs" / "wechat-mini-program-setup.md",
        ]

        for file in files:
            content = file.read_text(encoding="utf-8")
            self.assertNotIn("�", content, str(file))
            self.assertNotIn("鍙", content, str(file))
            self.assertNotIn("闇€", content, str(file))

        app_json = (root / "mini-program" / "app.json").read_text(encoding="utf-8")
        self.assertIn("pages/privacy/index", app_json)

    def test_publish_page_has_draft_idempotency_and_confirmation(self):
        root = Path(__file__).parents[1]
        source = (
            root / "mini-program" / "pages" / "demand" / "index.js"
        ).read_text(encoding="utf-8")
        wxml = (
            root / "mini-program" / "pages" / "demand" / "index.wxml"
        ).read_text(encoding="utf-8")

        self.assertIn("loadDraft", source)
        self.assertIn("saveDraft", source)
        self.assertIn("clearDraft", source)
        self.assertIn("client_request_id: form.client_request_id", source)
        self.assertIn("wx.showModal", source)
        self.assertIn("privacy_accepted", source)
        self.assertIn("隐私政策", wxml)


if __name__ == "__main__":
    unittest.main()
