"""
app.py
------
Defence Cyber Shield - AI Powered Military Email Phishing Detection &
Incident Management Portal.

Run with:
    python init_db.py
    python app.py
"""

import os
import json
import secrets
from functools import wraps
from datetime import datetime, timezone

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, abort, jsonify
)
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import models
from phishing_detector import analyze_text
from ocr import extract_text

# ----------------------------------------------------------------------
# App configuration
# ----------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("DCS_SECRET_KEY", secrets.token_hex(32))
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

csrf = CSRFProtect(app)

# Ensure database tables and initial admin seed exist
models.init_db()


# ----------------------------------------------------------------------
# Helpers / decorators
# ----------------------------------------------------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session or "role" not in session:
                flash("Please sign in to continue.", "warning")
                if role == "admin":
                    return redirect(url_for("admin_login"))
                return redirect(url_for("login"))

            if role and session["role"] != role:
                if session["role"] == "soldier" and role == "admin":
                    flash("Access denied. Administrator privileges required.", "danger")
                    return redirect(url_for("admin_login"))
                elif session["role"] == "admin" and role == "soldier":
                    flash("Admin session active. Redirected to Admin Dashboard.", "info")
                    return redirect(url_for("admin_dashboard"))
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now(timezone.utc).year,
        "session_role": session.get("role"),
        "session_name": session.get("name"),
        "admin_exists": models.has_admin(),
    }


