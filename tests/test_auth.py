from tests.conftest import AuthActions
from flask import url_for
from app.db import query_db
import pytest
from flask import Flask
from flask.testing import FlaskClient


def test_login_page_loads(client: FlaskClient):
    response = client.get("/login")
    assert response.status_code == 200


def test_user_login(client: FlaskClient, app: Flask):
    response = client.post(
        "/login",
        data={"username": "test user", "password": "password"},
        follow_redirects=True,
    )
    assert len(response.history) == 1
    assert response.status_code == 200
    assert response.request.path == url_for("dashboard.index")

    with app.app_context():
        assert (
            query_db("SELECT * FROM users WHERE username = 'test user'", single=True)
            is not None
        )


def test_admin_login(client: FlaskClient, app: Flask):
    response = client.post(
        "/login",
        data={"username": "default admin", "password": "password"},
        follow_redirects=True,
    )
    assert len(response.history) == 1
    assert response.status_code == 200
    assert response.request.path.rstrip("/") == url_for("admin.dashboard").rstrip("/")

    with app.app_context():
        assert (
            query_db(
                "SELECT * FROM users WHERE username = 'default admin'", single=True
            )
            is not None
        )


@pytest.mark.parametrize(
    ("username", "password"),
    (
        ("", ""),
        ("test user", ""),
        ("", "password"),
    ),
)
def test_login_fail(client: FlaskClient, username: str, password: str):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert len(response.history) == 1
    assert response.status_code == 200
    assert response.request.path == url_for("auth.login").rstrip("/")


def test_logout(client: FlaskClient, auth: AuthActions):
    auth.login()
    assert client.get_cookie("access_token") is not None

    response = client.get("/logout", follow_redirects=True)
    assert len(response.history) == 1
    assert response.status_code == 200
    assert response.request.path == url_for("auth.login").rstrip("/")
    assert client.get_cookie("access_token") is None
