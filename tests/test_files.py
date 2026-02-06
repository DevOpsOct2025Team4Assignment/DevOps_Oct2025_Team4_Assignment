import io
import os

from flask import url_for
from flask.testing import FlaskClient

from app.db import query_db
from tests.conftest import AuthActions


def test_view_dashboard_unauthorized(client: FlaskClient):
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == url_for("auth.login")


def test_view_dashboard(client: FlaskClient, auth: AuthActions):
    auth.login()
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200


def test_upload_file(client: FlaskClient, auth: AuthActions, app):
    auth.login()

    data = {"file": (io.BytesIO(b"test content"), "test.txt")}

    response = client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        file_record = query_db(
            "SELECT * FROM files WHERE display_name = 'test.txt'", single=True
        )
        assert file_record is not None
        assert file_record["size_bytes"] == len(b"test content")

        file_path = os.path.join(app.config["FILE_STORE"], file_record["file_path"])
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            assert f.read() == b"test content"


def test_download_file(client: FlaskClient, auth: AuthActions, app):
    auth.login()

    # Upload first
    data = {"file": (io.BytesIO(b"download content"), "download.txt")}
    client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    with app.app_context():
        file_record = query_db(
            "SELECT * FROM files WHERE display_name = 'download.txt'", single=True
        )
        file_id = file_record["id"]

    response = client.get(f"/dashboard/download/{file_id}")
    assert response.status_code == 200
    assert response.data == b"download content"


def test_delete_file(client: FlaskClient, auth: AuthActions, app):
    auth.login()

    # Upload first
    data = {"file": (io.BytesIO(b"delete content"), "delete.txt")}
    client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    with app.app_context():
        file_record = query_db(
            "SELECT * FROM files WHERE display_name = 'delete.txt'", single=True
        )
        file_id = file_record["id"]
        file_path = os.path.join(app.config["FILE_STORE"], file_record["file_path"])

    response = client.post(f"/dashboard/delete/{file_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"File deleted successfully" in response.data

    with app.app_context():
        assert (
            query_db("SELECT * FROM files WHERE id = ?", (file_id,), single=True)
            is None
        )
        assert not os.path.exists(file_path)


def test_upload_no_file(client: FlaskClient, auth: AuthActions):
    auth.login()
    response = client.post("/dashboard/upload", data={}, follow_redirects=True)
    assert b"No file part" in response.data


def test_upload_empty_filename(client, auth: AuthActions):
    auth.login()
    data = {"file": (io.BytesIO(b""), "")}
    response = client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"No selected file" in response.data


def test_access_other_user_file(client: FlaskClient, auth: AuthActions, app):
    # Upload as default user
    auth.login()
    data = {"file": (io.BytesIO(b"user1 content"), "user1.txt")}
    client.post("/dashboard/upload", data=data, content_type="multipart/form-data")

    with app.app_context():
        file_record = query_db(
            "SELECT * FROM files WHERE display_name = 'user1.txt'", single=True
        )
        file_id = file_record["id"]

    auth.logout()
    auth.login(username="test user 2")

    # Try to download first user's file
    response = client.get(f"/dashboard/download/{file_id}", follow_redirects=True)
    assert b"File not found" in response.data  # Should behave like not found

    # Try to delete first user's file
    response = client.post(f"/dashboard/delete/{file_id}", follow_redirects=True)
    assert b"File not found" in response.data
