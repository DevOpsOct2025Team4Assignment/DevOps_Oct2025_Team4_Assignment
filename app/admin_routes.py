from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
# Import the decorator from your admin module
from app.admin import admin_required 

# Define the blueprint
admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/admin")
@admin_required
def admin_dashboard(payload):
    # Use a 'lazy import' inside the function to avoid circularity with query_db
    from app import query_db
    users = query_db("SELECT id, username, is_admin, created_at FROM users ORDER BY created_at DESC")
    return render_template("admin_dashboard.html", user=payload['username'], users=users)

@admin_bp.route("/admin/create_user", methods=["POST"])
@admin_required
def create_user(payload):
    from app import query_db
    username = request.form.get("username")
    password = request.form.get("password")
    is_admin = 1 if request.form.get("is_admin") else 0

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for('admin_bp.admin_dashboard'))

    try:
        password_hash = generate_password_hash(password)
        query_db("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", 
                 (username, password_hash, is_admin))
        flash(f"User '{username}' created successfully!")
    except Exception as e:
        flash(f"Error: {str(e)}")
    
    return redirect(url_for('admin_bp.admin_dashboard'))

@admin_bp.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(payload, user_id):
    from app import query_db
    current_user = query_db("SELECT id FROM users WHERE username = ?", (payload['username'],), single=True)
    
    if current_user and current_user['id'] == user_id:
        flash("Security alert: You cannot delete your own account.")
        return redirect(url_for('admin_bp.admin_dashboard'))

    try:
        query_db("DELETE FROM users WHERE id = ?", (user_id,))
        flash("User account removed.")
    except Exception as e:
        flash(f"Database error: {str(e)}")
        
    return redirect(url_for('admin_bp.admin_dashboard'))