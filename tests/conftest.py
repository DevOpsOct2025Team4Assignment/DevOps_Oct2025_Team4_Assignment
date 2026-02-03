import os
import tempfile

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import init_db, query_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
        }
    )

    with app.app_context():
        init_db()
        query_db(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ("test user", generate_password_hash("password"), 0),
        )

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client: FlaskClient):
        self._client: FlaskClient = client

    def login(self, username="test user", password="password"):
        return self._client.post(
            "/login",
            data={"username": username, "password": password},
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client: FlaskClient):
    return AuthActions(client)
