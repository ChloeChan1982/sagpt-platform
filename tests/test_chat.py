import unittest

from app.core.ai_url import build_chat_completions_url


class ChatConfigurationTests(unittest.TestCase):
    def test_builds_chat_url_from_configured_base_url(self):
        self.assertEqual(
            build_chat_completions_url("https://open.bigmodel.cn/api/paas/v4"),
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        )

    def test_avoids_duplicate_slash(self):
        self.assertEqual(
            build_chat_completions_url("https://open.bigmodel.cn/api/paas/v4/"),
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        )


if __name__ == "__main__":
    unittest.main()
