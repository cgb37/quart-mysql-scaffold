"""
Application configuration management.
"""
import os
from typing import Dict, Type
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class BaseConfig(BaseSettings):
    """Base configuration class."""
    
    # Application
    QUART_ENV: str = Field(default='development')
    SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex())
    DEBUG: bool = False
    TESTING: bool = False
    
    # Database
    DB_HOST: str = Field(default='localhost')
    DB_PORT: int = Field(default=3306)
    DB_NAME: str = Field(default='quart_db')
    DB_USER: str = Field(default='quart_user')
    DB_PASSWORD: str = Field(default='quart_password')
    DATABASE_URL: str = Field(default='')
    
    # Redis
    REDIS_HOST: str = Field(default='localhost')
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default='')
    REDIS_URL: str = Field(default='')
    
    # Security
    JWT_SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex())
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(default=3600)  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(default=2592000)  # 30 days
    
    # Session
    SESSION_TYPE: str = Field(default='redis')
    SESSION_PERMANENT: bool = Field(default=False)
    SESSION_USE_SIGNER: bool = Field(default=True)
    SESSION_KEY_PREFIX: str = Field(default='quart_session:')
    SESSION_REDIS: str = Field(default='')
    
    # Logging
    LOG_LEVEL: str = Field(default='INFO')
    LOG_FORMAT: str = Field(default='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_FILE: str = Field(default='logs/app.log')
    
    # Security Headers
    SECURITY_HEADERS: bool = Field(default=True)
    CORS_ORIGINS: str = Field(default='*')
    
    # Rate Limiting
    RATELIMIT_ENABLED: bool = Field(default=True)
    RATELIMIT_DEFAULT: str = Field(default='100 per hour')
    
    # File Upload
    MAX_CONTENT_LENGTH: int = Field(default=16 * 1024 * 1024)  # 16MB
    UPLOAD_FOLDER: str = Field(default='uploads')
    
    # SMTP Configuration
    SMTP_SERVER: str = Field(default='')
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default='')
    SMTP_PASSWORD: str = Field(default='')
    
    @validator('DATABASE_URL', pre=True, always=True)
    def assemble_database_url(cls, v, values):
        """Construct database URL from components."""
        if v:
            # If URL is provided, ensure it uses async driver
            if 'mysql+pymysql://' in v:
                return v.replace('mysql+pymysql://', 'mysql+aiomysql://')
            return v
        
        user = quote_plus(values.get('DB_USER', ''))
        password = quote_plus(values.get('DB_PASSWORD', ''))
        host = values.get('DB_HOST', 'localhost')
        port = values.get('DB_PORT', 3306)
        db_name = values.get('DB_NAME', 'quart_db')
        
        return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{db_name}"
    
    @validator('REDIS_URL', pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        """Construct Redis URL from components."""
        if v:
            return v
        
        host = values.get('REDIS_HOST', 'localhost')
        port = values.get('REDIS_PORT', 6379)
        db = values.get('REDIS_DB', 0)
        password = values.get('REDIS_PASSWORD', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    @validator('SESSION_REDIS', pre=True, always=True)
    def set_session_redis(cls, v, values):
        """Set Redis URL for sessions."""
        return v or values.get('REDIS_URL', '')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'allow'  # Allow extra fields for flexibility


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG: bool = True
    LOG_LEVEL: str = 'DEBUG'
    
    class Config:
        env_prefix = 'DEV_'


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = 'INFO'
    
    # Security
    SECURITY_HEADERS: bool = True
    CORS_ORIGINS: str = ''  # Restrict in production
    
    # Rate Limiting
    RATELIMIT_DEFAULT: str = '60 per hour'
    
    class Config:
        env_prefix = 'PROD_'


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING: bool = True
    DEBUG: bool = True
    
    # Use in-memory SQLite for testing
    DATABASE_URL: str = 'sqlite:///:memory:'
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED: bool = False
    
    class Config:
        env_prefix = 'TEST_'


# Configuration mapping
CONFIG_MAP: Dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config(config_name: str = 'development') -> BaseConfig:
    """Get configuration instance by name."""
    config_class = CONFIG_MAP.get(config_name, DevelopmentConfig)
    return config_class()