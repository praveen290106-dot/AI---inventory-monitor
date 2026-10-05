from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.product import Product
from models.inventory_transaction import InventoryTransaction
from models.ai_insight import AIInsight

__all__ = ["db", "User", "Product", "InventoryTransaction", "AIInsight"]
