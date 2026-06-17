import unittest

from app.core.config import Settings


class MiniFileTests(unittest.TestCase):
    def test_accepts_supported_file(self):
        from app.core.mini_files import validate_attachment

        validate_attachment("brief.pdf", "application/pdf", 1024)

    def test_rejects_unsupported_or_oversized_file(self):
        from app.core.mini_files import validate_attachment

        with self.assertRaises(ValueError):
            validate_attachment("payload.exe", "application/octet-stream", 1024)
        with self.assertRaises(ValueError):
            validate_attachment(
                "large.pdf",
                "application/pdf",
                Settings().MAX_ATTACHMENT_BYTES + 1,
            )


if __name__ == "__main__":
    unittest.main()
