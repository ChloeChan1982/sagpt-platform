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

        self.assertIn('url: "/demands"', source)
        self.assertIn("client_request_id: form.client_request_id", source)
        self.assertIn("privacy_accepted", source)

    def test_mini_program_uses_consultation_registration_copy(self):
        root = Path(__file__).parents[1]
        files = [
            root / "mini-program" / "app.json",
            root / "mini-program" / "pages" / "login" / "index.wxml",
            root / "mini-program" / "pages" / "login" / "index.js",
            root / "mini-program" / "pages" / "demand" / "index.wxml",
            root / "mini-program" / "pages" / "demand" / "index.js",
            root / "mini-program" / "pages" / "privacy" / "index.wxml",
            root / "mini-program" / "utils" / "api.js",
            root / "mini-program" / "utils" / "config.js",
        ]
        combined = "\n".join(file.read_text(encoding="utf-8") for file in files)
        for blocked in (
            "\u53d1\u5e03\u9700\u6c42",
            "\u63d0\u4ea4\u9700\u6c42",
            "\u6211\u7684\u9700\u6c42",
            "AI \u4f18\u5316\u63cf\u8ff0",
            "AI\u4f18\u5316",
            "\u9644\u4ef6",
            "\u9009\u62e9\u9644\u4ef6",
            "uploadAttachment",
            "requestSubscribeMessage",
            "contactedTemplateId",
            "completedTemplateId",
        ):
            self.assertNotIn(blocked, combined)

        for required in (
            "\u54a8\u8be2\u767b\u8bb0",
            "\u63d0\u4ea4\u54a8\u8be2",
            "\u6211\u7684\u54a8\u8be2\u8bb0\u5f55",
            "\u5fae\u4fe1\u767b\u5f55",
        ):
            self.assertIn(required, combined)

        demand_js = (
            root / "mini-program" / "pages" / "demand" / "index.js"
        ).read_text(encoding="utf-8")
        self.assertNotIn('url: "/demands/improve"', demand_js)

    def test_mini_program_text_is_readable_and_privacy_page_is_registered(self):
        root = Path(__file__).parents[1]
        files = [
            root / "mini-program" / "app.json",
            root / "mini-program" / "pages" / "login" / "index.js",
            root / "mini-program" / "pages" / "login" / "index.wxml",
            root / "mini-program" / "pages" / "demand" / "index.js",
            root / "mini-program" / "pages" / "demand" / "index.wxml",
            root / "mini-program" / "pages" / "privacy" / "index.wxml",
            root / "mini-program" / "pages" / "demands" / "index.wxml",
            root / "mini-program" / "utils" / "api.js",
            root / "mini-program" / "utils" / "config.js",
            root / "docs" / "wechat-mini-program-setup.md",
        ]

        for file in files:
            content = file.read_text(encoding="utf-8")
            for marker in ("\u9407", "\u6f76", "\u7f03", "\u95c4", "\u5bf0", "\u93c7", "\u5d32", "\u9599", "\u95c1", "\u95c2", "????"):
                self.assertNotIn(marker, content, str(file))

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
        self.assertIn("privacy_accepted", source)
        self.assertIn("\u9690\u79c1\u653f\u7b56", wxml)


if __name__ == "__main__":
    unittest.main()
