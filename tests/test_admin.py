
import jwt
from flask import current_app
from datetime import datetime, timedelta, timezone
import io
import os
from flask import Flask
from flask.testing import FlaskClient

from app.db import query_db
from tests.conftest import AuthActions

def test_admin_create_user(client, auth, app):
    auth.login(username="default admin", password="password")

    username = "new_employee_2024"
    response = client.post("/admin/create_user", data={
        "username": username,
        "password": "password123",
        "is_admin": "1"
    }, follow_redirects=True)

    assert response.status_code == 200

    assert b"created successfully!" in response.data
    assert username.encode() in response.data

def test_admin_delete_user(client, auth, app):
    """Verify admin can delete the 'test user' created in conftest.py."""
    auth.login(username="default admin", password="password")

    with app.app_context():
        target = query_db("SELECT id FROM users WHERE username = ?", ("test user",), single=True)
        target_id = target["id"]

    response = client.post(f"/admin/delete_user/{target_id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"User account removed." in response.data



def test_admin_prevent_self_deletion(client, auth, app):
    """Test security logic preventing admin from deleting themselves."""
    auth.login(username="default admin", password="password")

    with app.app_context():
        admin = query_db("SELECT id FROM users WHERE username = 'default admin'", single=True)
        admin_id = admin["id"]

    response = client.post(f"/admin/delete_user/{admin_id}", follow_redirects=True)
    assert b"Security alert: You cannot delete your own account." in response.data

def test_delete_user_cleans_up_files(
    client: FlaskClient, auth: AuthActions, app: Flask
):
    auth.login(username="test user", password="password")

    data = {"file": (io.BytesIO(b"test file content"), "test_file.txt")}
    client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    with app.app_context():
        file_record = query_db(
            "SELECT * FROM files WHERE display_name = 'test_file.txt'", single=True
        )
        assert file_record is not None
        file_path = os.path.join(app.config["FILE_STORE"], file_record["file_path"])
        assert os.path.exists(file_path), "File should exist before user deletion"
        user_id = file_record["user_id"]

    auth.login(username="default admin", password="password")

    response = client.post(f"/admin/delete_user/{user_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"User account removed" in response.data

    assert not os.path.exists(file_path), "File should be deleted from disk"

    with app.app_context():
        user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), single=True)
        assert user is None

        file_record_after = query_db(
            "SELECT * FROM files WHERE id = ?", (file_record["id"],), single=True
        )
        assert file_record_after is None


