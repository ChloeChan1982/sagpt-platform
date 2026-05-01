"""Initialize database tables on first startup. Run automatically by Dockerfile.render."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db

if __name__ == "__main__":
    print("[INIT] Creating database tables...")
    init_db()
    print("[INIT] Done.")
