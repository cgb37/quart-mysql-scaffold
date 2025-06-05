"""
Authentication service for JWT token management.
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from quart import current_app

from src.extensions import get_redis
from src.services.error_handler import UnauthorizedError
from src.services.logging_service import get_logger


class AuthService:
    """Authentication service for managing JWT tokens."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def generate_tokens(self, user_id: int, email: str) -> Dict[str, str]:
        """Generate access and refresh tokens for a user."""
        try:
            now = datetime.utcnow()
            
            # Access token payload
            access_payload = {
                'user_id': user_id,
                'email': email,
                'iat': now,
                'exp': now + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
                'type': 'access'
            }
            
            # Refresh token payload
            refresh_payload = {
                'user_id': user_id,
                'email': email,
                'iat': now,
                'exp': now + timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES']),
                'type': 'refresh'
            }
            
            # Generate tokens
            access_token = jwt.encode(
                access_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            refresh_token = jwt.encode(
                refresh_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            # Store refresh token in Redis
            redis_client = await get_redis()
            refresh_key = f"refresh_token:{user_id}"
            await redis_client.setex(
                refresh_key,
                current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
                refresh_token
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate tokens: {e}")
            raise
    
    async def verify_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            # Check if token is blacklisted
            if await self.is_token_blacklisted(token):
                raise UnauthorizedError("Token has been revoked")
            
            # Decode token
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Verify token type
            if payload.get('type') != token_type:
                raise UnauthorizedError(f"Invalid token type. Expected {token_type}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token has expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Invalid token")
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise UnauthorizedError("Token verification failed")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Generate new access token using refresh token."""
        try:
            # Verify refresh token
            payload = await self.verify_token(refresh_token, 'refresh')
            
            user_id = payload['user_id']
            email = payload['email']
            
            # Check if refresh token exists in Redis
            redis_client = await get_redis()
            stored_token = await redis_client.get(f"refresh_token:{user_id}")
            
            if not stored_token or stored_token != refresh_token:
                raise UnauthorizedError("Invalid refresh token")
            
            # Generate new access token
            now = datetime.utcnow()
            access_payload = {
                'user_id': user_id,
                'email': email,
                'iat': now,
                'exp': now + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
                'type': 'access'
            }
            
            access_token = jwt.encode(
                access_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            }
            
        except UnauthorizedError:
            raise
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            raise UnauthorizedError("Token refresh failed")
    
    async def blacklist_token(self, token: str) -> None:
        """Add token to blacklist."""
        try:
            # Decode token to get expiration
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256'],
                options={"verify_exp": False}
            )
            
            exp = payload.get('exp')
            if exp:
                # Calculate TTL
                exp_datetime = datetime.fromtimestamp(exp)
                ttl = max(0, int((exp_datetime - datetime.utcnow()).total_seconds()))
                
                if ttl > 0:
                    # Add to blacklist with TTL
                    redis_client = await get_redis()
                    await redis_client.setex(f"blacklist:{token}", ttl, "1")
            
        except Exception as e:
            self.logger.error(f"Failed to blacklist token: {e}")
            # Don't raise exception for blacklisting failures
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        try:
            redis_client = await get_redis()
            result = await redis_client.get(f"blacklist:{token}")
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    async def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Get user information from token."""
        try:
            # Verify token
            payload = await self.verify_token(token, 'access')
            
            user_id = payload['user_id']
            email = payload['email']
            
            # Example user lookup (replace with actual database query)
            users_db = {
                1: {'id': 1, 'email': 'john@example.com', 'name': 'John Doe'},
                2: {'id': 2, 'email': 'jane@example.com', 'name': 'Jane Smith'}
            }
            
            user = users_db.get(user_id)
            if not user:
                raise UnauthorizedError("User not found")
            
            return user
            
        except UnauthorizedError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get user from token: {e}")
            raise UnauthorizedError("Failed to get user information")
    
    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoke all tokens for a user."""
        try:
            redis_client = await get_redis()
            
            # Remove refresh token
            await redis_client.delete(f"refresh_token:{user_id}")
            
            # Note: Access tokens will expire naturally or can be blacklisted individually
            self.logger.info(f"All tokens revoked for user: {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to revoke user tokens: {e}")
            raise