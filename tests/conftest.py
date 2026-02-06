import os
import tempfile
import threading
import asyncio

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from playwright.async_api import async_playwright

from app import create_app
from app.db import init_db, query_db


@pytest.fixture
def event_loop(request):
    """Create an event loop for async tests."""
    # Only create a new loop if we're running async tests
    if "asyncio" in request.keywords or "e2e" in request.keywords:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        yield loop
        loop.close()
    else:
        # For synchronous tests, don't create a loop
        yield None


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
async def browser(event_loop):
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
    # Setup default admin user for e2e tests
    await page.context.add_init_script("""
        window.localStorage.setItem('test_ready', 'true');
    """)
    yield page
    await context.close()
