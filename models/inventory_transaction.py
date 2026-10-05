from datetime import datetime, timezone
from models import db

class InventoryTransaction(db.Model):
    """Transaction audit log for all stock-in, stock-out, and adjustment events."""
    __tablename__ = "inventory_transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transaction_type = db.Column(db.String(20), nullable=False, index=True)  # STOCK_IN, STOCK_OUT, ADJUSTMENT
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        """Serialize transaction record with related product name."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else "Unknown Product",
            "category": self.product.category if self.product else "",
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "previous_quantity": self.previous_quantity,
            "new_quantity": self.new_quantity,
            "remarks": self.remarks or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<InventoryTransaction {self.id}: {self.transaction_type} {self.quantity} for Product {self.product_id}>"
