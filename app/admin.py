import os
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import render_template, request, make_response, redirect, url_for, flash
from werkzeug.security import check_password_hash
from flask import Blueprint, render_template, request, make_response, redirect, url_for, flash, current_app
from app import app, query_db

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'secret.env'))

app.secret_key = app.config['JWT_SECRET']
auth_bp = Blueprint('auth_bp', __name__)
# --- JWT DECORATORS ---

def auth_required(f):
    """Ensures a valid JWT is present."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return redirect(url_for('login'))
        try:
            # Verify signature and expiration
            data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            return f(data, *args, **kwargs) # Pass payload to the route
        except Exception:
            return redirect(url_for('login'))
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            flash("Unauthorized. Please log in.")
            return redirect(url_for('auth_bp.login')) # Note the blueprint name prefix
        try:
            # Use current_app.config instead of app.config to avoid circular import
            data = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            if data.get('role') != 'admin':
                flash("Access denied: Admins only.")
                return redirect(url_for('hello'))
            return f(data, *args, **kwargs)
        except Exception:
            return redirect(url_for('auth_bp.login'))
    return decorated

# --- AUTHENTICATION ROUTES ---

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), single=True)

        if user and check_password_hash(user["password_hash"], password):
            # Map DB integer (1/0) to a string role for the JWT
            user_role = "admin" if user["is_admin"] == 1 else "user"
            
            payload = {
                'username': username,
                'role': user_role, # Included for stateless auth
                'exp': datetime.now(timezone.utc) + timedelta(hours=2)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
            
            target = "admin_dashboard" if user_role == "admin" else "hello"
            response = make_response(redirect(url_for(target)))
            response.set_cookie('access_token', token, httponly=True, samesite='Lax')
            return response
        
        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/admin")
@admin_required
def admin_dashboard(payload):
    # payload['username'] comes directly from the JWT
    return render_template("admin_dashboard.html", user=payload['username'])

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("login")))
    response.set_cookie('access_token', '', expires=0)
    flash("You have been logged out.")
    return response