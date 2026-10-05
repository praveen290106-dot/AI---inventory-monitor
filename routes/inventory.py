from flask import Blueprint, request, jsonify, render_template
from models import Product, InventoryTransaction
from services.inventory_service import InventoryService
from routes.auth import login_required

inventory_bp = Blueprint("inventory", __name__)

# ----------------------------------------------------
# HTML Template Views
# ----------------------------------------------------
@inventory_bp.route("/inventory", methods=["GET"])
@login_required
def inventory_page():
    return render_template("inventory.html")

@inventory_bp.route("/inventory/transactions", methods=["GET"])
@login_required
def transactions_page():
    return render_template("transactions.html")

@inventory_bp.route("/alerts", methods=["GET"])
@login_required
def alerts_page():
    return render_template("alerts.html")

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------
@inventory_bp.route("/api/inventory", methods=["GET"])
def get_inventory():
    """List full inventory status including computed stock health states."""
    products = Product.query.order_by(Product.id.asc()).all()
    return jsonify({
        "success": True,
        "count": len(products),
        "inventory": [p.to_dict() for p in products]
    }), 200

@inventory_bp.route("/api/inventory/stock-in", methods=["POST"])
def api_stock_in():
    """
    Record stock addition:
    Payload: { "product_id": int, "quantity": int, "remarks": str }
    """
    data = request.get_json() or {}
    product_id = data.get("product_id")
    remarks = data.get("remarks")

    if not product_id:
        return jsonify({"success": False, "error": "Product ID is required."}), 400

    try:
        quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Quantity must be an integer."}), 400

    try:
        result = InventoryService.stock_in(product_id, quantity, remarks)
        return jsonify({
            "success": True,
            "message": f"Successfully added {quantity} units to stock.",
            "data": result
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

@inventory_bp.route("/api/inventory/stock-out", methods=["POST"])
def api_stock_out():
    """
    Record stock dispatch / consumption:
    Payload: { "product_id": int, "quantity": int, "remarks": str }
    """
    data = request.get_json() or {}
    product_id = data.get("product_id")
    remarks = data.get("remarks")

    if not product_id:
        return jsonify({"success": False, "error": "Product ID is required."}), 400

    try:
        quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Quantity must be an integer."}), 400

    try:
        result = InventoryService.stock_out(product_id, quantity, remarks)
        return jsonify({
            "success": True,
            "message": f"Successfully removed {quantity} units from stock.",
            "data": result
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

@inventory_bp.route("/api/inventory/adjust", methods=["POST"])
def api_adjust():
    """
    Record manual inventory audit adjustment:
    Payload: { "product_id": int, "quantity": int, "remarks": str }
    """
    data = request.get_json() or {}
    product_id = data.get("product_id")
    remarks = data.get("remarks")

    if not product_id:
        return jsonify({"success": False, "error": "Product ID is required."}), 400

    try:
        new_quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Quantity must be an integer."}), 400

    try:
        result = InventoryService.stock_adjust(product_id, new_quantity, remarks)
        return jsonify({
            "success": True,
            "message": "Stock adjusted successfully.",
            "data": result
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

@inventory_bp.route("/api/inventory/low-stock", methods=["GET"])
def get_low_stock():
    """Return all products whose quantity is at or below minimum_stock, but > 0."""
    products = Product.query.all()
    low_stock = [p.to_dict() for p in products if 0 < p.quantity <= p.minimum_stock]
    return jsonify({
        "success": True,
        "count": len(low_stock),
        "products": low_stock
    }), 200

@inventory_bp.route("/api/inventory/out-of-stock", methods=["GET"])
def get_out_of_stock():
    """Return all products whose quantity is exactly 0."""
    products = Product.query.filter_by(quantity=0).all()
    out_of_stock = [p.to_dict() for p in products]
    return jsonify({
        "success": True,
        "count": len(out_of_stock),
        "products": out_of_stock
    }), 200

@inventory_bp.route("/api/inventory/transactions", methods=["GET"])
def get_transactions():
    """
    Return transaction history with optional product_id or transaction_type filters.
    """
    query = InventoryTransaction.query

    product_id = request.args.get("product_id", type=int)
    if product_id:
        query = query.filter_by(product_id=product_id)

    tx_type = request.args.get("type", "").strip().upper()
    if tx_type:
        query = query.filter_by(transaction_type=tx_type)

    limit = request.args.get("limit", default=100, type=int)
    transactions = query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()

    return jsonify({
        "success": True,
        "count": len(transactions),
        "transactions": [t.to_dict() for t in transactions]
    }), 200
