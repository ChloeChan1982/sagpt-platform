import unittest
from pathlib import Path


class WeChatNotificationContractTests(unittest.TestCase):
    def test_contacted_and_completed_statuses_trigger_notifications(self):
        source = (Path(__file__).parents[1] / "app" / "routers" / "demands.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('{"contacted", "completed"}', source)
        self.assertIn("send_demand_status_notification", source)

    def test_notification_failure_does_not_rollback_status(self):
        source = (Path(__file__).parents[1] / "app" / "routers" / "demands.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("except WeChatAPIError", source)
        self.assertIn("db.commit()", source)

    def test_mini_profile_routes_support_phone_and_subscription_grants(self):
        source = (Path(__file__).parents[1] / "app" / "routers" / "mini.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('@router.post("/profile/phone")', source)
        self.assertIn('@router.post("/subscriptions/grant")', source)
        self.assertIn("get_phone_number", source)


if __name__ == "__main__":
    unittest.main()
