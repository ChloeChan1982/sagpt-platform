import unittest
from pathlib import Path


MAIN_SOURCE = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")


class ErrorContractTests(unittest.TestCase):
    def test_http_errors_include_frontend_message(self):
        self.assertIn("@app.exception_handler(HTTPException)", MAIN_SOURCE)
        self.assertIn('"message": detail', MAIN_SOURCE)

    def test_validation_errors_include_message_without_echoing_input(self):
        self.assertIn("@app.exception_handler(RequestValidationError)", MAIN_SOURCE)
        self.assertIn('"message": errors[0]["msg"]', MAIN_SOURCE)
        self.assertIn('"loc": error["loc"]', MAIN_SOURCE)
        self.assertNotIn('"input": error["input"]', MAIN_SOURCE)

    def test_global_errors_include_frontend_message(self):
        self.assertIn(
            'content={"detail": "Internal server error", "message": "Internal server error"}',
            MAIN_SOURCE,
        )


if __name__ == "__main__":
    unittest.main()
