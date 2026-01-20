import os
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import render_template, request, make_response, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash

from .setup import query_db, app

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
app.config['JWT_SECRET'] = os.getenv("JWT_SECRET")
app.secret_key = app.config['JWT_SECRET']

def auth_required(*, admin=False):
    """
    If admin=True, it checks for the 'admin' role in the JWT payload.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get('access_token')
            
            if not token:
                return redirect(url_for('login_get'))
            
            try:
                # Verify signature and expiration
                data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
                
                # Role check logic
                if admin and data.get('role') != 'admin':
                    flash("Access denied: Admins only.")
                    return redirect(url_for('login_get'))
                
                # Pass payload to the route
                return f(data, *args, **kwargs)
            except Exception:
                # Catches expired tokens or invalid signatures
                return redirect(url_for('login_get'))
        return decorated
    return decorator

# --- AUTHENTICATION ROUTES ---

@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")
    
    user = query_db("SELECT * FROM users WHERE username = ?", (username,), single=True)

    if user and check_password_hash(user["password_hash"], password):
        user_role = "admin" if user["is_admin"] == 1 else "user"
        
        payload = {
            'username': username,
            'role': user_role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=2)
        }
        token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
        
        # Determine where to send the user
        target = "admin_dashboard" if user_role == "admin" else "hello"
        response = make_response(redirect(url_for(target)))
        response.set_cookie('access_token', token, httponly=True, samesite='Lax')
        return response
    
    flash("Invalid username or password")
    return redirect(url_for('login_get'))

@app.route("/admin")
@auth_required(admin=True)
def admin_dashboard(payload):
    return render_template("admin_dashboard.html", user=payload['username'])

@app.route("/hello")
@auth_required(admin=False)
def hello(payload):
    return f"Hello, {payload['username']}!"

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("login_get")))
    response.delete_cookie('access_token') 
    flash("You have been logged out.")
    return response