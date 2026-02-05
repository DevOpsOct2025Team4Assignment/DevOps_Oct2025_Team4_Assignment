import pytest
from app.db import get_db, query_db
import jwt
from flask import current_app
from datetime import datetime, timedelta, timezone

def login_as_admin(client, app):
    """Helper to bypass fixture limitations and set a real Admin JWT."""
    with app.app_context():
        user = query_db("SELECT * FROM users WHERE username = 'default admin'", single=True)
        payload = {
            "sub": str(user['id']),
            "username": user['username'],
            "role": "admin", # Crucial for @auth_required(admin=True)
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
        client.set_cookie('access_token', token)

def test_admin_create_user(client, app):
    # 1. Manually set Admin Session
    login_as_admin(client, app)

    # 2. Test creation
    username = "new_test_worker"
    response = client.post("/admin/create_user", data={
        "username": username,
        "password": "password123",
        "is_admin": "" # False
    }, follow_redirects=True)

    assert b"created successfully!" in response.data
    
    with app.app_context():
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), single=True)
        assert user is not None

def test_admin_delete_user(client, app):
    # 1. Manually set Admin Session
    login_as_admin(client, app)

    with app.app_context():
        # Get 'test user' created in conftest.py
        target = query_db("SELECT id FROM users WHERE username = ?", ("test user",), single=True)
        target_id = target["id"]

    # 2. Test deletion
    response = client.post(f"/admin/delete_user/{target_id}", follow_redirects=True)

    # This should now work because we fixed 'admin.admin' to 'admin.dashboard'
    assert b"User account removed." in response.data

    with app.app_context():
        check = query_db("SELECT * FROM users WHERE id = ?", (target_id,), single=True)
        assert check is None