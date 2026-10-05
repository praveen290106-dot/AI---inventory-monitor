from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from models import db, User

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    """Decorator to protect view routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # If API endpoint, return JSON error
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Authentication required"}), 401
            # If page view, redirect to login
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------------------------------
# HTML Template Views
# ----------------------------------------------------
@auth_bp.route("/login", methods=["GET"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_page"))
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET"])
def register_page():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_page"))
    return render_template("register.html")

@auth_bp.route("/logout", methods=["GET"])
def logout_view():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login_page"))

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------
@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "admin").strip()

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "error": "Username, email, and password are required."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "error": "Password must be at least 6 characters long."
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "success": False,
            "error": f"Username '{username}' is already taken."
        }), 409

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "error": f"Email '{email}' is already registered."
        }), 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Automatically log the newly registered user in
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "success": True,
        "message": "User registered and logged in successfully.",
        "user": user.to_dict()
    }), 201

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    login_id = data.get("username", "").strip()
    password = data.get("password", "")

    if not login_id or not password:
        return jsonify({
            "success": False,
            "error": "Username/email and password are required."
        }), 400

    # Allow login by either username or email
    user = User.query.filter(
        (User.username == login_id) | (User.email == login_id.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "error": "Invalid username or password"
        }), 401

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict()
    }), 200

@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200
