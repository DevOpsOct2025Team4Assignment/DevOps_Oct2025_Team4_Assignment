import os
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import render_template, request, make_response, redirect, url_for, flash
from werkzeug.security import check_password_hash

# Import 'app' and 'query_db' from your package (__init__.py)
from app import app, query_db

# Load JWT_SECRET from secret.env (located one level up from /app)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'secret.env'))
app.config['JWT_SECRET'] = os.getenv("JWT_SECRET")
app.secret_key = app.config['JWT_SECRET']

# --- JWT DECORATOR FOR ROLE ENFORCEMENT ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        
        if not token:
            flash("Unauthorized. Please log in.")
            return redirect(url_for('login'))
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            user = query_db("SELECT * FROM users WHERE username = ?", (data['username'],), single=True)
            
            if not user or user['is_admin'] != 1:
                flash("Access denied: Admins only.")
                return redirect(url_for('hello'))
                
            return f(user, *args, **kwargs)
        except Exception:
            return redirect(url_for('login'))
    return decorated

# --- AUTHENTICATION ROUTES ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), single=True)

        if user and check_password_hash(user["password_hash"], password):
            payload = {
                'username': username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=2)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
            
            # Role-Based Redirect
            target = "admin_dashboard" if user["is_admin"] == 1 else "hello"
            response = make_response(redirect(url_for(target)))
            
            response.set_cookie('access_token', token, httponly=True, samesite='Lax')
            return response
        
        flash("Invalid username or password")
    
    return render_template("login.html")

@app.route("/admin")
@admin_required
def admin_dashboard(current_user):
    return render_template("admin_dashboard.html", user=current_user['username'])

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("login")))
    response.set_cookie('access_token', '', expires=0)
    flash("You have been logged out.")
    return response