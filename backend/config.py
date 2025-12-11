"""
Configuration and Settings
إعدادات النظام المركزية
"""
import os
from typing import Optional

class Settings:
    """إعدادات التطبيق"""
    
    # Application
    APP_NAME: str = "Smart Security System - Absher"
    APP_VERSION: str = "2.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_PATH: str = "security_system.db"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-123456")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 128
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "app.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Production URLs
    PRODUCTION_URL: str = "https://syntrue-absher.onrender.com"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {".csv", ".pdf", ".jpg", ".png"}
    
    # Events Management
    MAX_PARTICIPANTS_PER_EVENT: int = 100000
    DEFAULT_SECURITY_LEVEL: str = "high"
    
    # Performance
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    REQUEST_TIMEOUT: int = 30  # seconds

# Singleton instance
settings = Settings()
