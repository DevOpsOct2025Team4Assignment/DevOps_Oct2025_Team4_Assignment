import pytest
from app import app as flask_app

@pytest.fixture
def client():
    """Provide a test client for the Flask app."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

def test_home(client):
    """Test the '/' route returns 200 and expected content."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello!" in response.data
