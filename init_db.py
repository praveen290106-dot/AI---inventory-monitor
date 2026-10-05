import os
import sys
from app import create_app
from models import db
from config import Config

def init_database():
    """Initializes the SQLite database and creates all required tables."""
    print("=" * 60)
    print(" Initializing AI-Powered Inventory Monitor Database")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # Ensure database directory exists
        db_path = Config.DATABASE_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        print(f"Creating tables at: {db_path}...")
        db.create_all()
        print("[OK] Tables created successfully:")
        print("  - users")
        print("  - products")
        print("  - inventory_transactions")
        print("  - ai_insights")
    print("=" * 60)
    print(" Database initialization complete! Run 'python seed_data.py' to populate sample records.")
    print("=" * 60)

if __name__ == "__main__":
    init_database()
