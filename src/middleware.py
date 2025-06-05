"""
Application middleware for security, rate limiting, and request processing.
"""
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps

from quart import Quart, request, g, jsonify
from werkzeug.exceptions import TooManyRequests

from src.extensions import get_redis
from src.services.logging_service import get_logger


async def add_request_id():
    """Add unique request ID to each request."""
    g.request_id = str(uuid.uuid4())
    g.request_start_time = time.time()


async def add_security_headers(response):
    """Add security headers to responses."""
    if not response:
        return response
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    
    # Add request ID to response headers
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id
    
    return response


async def add_cors_headers(response):
    """Add CORS headers to responses."""
    if not response:
        return response
    
    origin = request.headers.get('Origin')
    allowed_origins = ['http://localhost:3000', 'http://localhost:5000']  # Configure as needed
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'
    
    return response


class RateLimiter:
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app: Optional[Quart] = None):
        self.app = app
        self.logger = get_logger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Quart):
        """Initialize rate limiter with app."""
        self.app = app
        self.enabled = app.config.get('RATELIMIT_ENABLED', True)
        self.default_limit = app.config.get('RATELIMIT_DEFAULT', '100 per hour')
    
    def limit(self, limit_string: str):
        """Decorator to apply rate limiting to routes."""
        def decorator(f):
            @wraps(f)
            async def decorated_function(*args, **kwargs):
                if not self.enabled:
                    return await f(*args, **kwargs)
                
                # Parse limit string (e.g., "100 per hour", "5 per minute")
                limit, period = self._parse_limit_string(limit_string)
                
                # Get client identifier
                client_id = self._get_client_id()
                
                # Check rate limit
                if not await self._check_rate_limit(client_id, limit, period):
                    raise TooManyRequests(f"Rate limit exceeded: {limit_string}")
                
                return await f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _parse_limit_string(self, limit_string: str) -> tuple:
        """Parse limit string into limit and period."""
        parts = limit_string.lower().split()
        
        if len(parts) != 3 or parts[1] != 'per':
            raise ValueError(f"Invalid limit string: {limit_string}")
        
        limit = int(parts[0])
        period_str = parts[2]
        
        period_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        period = period_map.get(period_str)
        if period is None:
            raise ValueError(f"Invalid period: {period_str}")
        
        return limit, period
    
    def _get_client_id(self) -> str:
        """Get client identifier for rate limiting."""
        # Use IP address as default identifier
        # In production, you might want to use authenticated user ID
        return request.remote_addr or 'unknown'
    
    async def _check_rate_limit(self, client_id: str, limit: int, period: int) -> bool:
        """Check if client has exceeded rate limit."""
        try:
            redis_client = await get_redis()
            key = f"rate_limit:{client_id}:{request.endpoint}"
            
            # Use sliding window counter
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=period)
            
            # Remove old entries
            await redis_client.zremrangebyscore(key, 0, window_start.timestamp())
            
            # Count current requests
            current_count = await redis_client.zcard(key)
            
            if current_count >= limit:
                return False
            
            # Add current request
            await redis_client.zadd(key, {str(uuid.uuid4()): now.timestamp()})
            
            # Set expiration
            await redis_client.expire(key, period)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return True

    async def check_and_apply_limit(self, limit_string: str):
        """Check and apply rate limit for current request."""
        if not self.enabled:
            return
        
        # Parse limit string
        limit, period = self._parse_limit_string(limit_string)
        
        # Get client identifier
        client_id = self._get_client_id()
        
        # Check rate limit
        if not await self._check_rate_limit(client_id, limit, period):
            raise TooManyRequests(f"Rate limit exceeded: {limit_string}")


def create_request_context_middleware():
    """Create request context middleware."""
    
    async def before_request():
        """Set up request context."""
        await add_request_id()
        
        # Add user context if authenticated
        # This would be implemented with your authentication system
        g.user_id = None  # Set from JWT token or session
        g.user_roles = []  # Set from JWT token or session
    
    async def after_request(response):
        """Clean up request context and add headers."""
        # Add performance timing
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Add security headers
        response = await add_security_headers(response)
        
        # Add CORS headers
        response = await add_cors_headers(response)
        
        return response
    
    return before_request, after_request


def register_middleware(app: Quart):
    """Register all middleware with the application."""
    logger = get_logger(__name__)
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(app)
    
    # Register request context middleware
    before_request, after_request = create_request_context_middleware()
    
    app.before_request(before_request)
    app.after_request(after_request)
    
    # Handle OPTIONS requests for CORS
    @app.before_request
    async def handle_preflight():
        if request.method == 'OPTIONS':
            response = jsonify({})
            response = await add_cors_headers(response)
            return response
    
    # Store rate limiter instance for use in routes
    app.rate_limiter = rate_limiter
    
    logger.info("Middleware registered successfully")