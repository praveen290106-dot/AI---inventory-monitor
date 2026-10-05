from datetime import datetime, timezone
from models import db

class AIInsight(db.Model):
    """Storage for AI-generated inventory insights, restocking recommendations, and risk warnings."""
    __tablename__ = "ai_insights"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    insight_type = db.Column(db.String(50), nullable=False, index=True)  # RESTOCK_RECOMMENDATION, RISK_ALERT, SUMMARY_ANALYSIS
    recommendation = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        """Serialize insight data."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else "All Products / General Inventory",
            "category": self.product.category if self.product else "General",
            "insight_type": self.insight_type,
            "recommendation": self.recommendation,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<AIInsight {self.id}: [{self.priority}] {self.insight_type}>"
