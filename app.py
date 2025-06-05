"""
Main application factory and configuration.
"""
import os
from typing import Optional

from quart import Quart, jsonify
from quart.logging import default_handler
from sqlalchemy import text

from src.config import get_config
from src.extensions import db, redis_client, init_extensions
from src.middleware import register_middleware
from src.routes import register_blueprints
from src.services.logging_service import setup_logging
from src.services.error_handler import register_error_handlers


def create_app(config_name: Optional[str] = None) -> Quart:
    """Application factory pattern."""
    app = Quart(__name__, template_folder='templates')
    
    # Load configuration
    config_name = config_name or os.getenv('QUART_ENV', 'development')
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    setup_logging(app)
    app.logger.removeHandler(default_handler)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Health check endpoint
    @app.route('/health')
    async def health_check():
        """Health check endpoint for Docker and load balancers."""
        try:
            # Check database connection
            async with db.engine.connect() as connection:
                await connection.execute(text('SELECT 1'))
            
            # Check Redis connection (only if initialized)
            if redis_client is not None:
                await redis_client.ping()
                cache_status = 'connected'
            else:
                cache_status = 'initializing'
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'cache': cache_status
            }), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    @app.before_serving
    async def startup():
        """Application startup tasks."""
        app.logger.info("Application starting up...")
        
        # Create database tables
        async with app.app_context():
            await db.create_all()
        
        app.logger.info("Application startup complete")
    
    @app.after_serving
    async def shutdown():
        """Application shutdown tasks."""
        app.logger.info("Application shutting down...")
        
        # Close database connections
        await db.engine.dispose()
        
        # Close Redis connections
        await redis_client.close()
        
        app.logger.info("Application shutdown complete")
    
    return app


# Create application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)