from flask import Blueprint, jsonify, render_template, redirect, url_for, session
from services.inventory_service import InventoryService
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_page"))
    return redirect(url_for("auth.login_page"))

@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard_page():
    return render_template("dashboard.html")

@dashboard_bp.route("/api/dashboard", methods=["GET"])
def get_dashboard_api():
    """Retrieve all aggregated KPI metrics for the dashboard view."""
    stats = InventoryService.get_dashboard_stats()
    return jsonify({
        "success": True,
        "data": stats
    }), 200
