"""
Database service for managing connections and operations.
"""
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

from quart import Quart, current_app
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from src.services.logging_service import get_logger


class DatabaseService:
    """Database service for managing connections and operations."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.logger = get_logger(__name__)
    
    async def init_app(self, app: Quart, engine: AsyncEngine) -> None:
        """Initialize the database service with the app."""
        self.engine = engine
        app.db = self
        
        # Create tables
        await self.create_all()
    
    async def create_all(self) -> None:
        """Create all database tables."""
        try:
            from src.extensions import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_all(self) -> None:
        """Drop all database tables."""
        try:
            from src.extensions import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            self.logger.info("Database tables dropped successfully")
        except Exception as e:
            self.logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get a database session with automatic cleanup."""
        from src.extensions import async_session_factory
        
        if not async_session_factory:
            raise RuntimeError("Database session factory not initialized")
        
        session = async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results."""
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except SQLAlchemyError as e:
            self.logger.error(f"Raw query execution failed: {e}")
            raise
    
    async def execute_raw_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a raw SQL command and return affected rows count."""
        try:
            async with self.get_session() as session:
                result = await session.execute(text(command), params or {})
                return result.rowcount
        except SQLAlchemyError as e:
            self.logger.error(f"Raw command execution failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        try:
            query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = :table_name
            AND TABLE_SCHEMA = DATABASE()
            """
            
            result = await self.execute_raw_query(query, {"table_name": table_name})
            return {
                "table_name": table_name,
                "columns": result
            }
        except Exception as e:
            self.logger.error(f"Failed to get table info for {table_name}: {e}")
            raise
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats = {}
            
            # Get table count
            table_count_query = """
            SELECT COUNT(*) as table_count 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            """
            result = await self.execute_raw_query(table_count_query)
            stats["table_count"] = result[0]["table_count"] if result else 0
            
            # Get database size
            size_query = """
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            """
            result = await self.execute_raw_query(size_query)
            stats["size_mb"] = result[0]["size_mb"] if result else 0
            
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            raise