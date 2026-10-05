from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from models import db, Product, InventoryTransaction
from routes.auth import login_required

products_bp = Blueprint("products", __name__)

# ----------------------------------------------------
# HTML Template Views
# ----------------------------------------------------
@products_bp.route("/products", methods=["GET"])
@login_required
def products_page():
    return render_template("products.html")

@products_bp.route("/products/add", methods=["GET"])
@login_required
def add_product_page():
    return render_template("add_product.html")

@products_bp.route("/products/edit/<int:product_id>", methods=["GET"])
@login_required
def edit_product_page(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("products.products_page"))
    return render_template("edit_product.html", product=product)

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------
@products_bp.route("/api/products", methods=["GET"])
def get_products():
    """
    List products with optional search query and category filtering.
    Query params:
    - search: string filter on product_name or description
    - category: string filter on category
    - status: OUT_OF_STOCK | LOW_STOCK | NORMAL
    """
    query = Product.query

    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            (Product.product_name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%")) |
            (Product.supplier.ilike(f"%{search}%"))
        )

    category = request.args.get("category", "").strip()
    if category:
        query = query.filter(Product.category.ilike(category))

    products = query.order_by(Product.id.asc()).all()

    status_filter = request.args.get("status", "").strip().upper()
    if status_filter:
        products = [p for p in products if p.status == status_filter]

    # Distinct categories for frontend dropdown
    all_categories = sorted(list({p.category for p in Product.query.all() if p.category}))

    return jsonify({
        "success": True,
        "count": len(products),
        "categories": all_categories,
        "products": [p.to_dict() for p in products]
    }), 200

@products_bp.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Retrieve single product details."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    return jsonify({
        "success": True,
        "product": product.to_dict()
    }), 200

@products_bp.route("/api/products", methods=["POST"])
def create_product():
    """Create a new product with input validation and initial stock tracking."""
    data = request.get_json() or {}

    product_name = data.get("product_name", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    supplier = data.get("supplier", "").strip()

    # Required field validation
    if not product_name:
        return jsonify({"success": False, "error": "Product Name is required."}), 400
    if not category:
        return jsonify({"success": False, "error": "Category is required."}), 400

    # Numeric validation
    try:
        price = float(data.get("price", 0.0))
        quantity = int(data.get("quantity", 0))
        minimum_stock = int(data.get("minimum_stock", 5))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Price, quantity, and minimum stock must be valid numbers."}), 400

    if price < 0:
        return jsonify({"success": False, "error": "Price cannot be negative."}), 400
    if quantity < 0:
        return jsonify({"success": False, "error": "Quantity cannot be negative."}), 400
    if minimum_stock < 0:
        return jsonify({"success": False, "error": "Minimum stock cannot be negative."}), 400

    product = Product(
        product_name=product_name,
        category=category,
        description=description,
        price=price,
        quantity=quantity,
        minimum_stock=minimum_stock,
        supplier=supplier
    )

    db.session.add(product)
    db.session.flush()  # assign product.id

    # If initial quantity > 0, log an initial STOCK_IN transaction
    if quantity > 0:
        tx = InventoryTransaction(
            product_id=product.id,
            transaction_type="STOCK_IN",
            quantity=quantity,
            previous_quantity=0,
            new_quantity=quantity,
            remarks="Initial inventory stock upon product creation"
        )
        db.session.add(tx)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Product '{product.product_name}' created successfully.",
        "product": product.to_dict()
    }), 201

@products_bp.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id: int):
    """Update product information with quantity difference adjustment audit."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    data = request.get_json() or {}

    if "product_name" in data:
        name = data["product_name"].strip()
        if not name:
            return jsonify({"success": False, "error": "Product name cannot be empty."}), 400
        product.product_name = name

    if "category" in data:
        cat = data["category"].strip()
        if not cat:
            return jsonify({"success": False, "error": "Category cannot be empty."}), 400
        product.category = cat

    if "description" in data:
        product.description = data["description"].strip()

    if "supplier" in data:
        product.supplier = data["supplier"].strip()

    if "price" in data:
        try:
            val = float(data["price"])
            if val < 0:
                return jsonify({"success": False, "error": "Price cannot be negative."}), 400
            product.price = val
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid price value."}), 400

    if "minimum_stock" in data:
        try:
            val = int(data["minimum_stock"])
            if val < 0:
                return jsonify({"success": False, "error": "Minimum stock cannot be negative."}), 400
            product.minimum_stock = val
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid minimum stock value."}), 400

    # If quantity is directly updated in product edit, record an ADJUSTMENT transaction
    if "quantity" in data:
        try:
            new_qty = int(data["quantity"])
            if new_qty < 0:
                return jsonify({"success": False, "error": "Quantity cannot be negative."}), 400
            old_qty = product.quantity
            if new_qty != old_qty:
                product.quantity = new_qty
                diff = new_qty - old_qty
                tx = InventoryTransaction(
                    product_id=product.id,
                    transaction_type="ADJUSTMENT",
                    quantity=abs(diff),
                    previous_quantity=old_qty,
                    new_quantity=new_qty,
                    remarks=f"Product edit adjustment ({'+' if diff > 0 else ''}{diff})"
                )
                db.session.add(tx)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid quantity value."}), 400

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Product '{product.product_name}' updated successfully.",
        "product": product.to_dict()
    }), 200

@products_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id: int):
    """Delete product and cascade related transactions and insights."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    name = product.product_name
    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Product '{name}' deleted successfully."
    }), 200
