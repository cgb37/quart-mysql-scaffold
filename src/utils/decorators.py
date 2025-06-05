"""
Utility decorators for the application.
"""
from functools import wraps
from quart import current_app
from werkzeug.exceptions import TooManyRequests

from src.services.logging_service import get_logger

logger = get_logger(__name__)


def rate_limit(limit_string: str):
    """
    Rate limiting decorator that works with blueprint registration.
    
    Args:
        limit_string: Rate limit specification (e.g., "100 per hour", "5 per minute")
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Check if rate limiter is available
            rate_limiter = getattr(current_app, 'rate_limiter', None)
            if rate_limiter and rate_limiter.enabled:
                try:
                    # Use the rate limiter's check_and_apply_limit method
                    await rate_limiter.check_and_apply_limit(limit_string)
                except Exception as e:
                    logger.warning(f"Rate limiting error: {e}")
                    # Continue without rate limiting if there's an error
            else:
                logger.debug("Rate limiter not available or disabled")
            
            return await f(*args, **kwargs)
        return decorated_function
    return decorator
