"""
Routes package for organizing API endpoints.
"""
from quart import Quart

from .api import api_bp
from .auth import auth_bp
from .web import web_bp


def register_blueprints(app: Quart) -> None:
    """Register all blueprints with the application."""
    
    # API routes
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Authentication routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Web routes (for serving HTML pages)
    app.register_blueprint(web_bp)
    
    app.logger.info("Blueprints registered successfully")