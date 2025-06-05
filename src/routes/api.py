"""
API routes for the application.
"""
from quart import Blueprint, jsonify, request, current_app

from src.services.error_handler import ValidationError, NotFoundError
from src.services.logging_service import get_logger
from src.extensions import get_db_session
from src.utils.decorators import rate_limit

api_bp = Blueprint('api', __name__)
logger = get_logger(__name__)


@api_bp.route('/status')
async def api_status():
    """API status endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'environment': current_app.config.get('QUART_ENV', 'development')
    })


@api_bp.route('/health')
async def health_check():
    """Detailed health check endpoint."""
    try:
        from src.extensions import db, redis_client
        
        # Check database
        db_healthy = await db.health_check()
        
        # Check Redis
        redis_healthy = False
        try:
            await redis_client.ping()
            redis_healthy = True
        except Exception:
            pass
        
        # Get database stats
        db_stats = await db.get_database_stats() if db_healthy else {}
        
        health_data = {
            'status': 'healthy' if db_healthy and redis_healthy else 'degraded',
            'timestamp': '2025-06-04T12:00:00Z',  # Would use actual timestamp
            'services': {
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'stats': db_stats
                },
                'cache': {
                    'status': 'healthy' if redis_healthy else 'unhealthy'
                }
            }
        }
        
        status_code = 200 if db_healthy and redis_healthy else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@api_bp.route('/users', methods=['GET'])
@rate_limit('100 per hour')
async def get_users():
    """Get all users."""
    try:
        # Example query - replace with actual user model
        session = await get_db_session()
        try:
            # This would be replaced with actual user query
            users = [
                {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ]
        finally:
            await session.close()
        
        return jsonify({
            'users': users,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise


@api_bp.route('/users', methods=['POST'])
@rate_limit('10 per hour')
async def create_user():
    """Create a new user."""
    try:
        data = await request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate email format (basic validation)
        email = data.get('email')
        if '@' not in email:
            raise ValidationError("Invalid email format")
        
        # Create user (example - replace with actual user creation)
        user_data = {
            'id': 123,  # Would be auto-generated
            'name': data['name'],
            'email': data['email'],
            'created_at': '2025-06-04T12:00:00Z'
        }
        
        logger.info(f"User created: {user_data['email']}")
        
        return jsonify({
            'message': 'User created successfully',
            'user': user_data
        }), 201
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@rate_limit('200 per hour')
async def get_user(user_id: int):
    """Get a specific user."""
    try:
        # Example query - replace with actual user lookup
        if user_id == 1:
            user = {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
        elif user_id == 2:
            user = {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        else:
            raise NotFoundError("User")
        
        return jsonify({'user': user})
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@rate_limit('20 per hour')
async def update_user(user_id: int):
    """Update a specific user."""
    try:
        data = await request.get_json()
        
        # Check if user exists (example)
        if user_id not in [1, 2]:
            raise NotFoundError("User")
        
        # Validate email if provided
        if 'email' in data and '@' not in data['email']:
            raise ValidationError("Invalid email format")
        
        # Update user (example)
        updated_user = {
            'id': user_id,
            'name': data.get('name', 'John Doe'),
            'email': data.get('email', 'john@example.com'),
            'updated_at': '2025-06-04T12:00:00Z'
        }
        
        logger.info(f"User updated: {user_id}")
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user
        })
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@rate_limit('10 per hour')
async def delete_user(user_id: int):
    """Delete a specific user."""
    try:
        # Check if user exists (example)
        if user_id not in [1, 2]:
            raise NotFoundError("User")
        
        # Delete user (example)
        logger.info(f"User deleted: {user_id}")
        
        return jsonify({
            'message': 'User deleted successfully'
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise


@api_bp.route('/search/users', methods=['GET'])
@rate_limit('50 per hour')
async def search_users():
    """Search users with query parameters."""
    try:
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 100)
        offset = int(request.args.get('offset', 0))
        
        if not query:
            raise ValidationError("Search query parameter 'q' is required")
        
        # Example search - replace with actual search logic
        all_users = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        # Simple search by name (replace with database search)
        matching_users = [
            user for user in all_users 
            if query.lower() in user['name'].lower()
        ]
        
        # Apply pagination
        paginated_users = matching_users[offset:offset + limit]
        
        return jsonify({
            'users': paginated_users,
            'total': len(matching_users),
            'limit': limit,
            'offset': offset,
            'query': query
        })
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to search users: {e}")
        raise