# ----------------------------------------------------------------------
# Public pages & Authentication Routes
# ----------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        admin_exists=models.has_admin(),
        registration_open=True,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        army_id_input = request.form.get("army_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not all([name, email, username, password, confirm_password]):
            errors.append("All required fields are required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if army_id_input:
            if models.get_user_by_army_id(army_id_input):
                errors.append("Army ID already registered.")
            army_id = army_id_input
        else:
            army_id = models.generate_unique_army_id()

        if username and models.get_user_by_username(username):
            errors.append("Username already registered.")
        if email and models.get_user_by_email(email):
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        try:
            models.create_soldier(
                name, army_id, email, username, generate_password_hash(password)
            )
        except Exception:
            flash("Registration failed. Email, Username, or Army ID may already be in use.", "danger")
            return render_template("register.html", form=request.form)

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form={})


@app.route("/admin-register", methods=["GET", "POST"])
@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if models.has_admin():
        flash("Administrator account already exists. Please use Admin Login.", "warning")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        army_id_input = request.form.get("army_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not all([name, email, username, password, confirm_password]):
            errors.append("All fields are required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if army_id_input:
            if models.get_user_by_army_id(army_id_input):
                errors.append("Army ID already registered.")
            army_id = army_id_input
        else:
            army_id = f"ADMIN-{secrets.token_hex(4).upper()}"

        if username and models.get_user_by_username(username):
            errors.append("Username already registered.")
        if email and models.get_user_by_email(email):
            errors.append("Email already registered.")

        if models.has_admin():
            flash("Administrator account already exists. Please use Admin Login.", "warning")
            return redirect(url_for("admin_login"))

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin_register.html", form=request.form)

        try:
            models.create_admin(
                name, army_id, email, username, generate_password_hash(password)
            )
        except Exception:
            flash("Admin registration failed. Email, Username, or Army ID may already be in use.", "danger")
            return render_template("admin_register.html", form=request.form)

        flash("Administrator account created successfully. Please sign in.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin_register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and "user_id" in session:
        if session.get("role") == "soldier":
            return redirect(url_for("soldier_dashboard"))
        elif session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = models.get_user_by_login(identifier, role="soldier")
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = "soldier"
            session["name"] = user["name"]
            flash(f"Welcome back, {user['name']}.", "success")
            return redirect(url_for("soldier_dashboard"))
        
        flash("Invalid soldier credentials.", "danger")
        return render_template("login.html", registration_open=True)

    return render_template("login.html", registration_open=True)


@app.route("/admin-login", methods=["GET", "POST"])
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET" and "user_id" in session and session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user = models.get_user_by_username(username, role="admin")
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = "admin"
            session["name"] = user["name"]
            flash("Welcome back, Administrator.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid administrator credentials.", "danger")
        return render_template("admin_login.html")

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Soldier area
# ----------------------------------------------------------------------

@app.route("/soldier/dashboard")
@login_required(role="soldier")
def soldier_dashboard():
    scans = models.get_scans_for_soldier(session["user_id"])
    total = len(scans)
    high = len([s for s in scans if s["risk_level"] == "High"])
    medium = len([s for s in scans if s["risk_level"] == "Medium"])
    low = len([s for s in scans if s["risk_level"] == "Low"])
    return render_template(
        "soldier_dashboard.html",
        total=total, high=high, medium=medium, low=low,
        recent_scans=scans[:5],
    )


@app.route("/soldier/analyze", methods=["POST"])
@login_required(role="soldier")
def soldier_analyze():
    file = request.files.get("screenshot")

    if not file or file.filename == "":
        flash("Please choose a screenshot to upload.", "danger")
        return redirect(url_for("soldier_dashboard"))

    if not allowed_file(file.filename):
        flash("Only PNG, JPG, JPEG, or WEBP images are allowed.", "danger")
        return redirect(url_for("soldier_dashboard"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = secure_filename(f"{session['user_id']}_{secrets.token_hex(8)}.{ext}")
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    file.save(save_path)

    ocr_text = extract_text(save_path)
    result = analyze_text(ocr_text)
    indicators_json = json.dumps(result["indicators"])

    incident_id = None
    if result["level"] == "High":
        incident_id = models.create_incident(
            soldier_id=session["user_id"],
            risk_score=result["score"],
            risk_level=result["level"],
            ocr_text=ocr_text,
            recommendation=result["recommendation"],
            indicators=indicators_json,
            uploaded_image=safe_name,
        )

    scan_id = models.create_scan(
        soldier_id=session["user_id"],
        risk_score=result["score"],
        risk_level=result["level"],
        ocr_text=ocr_text,
        recommendation=result["recommendation"],
        indicators=indicators_json,
        uploaded_image=safe_name,
        incident_id=incident_id,
    )

    return redirect(url_for("scan_result", scan_id=scan_id))


@app.route("/soldier/result/<int:scan_id>")
@login_required(role="soldier")
def scan_result(scan_id):
    scans = models.get_scans_for_soldier(session["user_id"])
    scan = next((s for s in scans if s["id"] == scan_id), None)
    if not scan:
        abort(404)
    indicators = json.loads(scan["indicators"] or "[]")
    return render_template("result.html", scan=scan, indicators=indicators)


@app.route("/soldier/history")
@login_required(role="soldier")
def soldier_history():
    scans = models.get_scans_for_soldier(session["user_id"])
    return render_template("history.html", scans=scans)


@app.route("/soldier/profile")
@login_required(role="soldier")
def soldier_profile():
    user = models.get_user_by_id(session["user_id"])
    scans = models.get_scans_for_soldier(session["user_id"])
    return render_template("profile.html", user=user, total_scans=len(scans))


# ----------------------------------------------------------------------
# Admin area
# ----------------------------------------------------------------------

@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    risk_counts = models.get_risk_counts()
    incident_counts = models.get_incident_counts()
    return render_template(
        "admin_dashboard.html",
        soldiers=models.count_soldiers(),
        uploads=models.total_uploads(),
        risk_counts=risk_counts,
        incident_counts=incident_counts,
        recent_incidents=models.get_all_incidents()[:6],
    )


@app.route("/admin/incidents")
@login_required(role="admin")
def admin_incidents():
    incidents = models.get_all_incidents()
    return render_template("incidents.html", incidents=incidents)


@app.route("/admin/incidents/<int:incident_id>")
@login_required(role="admin")
def admin_incident_detail(incident_id):
    incident = models.get_incident_by_id(incident_id)
    if not incident:
        abort(404)
    indicators = json.loads(incident["indicators"] or "[]")
    return jsonify({
        "id": incident["id"],
        "soldier_name": incident["soldier_name"],
        "soldier_army_id": incident["soldier_army_id"],
        "soldier_email": incident["soldier_email"],
        "risk_score": incident["risk_score"],
        "risk_level": incident["risk_level"],
        "status": incident["status"],
        "ocr_text": incident["ocr_text"],
        "recommendation": incident["recommendation"],
        "indicators": indicators,
        "uploaded_image": url_for("uploaded_file", filename=incident["uploaded_image"]),
        "created_at": incident["created_at"],
    })


@app.route("/admin/incidents/<int:incident_id>/status", methods=["POST"])
@login_required(role="admin")
def admin_incident_status(incident_id):
    status = request.form.get("status")
    if status not in ("Pending", "Open", "Resolved"):
        abort(400)
    models.update_incident_status(incident_id, status)
    flash(f"Incident #{incident_id} marked as {status}.", "success")
    return redirect(url_for("admin_incidents"))


@app.route("/admin/incidents/<int:incident_id>/delete", methods=["POST"])
@login_required(role="admin")
def admin_incident_delete(incident_id):
    models.delete_incident(incident_id)
    flash(f"Incident #{incident_id} deleted.", "info")
    return redirect(url_for("admin_incidents"))


@app.route("/admin/users")
@login_required(role="admin")
def admin_users():
    soldiers = models.get_all_soldiers()
    return render_template("users.html", soldiers=soldiers)


@app.route("/admin/analytics")
@login_required(role="admin")
def admin_analytics():
    risk_counts = models.get_risk_counts()
    incident_counts = models.get_incident_counts()
    monthly_trend = models.get_monthly_trend()
    top_threats = models.get_top_threat_categories()
    chart_payload = {
        "risk_counts": risk_counts,
        "incident_counts": incident_counts,
        "monthly_trend": monthly_trend,
        "top_threats": top_threats,
    }
    return render_template(
        "analytics.html",
        risk_counts=risk_counts,
        incident_counts=incident_counts,
        monthly_trend=monthly_trend,
        top_threats=top_threats,
        chart_payload=json.dumps(chart_payload),
    )


@app.route("/admin/reports")
@login_required(role="admin")
def admin_reports():
    scans = models.get_all_scans()
    return render_template("reports.html", scans=scans)


# ----------------------------------------------------------------------
# Secure file serving (uploaded screenshots)
# ----------------------------------------------------------------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    if "user_id" not in session:
        abort(403)

    filename = secure_filename(filename)

    if session["role"] == "admin":
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Soldiers may only view their own screenshots (filename is prefixed
    # with their user id at upload time).
    if filename.startswith(f"{session['user_id']}_"):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    abort(403)


# ----------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="Access denied."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(413)
def too_large(e):
    return render_template("error.html", code=413, message="File too large (max 8 MB)."), 413


if __name__ == "__main__":
    app.run(debug=os.environ.get("DCS_DEBUG", "1") == "1", host="0.0.0.0", port=5000)


