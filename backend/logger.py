"""
Logging Configuration
نظام تسجيل الأحداث المحترف
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import settings

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory if not exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_dir / settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

def log_api_call(endpoint: str, method: str, status_code: int, duration: float):
    """Log API call details"""
    logger.info(
        f"API Call - {method} {endpoint} - Status: {status_code} - Duration: {duration:.3f}s"
    )

def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}", exc_info=True)

def log_security_event(event_type: str, user_id: int = None, details: str = ""):
    """Log security-related events"""
    logger.warning(f"Security Event - Type: {event_type} - User: {user_id} - Details: {details}")

def log_database_operation(operation: str, table: str, affected_rows: int = 0):
    """Log database operations"""
    logger.debug(f"DB Operation - {operation} on {table} - Affected rows: {affected_rows}")
