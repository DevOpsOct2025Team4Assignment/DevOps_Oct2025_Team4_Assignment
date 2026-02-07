import os
import shutil
import tempfile
import threading

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from playwright.async_api import async_playwright

from app import create_app
from app.db import init_db, query_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    file_store = tempfile.mkdtemp()

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
            "FILE_STORE": file_store,
        }
    )

    with app.app_context():
        init_db()
        query_db(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?), (?, ?, ?)",
            (
                "test user",
                generate_password_hash("password"),
                0,
                "test user 2",
                generate_password_hash("password"),
                0,
            ),
        )

    yield app

    os.close(db_fd)
    os.unlink(db_path)
    shutil.rmtree(file_store)


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


@pytest.fixture
def live_server(app: Flask):
    """Start a live server for E2E testing."""
    from werkzeug.serving import make_server
    
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    class LiveServer:
        def __init__(self, server, app):
            self.server = server
            self.host = server.host
            self.port = server.server_port
            self.app = app
        
        @property
        def url(self):
            return f"http://{self.host}:{self.port}"
    
    live_server = LiveServer(server, app)
    
    yield live_server
    
    server.shutdown()


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


@pytest.fixture
async def browser():
    """Initialize Playwright browser for async tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser, live_server):
    """Create a new Playwright page for each async test."""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()
