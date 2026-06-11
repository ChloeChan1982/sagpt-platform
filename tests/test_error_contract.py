import unittest
from pathlib import Path


MAIN_SOURCE = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")


class ErrorContractTests(unittest.TestCase):
    def test_http_errors_include_frontend_message(self):
        self.assertIn("@app.exception_handler(HTTPException)", MAIN_SOURCE)
        self.assertIn('"message": detail', MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
