"""
Error handling service with custom exception classes.
"""
import traceback
from typing import Dict, Any, Optional
from dataclasses import dataclass

from quart import Quart, jsonify, request
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.services.logging_service import get_logger


@dataclass
class ErrorResponse:
    """Standardized error response format."""
    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class BaseAPIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


class NotFoundError(BaseAPIException):
    """Resource not found exception."""
    
    def __init__(self, resource: str = "Resource", message: Optional[str] = None):
        message = message or f"{resource} not found"
        super().__init__(message, 404)


class UnauthorizedError(BaseAPIException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, 401)


class ForbiddenError(BaseAPIException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, 403)


class ConflictError(BaseAPIException):
    """Resource conflict exception."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, 409)


class RateLimitError(BaseAPIException):
    """Rate limit exceeded exception."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429)


class DatabaseError(BaseAPIException):
    """Database operation error."""
    
    def __init__(self, message: str = "Database operation failed", original_error: Optional[Exception] = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, 500, details)


class ExternalServiceError(BaseAPIException):
    """External service error."""
    
    def __init__(self, service: str, message: Optional[str] = None):
        message = message or f"External service '{service}' is unavailable"
        super().__init__(message, 503)


def create_error_response(
    error: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> tuple:
    """Create standardized error response."""
    error_response = ErrorResponse(
        error=error,
        message=message,
        status_code=status_code,
        details=details,
        request_id=request_id
    )
    
    response_data = {
        "error": error_response.error,
        "message": error_response.message,
        "status_code": error_response.status_code
    }
    
    if error_response.details:
        response_data["details"] = error_response.details
    
    if error_response.request_id:
        response_data["request_id"] = error_response.request_id
    
    return jsonify(response_data), status_code


def register_error_handlers(app: Quart) -> None:
    """Register error handlers for the application."""
    logger = get_logger(__name__)
    
    @app.errorhandler(BaseAPIException)
    async def handle_api_exception(error: BaseAPIException):
        """Handle custom API exceptions."""
        request_id = getattr(request, 'id', None) if request else None
        
        logger.warning(
            f"API Exception: {error.__class__.__name__}: {error.message}",
            extra={
                "exception_type": error.__class__.__name__,
                "status_code": error.status_code,
                "details": error.details,
                "request_id": request_id
            }
        )
        
        return create_error_response(
            error=error.__class__.__name__,
            message=error.message,
            status_code=error.status_code,
            details=error.details,
            request_id=request_id
        )
    
    @app.errorhandler(ValidationError)
    async def handle_validation_error(error: ValidationError):
        """Handle validation errors."""
        request_id = getattr(request, 'id', None) if request else None
        
        logger.warning(
            f"Validation Error: {error.message}",
            extra={
                "details": error.details,
                "request_id": request_id
            }
        )
        
        return create_error_response(
            error="ValidationError",
            message=error.message,
            status_code=400,
            details=error.details,
            request_id=request_id
        )
    
    @app.errorhandler(HTTPException)
    async def handle_http_exception(error: HTTPException):
        """Handle HTTP exceptions."""
        request_id = getattr(request, 'id', None) if request else None
        
        logger.warning(
            f"HTTP Exception: {error.code} - {error.description}",
            extra={
                "status_code": error.code,
                "request_id": request_id
            }
        )
        
        return create_error_response(
            error="HTTPException",
            message=error.description or "HTTP error occurred",
            status_code=error.code or 500,
            request_id=request_id
        )
    
    @app.errorhandler(SQLAlchemyError)
    async def handle_database_error(error: SQLAlchemyError):
        """Handle database errors."""
        request_id = getattr(request, 'id', None) if request else None
        
        logger.error(
            f"Database Error: {str(error)}",
            extra={
                "exception_type": error.__class__.__name__,
                "request_id": request_id
            },
            exc_info=True
        )
        
        # Don't expose internal database errors in production
        if app.config.get('DEBUG'):
            message = str(error)
            details = {"original_error": str(error)}
        else:
            message = "A database error occurred"
            details = None
        
        return create_error_response(
            error="DatabaseError",
            message=message,
            status_code=500,
            details=details,
            request_id=request_id
        )
    
    @app.errorhandler(Exception)
    async def handle_generic_exception(error: Exception):
        """Handle all other exceptions."""
        request_id = getattr(request, 'id', None) if request else None
        
        logger.error(
            f"Unhandled Exception: {error.__class__.__name__}: {str(error)}",
            extra={
                "exception_type": error.__class__.__name__,
                "traceback": traceback.format_exc(),
                "request_id": request_id
            },
            exc_info=True
        )
        
        # Don't expose internal errors in production
        if app.config.get('DEBUG'):
            message = str(error)
            details = {
                "exception_type": error.__class__.__name__,
                "traceback": traceback.format_exc()
            }
        else:
            message = "An internal server error occurred"
            details = None
        
        return create_error_response(
            error="InternalServerError",
            message=message,
            status_code=500,
            details=details,
            request_id=request_id
        )
    
    @app.errorhandler(404)
    async def handle_not_found(error):
        """Handle 404 errors."""
        request_id = getattr(request, 'id', None) if request else None
        
        return create_error_response(
            error="NotFound",
            message="The requested resource was not found",
            status_code=404,
            request_id=request_id
        )
    
    @app.errorhandler(405)
    async def handle_method_not_allowed(error):
        """Handle 405 errors."""
        request_id = getattr(request, 'id', None) if request else None
        
        return create_error_response(
            error="MethodNotAllowed",
            message="The requested method is not allowed for this resource",
            status_code=405,
            request_id=request_id
        )