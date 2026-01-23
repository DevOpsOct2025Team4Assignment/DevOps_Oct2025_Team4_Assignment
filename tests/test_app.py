import pytest
import sqlite3
import os
import tempfile
from app import app as flask_app, get_db, DB_PATH, SCHEMA_PATH
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Provide a test client for the Flask app with an initialized database."""
    # Use a temporary database file for testing
    test_db_fd, test_db_path = tempfile.mkstemp()
    
    # Temporarily override the DB_PATH
    original_db_path = os.environ.get('TEST_DB_PATH')
    os.environ['TEST_DB_PATH'] = test_db_path
    
    # Configure the app for testing
    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE"] = test_db_path
    
    # Initialize the test database
    with flask_app.app_context():
        db = sqlite3.connect(test_db_path)
        with open(SCHEMA_PATH, "r") as f:
            db.executescript(f.read())
        db.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
            ("test_admin", generate_password_hash("password")),
        )
        db.commit()
        db.close()
    
    # Create test client
    with flask_app.test_client() as test_client:
        yield test_client
    
    # Cleanup
    os.close(test_db_fd)
    os.unlink(test_db_path)
    if original_db_path is not None:
        os.environ['TEST_DB_PATH'] = original_db_path
    elif 'TEST_DB_PATH' in os.environ:
        del os.environ['TEST_DB_PATH']

def test_home(client):
    """Test the '/' route returns 200 and expected content."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello!" in response.data
