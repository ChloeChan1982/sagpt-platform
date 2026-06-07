import unittest
from pathlib import Path


class ProductionSecurityTests(unittest.TestCase):
    def test_debug_route_is_not_exposed(self):
        main_source = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")

        self.assertNotIn('@app.get("/debug")', main_source)


if __name__ == "__main__":
    unittest.main()
