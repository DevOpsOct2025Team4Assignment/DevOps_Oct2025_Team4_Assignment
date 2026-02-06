"""End-to-end tests for the Flask application using Playwright."""
import pytest

# Test fixtures
TEST_NEW_USER_PASSWORD = "test_password_123"

pytestmark = pytest.mark.e2e


class TestUserLoginE2E:
    """End-to-end tests for user login workflow."""
    
    @pytest.mark.asyncio
    async def test_user_login_and_redirect_to_dashboard(self, page, live_server):
        """Test that a regular user can login and is redirected to their dashboard."""
        base_url = live_server.url
        await page.goto(f"{base_url}/login")
        
        # Verify login page is loaded
        content = await page.content()
        if "Login" not in content and "login" not in content.lower():
            pytest.fail("Login page not loaded correctly")
        
        # Fill in login form
        await page.fill("input[name='username']", "test user")
        await page.fill("input[name='password']", "password")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Wait for redirect and verify dashboard page
        await page.wait_for_url("**/dashboard/", timeout=10000)
        
        # Check for access token in cookies
        cookies = await page.context.cookies()
        cookie_names = [c['name'] for c in cookies]
        if "access_token" not in cookie_names:
            pytest.fail("Access token not found in cookies")
    
    @pytest.mark.asyncio
    async def test_user_logout(self, page, live_server):
        """Test that a user can logout successfully."""
        base_url = live_server.url
        
        # Login first
        await page.goto(f"{base_url}/login")
        await page.fill("input[name='username']", "test user")
        await page.fill("input[name='password']", "password")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard/", timeout=10000)
        
        # Now logout
        await page.click("a:has-text('Logout')")
        
        # Wait for redirect to login page
        await page.wait_for_url("**/login", timeout=10000)
        
        cookies = await page.context.cookies()
        cookie_names = [c['name'] for c in cookies]
        if "access_token" in cookie_names:
            pytest.fail("Access token should not be present after logout")


class TestAdminLoginE2E:
    """End-to-end tests for admin login workflow."""
    
    @pytest.mark.asyncio
    async def test_admin_login_and_redirect_to_admin_dashboard(self, page, live_server):
        """Test that an admin can login and is redirected to admin dashboard."""
        base_url = live_server.url
        await page.goto(f"{base_url}/login")
        
        # Verify login page is loaded
        content = await page.content()
        if "Login" not in content and "login" not in content.lower():
            pytest.fail("Login page not loaded correctly")
        
        # Fill in login form with admin credentials
        await page.fill("input[name='username']", "default admin")
        await page.fill("input[name='password']", "password")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Wait for redirect and verify admin dashboard page
        await page.wait_for_url("**/admin/", timeout=10000)
        
        cookies = await page.context.cookies()
        cookie_names = [c['name'] for c in cookies]
        if "access_token" not in cookie_names:
            pytest.fail("Access token not found in cookies after admin login")
    
    @pytest.mark.asyncio
    async def test_admin_create_user(self, page, live_server):
        """Test that an admin can create a new user."""
        base_url = live_server.url
        
        # Login as admin
        await page.goto(f"{base_url}/login")
        await page.fill("input[name='username']", "default admin")
        await page.fill("input[name='password']", "password")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/admin/", timeout=10000)
        
        # Fill in create user form
        new_username = "e2e_test_user"
        new_password = TEST_NEW_USER_PASSWORD
        
        # Wait for the form to be visible and fill it
        await page.wait_for_selector("input[name='username']", timeout=5000)
        username_inputs = await page.query_selector_all("input[name='username']")
        password_inputs = await page.query_selector_all("input[name='password']")
        
        # Fill the create user form (the second set of inputs on the page)
        if len(username_inputs) > 0:
            await username_inputs[0].fill(new_username)
        if len(password_inputs) > 0:
            await password_inputs[0].fill(new_password)
        
        # Submit form (click the create user submit button)
        buttons = await page.query_selector_all("button.submit-btn")
        if buttons:
            await buttons[0].click()
        
        # Wait a moment for form submission
        await page.wait_for_timeout(1000)
        
        # Verify user was created (should see success message or user in list)
        content = await page.content()
        if "created successfully" not in content.lower() and new_username not in content:
            pytest.fail("User creation could not be verified")


class TestInvalidLoginE2E:
    """End-to-end tests for invalid login scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self, page, live_server):
        """Test that invalid credentials show an error."""
        base_url = live_server.url
        await page.goto(f"{base_url}/login")
        
        # Fill in login form with wrong credentials
        await page.fill("input[name='username']", "nonexistent_user")
        await page.fill("input[name='password']", "wrong_password")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Wait a moment for potential redirect or error message
        await page.wait_for_timeout(1000)
        
        # Should remain on login page
        if "/login" not in page.url:
            pytest.fail("Should remain on login page after invalid credentials")
        cookies = await page.context.cookies()
        cookie_names = [c['name'] for c in cookies]
        if "access_token" in cookie_names:
            pytest.fail("Access token should not be present with invalid credentials")
    
    @pytest.mark.asyncio
    async def test_empty_username(self, page, live_server):
        """Test that empty username shows an error."""
        base_url = live_server.url
        await page.goto(f"{base_url}/login")
        
        # Leave username empty, fill password
        await page.fill("input[name='password']", "password")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Wait a moment for potential redirect or error message
        await page.wait_for_timeout(1000)
        
        # Should remain on login page
        if "/login" not in page.url:
            pytest.fail("Should remain on login page with empty username")
        cookies = await page.context.cookies()
        cookie_names = [c['name'] for c in cookies]
        if "access_token" in cookie_names:
            pytest.fail("Access token should not be present with empty username")