from pathlib import Path
from flask import (
    Blueprint,
    current_app,
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
def dashboard(user_id: int):
    current_user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), single=True)
    users = query_db(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY created_at DESC"
    )
    return render_template(
        "admin_dashboard.html", user=current_user["username"], users=users
    )


@bp.route("/create_user", methods=["POST"])
@auth_required(admin=True)
def create_user(current_user_id: int):
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
def delete_user(current_user_id: int, user_id: int):
    if current_user_id == user_id:
        flash("Security alert: You cannot delete your own account.")
        return redirect(url_for("admin.dashboard"))

    try:
        files = query_db("SELECT file_path FROM files WHERE user_id = ?", (user_id,))
        query_db("DELETE FROM users WHERE id = ?", (user_id,))

        for file in files:
            full_path: Path = Path(current_app.config["FILE_STORE"]) / file["file_path"]
            full_path.unlink(missing_ok=True)
        
        
        flash("User account removed.")
    except Exception as e:
        
        flash(f"Error: {str(e)}")
        
    return redirect(url_for("admin.dashboard"))