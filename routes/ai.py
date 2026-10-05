from flask import Blueprint, request, jsonify, render_template, current_app
from models import AIInsight
from services.inventory_service import InventoryService
from services.foundry_service import MicrosoftFoundryService
from routes.auth import login_required

ai_bp = Blueprint("ai", __name__)

def get_foundry_service() -> MicrosoftFoundryService:
    """Retrieve or instantiate the Microsoft Foundry AI service from app config."""
    return current_app.foundry_service

# ----------------------------------------------------
# HTML Template Views
# ----------------------------------------------------
@ai_bp.route("/ai-assistant", methods=["GET"])
@login_required
def ai_assistant_page():
    return render_template("ai_assistant.html")

@ai_bp.route("/ai-insights", methods=["GET"])
@login_required
def ai_insights_page():
    return render_template("ai_insights.html")

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------
@ai_bp.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    """
    POST /api/ai/chat
    Request payload: { "message": "Which products need immediate restocking?" }
    Collects live inventory data from SQLite and sends to Microsoft Foundry AI agent.
    """
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "The 'message' field is required."
        }), 400

    # Automatically extract inventory context from SQLite
    inventory_context = InventoryService.get_ai_context()

    # Invoke Microsoft Foundry
    service = get_foundry_service()
    result = service.chat(message, inventory_context)

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code

@ai_bp.route("/api/ai/analyze", methods=["POST"])
def api_ai_analyze():
    """
    POST /api/ai/analyze
    Runs an end-to-end diagnostic analysis on the database inventory and records insights.
    """
    inventory_context = InventoryService.get_ai_context()
    service = get_foundry_service()
    result = service.analyze_inventory(inventory_context)

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code

@ai_bp.route("/api/ai/recommend", methods=["POST"])
def api_ai_recommend():
    """
    POST /api/ai/recommend
    Generates intelligent restocking recommendations with urgency levels and reorder quantities.
    """
    inventory_context = InventoryService.get_ai_context()
    service = get_foundry_service()
    result = service.recommend_restock(inventory_context)

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code

@ai_bp.route("/api/ai/inventory-summary", methods=["GET"])
def api_ai_summary():
    """
    GET /api/ai/inventory-summary
    Fetches an AI-synthesized executive summary of current inventory health.
    """
    inventory_context = InventoryService.get_ai_context()
    service = get_foundry_service()
    result = service.get_inventory_summary(inventory_context)

    status_code = 200 if result.get("success") else 503
    return jsonify(result), status_code

@ai_bp.route("/api/ai/insights", methods=["GET"])
def api_get_insights():
    """
    GET /api/ai/insights
    Retrieves stored AI recommendations and alerts from SQLite.
    Optional query param: ?priority=HIGH|MEDIUM|LOW
    """
    query = AIInsight.query
    priority = request.args.get("priority", "").strip().upper()
    if priority:
        query = query.filter_by(priority=priority)

    insights = query.order_by(AIInsight.created_at.desc()).limit(50).all()

    return jsonify({
        "success": True,
        "count": len(insights),
        "insights": [i.to_dict() for i in insights]
    }), 200
