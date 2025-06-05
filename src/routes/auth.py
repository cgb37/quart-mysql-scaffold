"""
Authentication routes.
"""
from quart import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from src.services.error_handler import ValidationError, UnauthorizedError, NotFoundError
from src.services.logging_service import get_logger
from src.services.auth_service import AuthService
from src.extensions import get_db_session
from src.utils.decorators import rate_limit

auth_bp = Blueprint('auth', __name__)
logger = get_logger(__name__)
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
@rate_limit('5 per hour')
async def register():
    """Register a new user."""
    try:
        data = await request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"Missing required field: {field}")
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ValidationError("Invalid email format")
        
        # Validate password strength
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Check if user already exists (example)
        existing_users = ['john@example.com', 'jane@example.com']
        if email in existing_users:
            raise ValidationError("User with this email already exists")
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user (example - replace with actual user creation)
        user_data = {
            'id': 123,
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'created_at': '2025-06-04T12:00:00Z',
            'is_active': True
        }
        
        # Generate tokens
        tokens = await auth_service.generate_tokens(user_data['id'], user_data['email'])
        
        logger.info(f"User registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name']
            },
            'tokens': tokens
        }), 201
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise


@auth_bp.route('/login', methods=['POST'])
@rate_limit('10 per hour')
async def login():
    """Authenticate user and return tokens."""
    try:
        data = await request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            raise ValidationError("Email and password are required")
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Example user lookup (replace with actual database query)
        users_db = {
            'john@example.com': {
                'id': 1,
                'email': 'john@example.com',
                'name': 'John Doe',
                'password_hash': generate_password_hash('password123'),
                'is_active': True
            },
            'jane@example.com': {
                'id': 2,
                'email': 'jane@example.com',
                'name': 'Jane Smith',
                'password_hash': generate_password_hash('password456'),
                'is_active': True
            }
        }
        
        user = users_db.get(email)
        if not user:
            raise UnauthorizedError("Invalid email or password")
        
        # Check password
        if not check_password_hash(user['password_hash'], password):
            raise UnauthorizedError("Invalid email or password")
        
        # Check if user is active
        if not user.get('is_active', True):
            raise UnauthorizedError("Account is deactivated")
        
        # Generate tokens
        tokens = await auth_service.generate_tokens(user['id'], user['email'])
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name']
            },
            'tokens': tokens
        })
        
    except (ValidationError, UnauthorizedError):
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise


@auth_bp.route('/refresh', methods=['POST'])
@rate_limit('20 per hour')
async def refresh_token():
    """Refresh access token using refresh token."""
    try:
        data = await request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            raise ValidationError("Refresh token is required")
        
        # Verify refresh token and get new access token
        tokens = await auth_service.refresh_access_token(refresh_token)
        
        logger.info("Token refreshed successfully")
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'tokens': tokens
        })
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise UnauthorizedError("Invalid refresh token")


@auth_bp.route('/logout', methods=['POST'])
async def logout():
    """Logout user and invalidate tokens."""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise UnauthorizedError("No valid token provided")
        
        token = auth_header.split(' ')[1]
        
        # Blacklist the token
        await auth_service.blacklist_token(token)
        
        logger.info("User logged out successfully")
        
        return jsonify({
            'message': 'Logout successful'
        })
        
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise


@auth_bp.route('/me', methods=['GET'])
async def get_current_user():
    """Get current authenticated user information."""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise UnauthorizedError("No valid token provided")
        
        token = auth_header.split(' ')[1]
        
        # Verify token and get user info
        user_info = await auth_service.get_user_from_token(token)
        
        return jsonify({
            'user': user_info
        })
        
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        raise


@auth_bp.route('/change-password', methods=['POST'])
async def change_password():
    """Change user password."""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise UnauthorizedError("No valid token provided")
        
        token = auth_header.split(' ')[1]
        user_info = await auth_service.get_user_from_token(token)
        
        data = await request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            raise ValidationError("Current password and new password are required")
        
        # Validate new password strength
        if len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters long")
        
        # Verify current password (example - replace with actual verification)
        # This would involve fetching the user's current password hash and verifying
        
        # Update password (example)
        new_password_hash = generate_password_hash(new_password)
        
        logger.info(f"Password changed for user: {user_info['email']}")
        
        return jsonify({
            'message': 'Password changed successfully'
        })
        
    except (UnauthorizedError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise