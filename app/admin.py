from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import generate_password_hash

from app.auth import auth_required
from app.db import query_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@auth_required(admin=True)
def dashboard(payload):
    users = query_db(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY created_at DESC"
    )
    return render_template(
        "admin_dashboard.html", user=payload["username"], users=users
    )


@bp.route("/create_user", methods=["POST"])
@auth_required(admin=True)
def create_user():
    username = request.form.get("username")
    password = request.form.get("password")
    is_admin = 1 if request.form.get("is_admin") else 0

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for("admin.dashboard"))

    try:
        password_hash = generate_password_hash(password)
        query_db(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, password_hash, is_admin),
        )
        flash(f"User '{username}' created successfully!")
    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for("admin.dashboard"))


@bp.route("/delete_user/<int:user_id>", methods=["POST"])
@auth_required(admin=True)
def delete_user(payload, user_id):
    current_user = query_db(
        "SELECT id FROM users WHERE username = ?", (payload["username"],), single=True
    )

    if current_user and current_user["id"] == user_id:
        flash("Security alert: You cannot delete your own account.")
        return redirect(url_for("admin.dashboard"))

    try:
        query_db("DELETE FROM users WHERE id = ?", (user_id,))
        flash("User account removed.")
    except Exception as e:
        flash(f"Database error: {str(e)}")

    return redirect(url_for("admin.admin"))
