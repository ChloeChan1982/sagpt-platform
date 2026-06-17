import unittest


class MiniModelTests(unittest.TestCase):
    def test_wechat_settings_and_models_exist(self):
        from app.core.config import Settings
        from app.models.models import MiniSession, MiniSubscriptionGrant, MiniUser

        settings = Settings()
        self.assertTrue(hasattr(settings, "WECHAT_APP_ID"))
        self.assertTrue(hasattr(settings, "WECHAT_APP_SECRET"))
        self.assertEqual(MiniUser.__tablename__, "mini_users")
        self.assertEqual(MiniSession.__tablename__, "mini_sessions")
        self.assertEqual(
            MiniSubscriptionGrant.__tablename__, "mini_subscription_grants"
        )

    def test_mini_schema_migration_adds_demand_columns_to_existing_table(self):
        from sqlalchemy import create_engine, inspect, text
        from app.db.database import ensure_mini_schema

        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE demands (
                        id VARCHAR(36) PRIMARY KEY,
                        target_country VARCHAR(100) NOT NULL,
                        industry VARCHAR(100) NOT NULL,
                        scenario VARCHAR(100) NOT NULL,
                        budget_range VARCHAR(100) NOT NULL,
                        urgency VARCHAR(50) NOT NULL,
                        description TEXT NOT NULL,
                        email VARCHAR(255) NOT NULL
                    )
                    """
                )
            )

        ensure_mini_schema(engine)

        columns = {column["name"] for column in inspect(engine).get_columns("demands")}
        self.assertIn("mini_user_id", columns)
        self.assertIn("client_request_id", columns)


if __name__ == "__main__":
    unittest.main()
