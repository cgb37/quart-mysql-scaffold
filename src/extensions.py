"""
Application extensions and shared instances.
"""
import redis.asyncio as redis
from quart import Quart
from quart_session import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.services.database_service import DatabaseService


# Database
Base = declarative_base()
db: DatabaseService = DatabaseService()

# Redis client
redis_client: redis.Redis = None

# Session management
session_manager: Session = Session()

# Database session factory
async_session_factory: sessionmaker = None


async def init_redis(app: Quart) -> redis.Redis:
    """Initialize Redis client."""
    redis_url = app.config.get('REDIS_URL')
    
    client = redis.from_url(
        redis_url,
        encoding='utf-8',
        decode_responses=True,
        max_connections=20,
        retry_on_timeout=True
    )
    
    # Test connection
    try:
        await client.ping()
        app.logger.info("Redis connection established")
    except Exception as e:
        app.logger.error(f"Redis connection failed: {e}")
        raise
    
    return client


async def init_database(app: Quart) -> None:
    """Initialize database connection."""
    global async_session_factory
    
    database_url = app.config.get('DATABASE_URL')
    
    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=app.config.get('DEBUG', False),
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "charset": "utf8mb4",
            "autocommit": True
        }
    )
    
    # Create session factory
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Initialize database service
    await db.init_app(app, engine)
    
    app.logger.info("Database connection established")


def init_extensions(app: Quart) -> None:
    """Initialize all extensions."""
    global redis_client
    
    # Initialize session manager
    session_manager.init_app(app)
    
    @app.before_serving
    async def setup_extensions():
        """Setup extensions that require async initialization."""
        global redis_client
        
        # Initialize Redis
        redis_client = await init_redis(app)
        
        # Initialize Database
        await init_database(app)
        
        # Set Redis client for sessions
        app.session_interface.redis = redis_client
    
    @app.after_serving
    async def cleanup_extensions():
        """Cleanup extensions on shutdown."""
        if redis_client:
            await redis_client.close()
        
        if db.engine:
            await db.engine.dispose()


async def get_db_session() -> AsyncSession:
    """Get database session."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized")
    
    return async_session_factory()


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    
    return redis_client