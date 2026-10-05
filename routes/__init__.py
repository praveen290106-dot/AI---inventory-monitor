from routes.auth import auth_bp
from routes.products import products_bp
from routes.inventory import inventory_bp
from routes.dashboard import dashboard_bp
from routes.ai import ai_bp

__all__ = ["auth_bp", "products_bp", "inventory_bp", "dashboard_bp", "ai_bp"]
