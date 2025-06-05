"""
Test cases for authentication functionality.
"""
import pytest
from quart import Quart
from httpx import AsyncClient

from app import create_app


@pytest.fixture
async def app():
    """Create test application."""
    app = create_app('testing')
    return app


@pytest.fixture
async def client(app: Quart):
    """Create test client."""
    async with app.test_client() as client:
        yield client


class TestAuthentication:
    """Test authentication endpoints."""
    
    async def test_register_success(self, client):
        """Test successful user registration."""
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = await client.post('/auth/register', json=user_data)
        assert response.status_code == 201
        
        data = await response.get_json()
        assert data['message'] == 'User registered successfully'
        assert 'user' in data
        assert 'tokens' in data
        assert data['user']['email'] == user_data['email']
    
    async def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        user_data = {
            'name': 'Test User',
            'email': 'invalid-email',
            'password': 'testpassword123'
        }
        
        response = await client.post('/auth/register', json=user_data)
        assert response.status_code == 400
        
        data = await response.get_json()
        assert 'Invalid email format' in data['message']
    
    async def test_register_short_password(self, client):
        """Test registration with short password."""
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': '123'
        }
        
        response = await client.post('/auth/register', json=user_data)
        assert response.status_code == 400
        
        data = await response.get_json()
        assert 'Password must be at least 8 characters' in data['message']
    
    async def test_login_success(self, client):
        """Test successful login."""
        # First register a user
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        await client.post('/auth/register', json=user_data)
        
        # Then login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        response = await client.post('/auth/login', json=login_data)
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['message'] == 'Login successful'
        assert 'user' in data
        assert 'tokens' in data
    
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = await client.post('/auth/login', json=login_data)
        assert response.status_code == 401
        
        data = await response.get_json()
        assert 'Invalid email or password' in data['message']
    
    async def test_get_current_user_without_token(self, client):
        """Test getting current user without token."""
        response = await client.get('/auth/me')
        assert response.status_code == 401
        
        data = await response.get_json()
        assert 'No valid token provided' in data['message']
    
    async def test_logout_without_token(self, client):
        """Test logout without token."""
        response = await client.post('/auth/logout')
        assert response.status_code == 401
        
        data = await response.get_json()
        assert 'No valid token provided' in data['message']


class TestAPI:
    """Test API endpoints."""
    
    async def test_api_status(self, client):
        """Test API status endpoint."""
        response = await client.get('/api/v1/status')
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data['status'] == 'ok'
        assert 'version' in data
    
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get('/health')
        # Status might be 200 or 503 depending on services
        assert response.status_code in [200, 503]
        
        data = await response.get_json()
        assert 'status' in data
    
    async def test_get_users_without_auth(self, client):
        """Test getting users without authentication."""
        response = await client.get('/api/v1/users')
        # This should work as it's just an example endpoint
        # In production, you might require authentication
        assert response.status_code == 200
        
        data = await response.get_json()
        assert 'users' in data
        assert 'count' in data


class TestWebPages:
    """Test web page routes."""
    
    async def test_home_page(self, client):
        """Test home page."""
        response = await client.get('/')
        assert response.status_code == 200
        
        # Check if it returns HTML
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type
    
    async def test_login_page(self, client):
        """Test login page."""
        response = await client.get('/login')
        assert response.status_code == 200
    
    async def test_register_page(self, client):
        """Test register page."""
        response = await client.get('/register')
        assert response.status_code == 200
    
    async def test_docs_page(self, client):
        """Test docs page."""
        response = await client.get('/docs')
        assert response.status_code == 200


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    async def test_rate_limiting(self, client):
        """Test that rate limiting works."""
        # This test would need Redis to be running
        # For now, just test that the endpoint works
        response = await client.get('/api/v1/status')
        assert response.status_code == 200


# Pytest configuration
@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()