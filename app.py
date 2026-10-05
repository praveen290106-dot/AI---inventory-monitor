import os
import sys
import base64
import mimetypes
import uuid
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

from config import Config, BASE_DIR
from models import db
from routes import auth_bp, products_bp, inventory_bp, dashboard_bp, ai_bp
from services.foundry_service import MicrosoftFoundryService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger("ai_inventory_monitor")

def create_app() -> Flask:
    """Application factory for AI-Powered Inventory Monitor with full Foundry & Azure AI capabilities."""
    load_dotenv(BASE_DIR / ".env")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Ensure uploads and database directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(BASE_DIR / "database", exist_ok=True)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize SQLAlchemy database
    db.init_app(app)

    # ========================================================
    # Microsoft Foundry AI Client Initialization
    # ========================================================
    AOAI_ENDPOINT = Config.AOAI_ENDPOINT
    AOAI_KEY = Config.AOAI_KEY
    TEXT_MODEL = Config.TEXT_MODEL
    VISION_MODEL = Config.VISION_MODEL

    def get_client() -> OpenAI:
        """Create or return OpenAI client configured for Azure OpenAI / Foundry."""
        if not AOAI_ENDPOINT or not AOAI_KEY:
            raise RuntimeError("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")
        endpoint = AOAI_ENDPOINT.removesuffix("/openai/v1").rstrip("/")
        return OpenAI(api_key=AOAI_KEY, base_url=f"{endpoint}/openai/v1/")

    def text_response(prompt: str, system: str = "You are a helpful AI assistant.") -> str:
        """Generate text completions using responses.create or chat.completions fallback."""
        c = get_client()
        try:
            r = c.responses.create(model=TEXT_MODEL, instructions=system, input=prompt)
            return r.output_text
        except Exception:
            # Fallback to chat completions if responses endpoint has variation
            r = c.chat.completions.create(
                model=TEXT_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            )
            return r.choices[0].message.content

    # Initialize Microsoft Foundry Service instance for blueprints
    foundry_service = MicrosoftFoundryService(
        endpoint=AOAI_ENDPOINT,
        api_key=AOAI_KEY,
        deployment_name=TEXT_MODEL,
        api_version=Config.FOUNDRY_API_VERSION
    )
    app.foundry_service = foundry_service

    # Validate Microsoft Foundry configuration at startup
    is_valid, validation_error = foundry_service.validate_configuration()
    if is_valid:
        logger.info(f"[OK] Microsoft Foundry configured successfully (Deployment: {TEXT_MODEL})")
    else:
        logger.warning(f"WARNING: Microsoft Foundry configuration is incomplete: {validation_error}")

    # ========================================================
    # Register Core Blueprints
    # ========================================================
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)

    # ========================================================
    # Multimodal & AI Routes (from sample specification)
    # ========================================================
    @app.get("/home")
    def home_view():
        return render_template("home.html")

    @app.get("/chat")
    def chat_view():
        return render_template("chat.html")

    @app.post("/api/chat")
    def api_chat_endpoint():
        try:
            p = (request.json or {}).get("message", "").strip()
            if not p:
                return jsonify(error="Enter a message."), 400
            return jsonify(reply=text_response(p))
        except Exception as e:
            logger.error(f"api_chat error: {e}")
            return jsonify(error=str(e)), 500

    @app.get("/text-analysis")
    def text_analysis_view():
        return render_template("text_analysis.html")

    @app.post("/api/text-analysis")
    def api_text_analysis_endpoint():
        try:
            text = (request.json or {}).get("text", "").strip()
            if not text:
                return jsonify(error="Enter text."), 400
            prompt = f"""Analyze the following text and return exactly these sections:
1. Sentiment
2. Keywords
3. Entities (organization, person, location, date, product where applicable)
4. Summary

TEXT:
{text}"""
            return jsonify(result=text_response(prompt))
        except Exception as e:
            logger.error(f"api_text_analysis error: {e}")
            return jsonify(error=str(e)), 500

    @app.get("/vision")
    def vision_view():
        return render_template("vision.html")

    @app.post("/api/vision")
    def api_vision_endpoint():
        try:
            f = request.files.get("image")
            prompt = request.form.get("prompt", "Describe this image in detail.").strip()
            if not f:
                return jsonify(error="Upload an image."), 400
            data = base64.b64encode(f.read()).decode()
            mime = f.mimetype or "image/jpeg"
            c = get_client()
            r = c.responses.create(
                model=VISION_MODEL,
                input=[{"role": "user", "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:{mime};base64,{data}"}
                ]}]
            )
            return jsonify(result=r.output_text)
        except Exception as e:
            logger.error(f"api_vision error: {e}")
            return jsonify(error=str(e)), 500

    @app.get("/uploads/<name>")
    def uploads_view(name):
        return send_file(os.path.join(app.config["UPLOAD_FOLDER"], name))

    # Unified Health Endpoints (satisfies both /health and /api/health)
    @app.get("/health")
    def health_view():
        return jsonify(
            text_model=bool(TEXT_MODEL),
            vision_model=bool(VISION_MODEL),
            status="ok"
        )

    @app.get("/api/health")
    def api_health_view():
        is_configured, _ = app.foundry_service.validate_configuration()
        return jsonify({
            "status": "ok",
            "service": "AI Inventory Monitor",
            "microsoft_foundry_configured": is_configured,
            "deployment": TEXT_MODEL,
            "text_model": bool(TEXT_MODEL),
            "vision_model": bool(VISION_MODEL)
        }), 200

    # Ensure tables are created
    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    port = app.config.get("PORT", 10000)
    debug = app.config.get("DEBUG", False)
    logger.info(f"Starting AI Inventory Monitor on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
