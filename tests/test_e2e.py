"""End-to-end tests for the Flask application using Selenium."""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def chrome_options():
    """Configure Chrome options for headless testing."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    return options


@pytest.fixture
def driver(chrome_options, live_server):
    """Initialize Selenium WebDriver."""
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        pytest.skip("ChromeDriver not available")
    
    yield driver
    driver.quit()


@pytest.fixture
def wait(driver):
    """WebDriverWait instance for explicit waits."""
    return WebDriverWait(driver, 10)


class TestUserLoginE2E:
    """End-to-end tests for user login workflow."""
    
    def test_user_login_and_redirect_to_dashboard(self, driver, live_server, wait):
        """Test that a regular user can login and is redirected to their dashboard."""
        base_url = live_server.url
        driver.get(f"{base_url}/login")
        
        # Verify login page is loaded
        assert "Login" in driver.page_source or "login" in driver.page_source.lower()
        
        # Fill in login form
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys("test user")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect and verify dashboard page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Allow redirect to complete
        
        assert "/dashboard" in driver.current_url
        assert driver.get_cookie("access_token") is not None
    
    def test_user_logout(self, driver, live_server, wait):
        """Test that a user can logout successfully."""
        base_url = live_server.url
        
        # Login first
        driver.get(f"{base_url}/login")
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys("test user")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        # Now logout
        logout_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Logout')]"))
        )
        logout_link.click()
        
        time.sleep(1)
        assert "/login" in driver.current_url
        assert driver.get_cookie("access_token") is None


class TestAdminLoginE2E:
    """End-to-end tests for admin login workflow."""
    
    def test_admin_login_and_redirect_to_admin_dashboard(self, driver, live_server, wait):
        """Test that an admin can login and is redirected to admin dashboard."""
        base_url = live_server.url
        driver.get(f"{base_url}/login")
        
        # Verify login page is loaded
        assert "Login" in driver.page_source or "login" in driver.page_source.lower()
        
        # Fill in login form with admin credentials
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys("default admin")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect and verify admin dashboard page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        assert "/admin" in driver.current_url
        assert driver.get_cookie("access_token") is not None
    
    def test_admin_create_user(self, driver, live_server, wait):
        """Test that an admin can create a new user."""
        base_url = live_server.url
        
        # Login as admin
        driver.get(f"{base_url}/login")
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys("default admin")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        # Fill in create user form
        new_username = "e2e_test_user"
        new_password = "test_password_123"
        
        username_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
        )
        username_field.send_keys(new_username)
        
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        password_field.send_keys(new_password)
        
        # Submit form
        create_button = driver.find_element(
            By.CSS_SELECTOR, "button[type='submit']:last-of-type"
        )
        create_button.click()
        
        time.sleep(1)
        
        # Verify user was created (should see success message or user in list)
        page_source = driver.page_source
        assert "created successfully" in page_source.lower() or new_username in page_source


class TestInvalidLoginE2E:
    """End-to-end tests for invalid login scenarios."""
    
    def test_invalid_credentials(self, driver, live_server, wait):
        """Test that invalid credentials show an error."""
        base_url = live_server.url
        driver.get(f"{base_url}/login")
        
        # Fill in login form with wrong credentials
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys("nonexistent_user")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("wrong_password")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        time.sleep(1)
        
        # Should remain on login page
        assert "/login" in driver.current_url
        assert driver.get_cookie("access_token") is None
    
    def test_empty_username(self, driver, live_server, wait):
        """Test that empty username shows an error."""
        base_url = live_server.url
        driver.get(f"{base_url}/login")
        
        # Leave username empty, fill password
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        time.sleep(1)
        
        # Should remain on login page
        assert "/login" in driver.current_url
        assert driver.get_cookie("access_token") is None
