from typing import Dict, Any, List, Optional
from models import db, Product, InventoryTransaction, AIInsight

class InventoryService:
    """Centralized service managing inventory calculations, transaction logging, and state queries."""

    @staticmethod
    def get_status(quantity: int, minimum_stock: int) -> str:
        """Centralized status evaluator."""
        if quantity == 0:
            return "OUT_OF_STOCK"
        elif quantity <= minimum_stock:
            return "LOW_STOCK"
        return "NORMAL"

    @staticmethod
    def stock_in(product_id: int, quantity: int, remarks: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a stock-in event:
        new_quantity = old_quantity + quantity
        """
        if quantity <= 0:
            raise ValueError("Stock-in quantity must be greater than zero.")

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found.")

        old_quantity = product.quantity
        new_quantity = old_quantity + quantity
        product.quantity = new_quantity

        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type="STOCK_IN",
            quantity=quantity,
            previous_quantity=old_quantity,
            new_quantity=new_quantity,
            remarks=remarks or f"Restocked {quantity} units"
        )

        db.session.add(transaction)
        db.session.commit()

        return {
            "product": product.to_dict(),
            "transaction": transaction.to_dict()
        }

    @staticmethod
    def stock_out(product_id: int, quantity: int, remarks: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a stock-out event:
        new_quantity = old_quantity - quantity
        Enforces: stock-out cannot exceed available quantity, no negative inventory.
        """
        if quantity <= 0:
            raise ValueError("Stock-out quantity must be greater than zero.")

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found.")

        if quantity > product.quantity:
            raise ValueError(
                f"Insufficient stock for '{product.product_name}'. "
                f"Available: {product.quantity}, Requested: {quantity}."
            )

        old_quantity = product.quantity
        new_quantity = old_quantity - quantity

        if new_quantity < 0:
            raise ValueError("Inventory cannot be negative.")

        product.quantity = new_quantity

        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type="STOCK_OUT",
            quantity=quantity,
            previous_quantity=old_quantity,
            new_quantity=new_quantity,
            remarks=remarks or f"Dispatched {quantity} units"
        )

        db.session.add(transaction)
        db.session.commit()

        return {
            "product": product.to_dict(),
            "transaction": transaction.to_dict()
        }

    @staticmethod
    def stock_adjust(product_id: int, new_quantity: int, remarks: Optional[str] = None) -> Dict[str, Any]:
        """
        Record an inventory manual audit adjustment.
        """
        if new_quantity < 0:
            raise ValueError("Adjusted quantity cannot be negative.")

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found.")

        old_quantity = product.quantity
        diff = new_quantity - old_quantity

        if diff == 0:
            return {
                "product": product.to_dict(),
                "transaction": None,
                "message": "Quantity unchanged."
            }

        product.quantity = new_quantity

        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type="ADJUSTMENT",
            quantity=abs(diff),
            previous_quantity=old_quantity,
            new_quantity=new_quantity,
            remarks=remarks or f"Manual count adjustment ({'+' if diff > 0 else ''}{diff})"
        )

        db.session.add(transaction)
        db.session.commit()

        return {
            "product": product.to_dict(),
            "transaction": transaction.to_dict()
        }

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Aggregate high-level metrics for dashboard cards and charts."""
        products = Product.query.all()
        
        total_products = len(products)
        total_units = sum(p.quantity for p in products)
        total_value = round(sum(p.quantity * p.price for p in products), 2)

        out_of_stock_list = [p.to_dict() for p in products if p.quantity == 0]
        low_stock_list = [p.to_dict() for p in products if 0 < p.quantity <= p.minimum_stock]
        normal_stock_list = [p.to_dict() for p in products if p.quantity > p.minimum_stock]

        # Category breakdown
        category_counts = {}
        category_values = {}
        for p in products:
            category_counts[p.category] = category_counts.get(p.category, 0) + p.quantity
            category_values[p.category] = round(
                category_values.get(p.category, 0.0) + (p.quantity * p.price), 2
            )

        # Recent 10 transactions
        recent_transactions = [
            t.to_dict()
            for t in InventoryTransaction.query.order_by(
                InventoryTransaction.created_at.desc()
            ).limit(10).all()
        ]

        # Recent 5 AI insights
        recent_insights = [
            i.to_dict()
            for i in AIInsight.query.order_by(
                AIInsight.created_at.desc()
            ).limit(5).all()
        ]

        return {
            "total_products": total_products,
            "total_units": total_units,
            "total_value": total_value,
            "out_of_stock_count": len(out_of_stock_list),
            "low_stock_count": len(low_stock_list),
            "normal_stock_count": len(normal_stock_list),
            "out_of_stock_products": out_of_stock_list,
            "low_stock_products": low_stock_list,
            "category_distribution": category_counts,
            "category_valuation": category_values,
            "recent_transactions": recent_transactions,
            "recent_insights": recent_insights
        }

    @staticmethod
    def get_ai_context() -> Dict[str, Any]:
        """
        Extract compact and relevant inventory data for the Microsoft Foundry AI agent.
        Includes product levels, categories, low stock, out of stock, and recent stock-outs.
        """
        products = Product.query.all()
        
        low_stock = []
        out_of_stock = []
        healthy_stock = []
        all_items = []

        for p in products:
            item_info = {
                "id": p.id,
                "name": p.product_name,
                "category": p.category,
                "price": round(p.price, 2),
                "current_stock": p.quantity,
                "min_stock": p.minimum_stock,
                "supplier": p.supplier or "N/A",
                "status": p.status
            }
            all_items.append(item_info)
            if p.status == "OUT_OF_STOCK":
                out_of_stock.append(item_info)
            elif p.status == "LOW_STOCK":
                low_stock.append(item_info)
            else:
                healthy_stock.append(item_info)

        # Recent stock-outs or large deductions (velocity indicator)
        recent_stock_outs = [
            t.to_dict()
            for t in InventoryTransaction.query.filter_by(transaction_type="STOCK_OUT")
            .order_by(InventoryTransaction.created_at.desc())
            .limit(10).all()
        ]

        return {
            "total_catalog_products": len(products),
            "total_units_in_stock": sum(p.quantity for p in products),
            "total_inventory_value": round(sum(p.quantity * p.price for p in products), 2),
            "out_of_stock_items": out_of_stock,
            "low_stock_items": low_stock,
            "healthy_items_count": len(healthy_stock),
            "all_products": all_items,
            "recent_stock_outs": recent_stock_outs
        }
