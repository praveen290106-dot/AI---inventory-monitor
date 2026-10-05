from datetime import datetime, timezone
from models import db

class Product(db.Model):
    """Product model for tracking inventory items, pricing, and stock thresholds."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    minimum_stock = db.Column(db.Integer, nullable=False, default=5)
    supplier = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    transactions = db.relationship(
        "InventoryTransaction",
        backref="product",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="desc(InventoryTransaction.created_at)"
    )
    insights = db.relationship(
        "AIInsight",
        backref="product",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="desc(AIInsight.created_at)"
    )

    @property
    def status(self) -> str:
        """
        Compute stock status according to business rules:
        - OUT_OF_STOCK: quantity == 0
        - LOW_STOCK: quantity <= minimum_stock
        - NORMAL: quantity > minimum_stock
        """
        if self.quantity == 0:
            return "OUT_OF_STOCK"
        elif self.quantity <= self.minimum_stock:
            return "LOW_STOCK"
        else:
            return "NORMAL"

    def to_dict(self) -> dict:
        """Serialize product data including status and inventory valuation."""
        return {
            "id": self.id,
            "product_name": self.product_name,
            "category": self.category,
            "description": self.description or "",
            "price": round(float(self.price), 2),
            "quantity": int(self.quantity),
            "minimum_stock": int(self.minimum_stock),
            "supplier": self.supplier or "",
            "status": self.status,
            "total_value": round(float(self.price) * int(self.quantity), 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Product {self.id}: {self.product_name} (Qty: {self.quantity})>"
