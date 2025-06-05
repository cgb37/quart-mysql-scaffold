"""
Logging service with structured logging support.
"""
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import structlog
from quart import Quart, request, g
from quart.logging import default_handler


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if hasattr(record, 'color') and record.color:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)


def setup_logging(app: Quart) -> None:
    """Setup application logging."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', 
                               '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = CustomFormatter(log_format)
    console_handler.setFormatter(console_formatter)
    
    # Add color attribute to records
    def add_color_to_record(record):
        record.color = True
        return True
    
    console_handler.addFilter(add_color_to_record)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup request logging
    setup_request_logging(app)
    
    app.logger.info("Logging configured successfully")


def setup_request_logging(app: Quart) -> None:
    """Setup request/response logging middleware."""
    
    @app.before_request
    async def before_request_logging():
        """Log incoming requests."""
        g.request_start_time = time.time()
        
        app.logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', ''),
                "request_id": getattr(g, 'request_id', None)
            }
        )
    
    @app.after_request
    async def after_request_logging(response):
        """Log request completion."""
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            
            app.logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                    "request_id": getattr(g, 'request_id', None)
                }
            )
        
        return response


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def get_structured_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""
    
    def filter(self, record):
        """Add request context to log record."""
        try:
            record.request_id = getattr(g, 'request_id', None)
            record.user_id = getattr(g, 'user_id', None)
            record.remote_addr = request.remote_addr if request else None
        except RuntimeError:
            # Outside of request context
            record.request_id = None
            record.user_id = None
            record.remote_addr = None
        
        return True


def log_exception(logger: logging.Logger, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log exception with context."""
    context = context or {}
    
    logger.error(
        f"Exception occurred: {exc.__class__.__name__}: {str(exc)}",
        extra={
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
            "context": context
        },
        exc_info=True
    )


def log_performance(logger: logging.Logger, operation: str, duration: float, context: Optional[Dict[str, Any]] = None) -> None:
    """Log performance metrics."""
    context = context or {}
    
    level = logging.WARNING if duration > 1.0 else logging.INFO
    
    logger.log(
        level,
        f"Performance: {operation} took {duration:.3f}s",
        extra={
            "operation": operation,
            "duration_seconds": duration,
            "context": context
        }
    )