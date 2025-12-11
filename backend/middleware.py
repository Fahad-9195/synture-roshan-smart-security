"""
Custom Middleware
معالجات مخصصة للطلبات
"""
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
from logger import log_api_call, log_error

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """معالج الأخطاء المركزي"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            log_error(e, context=f"{request.method} {request.url.path}")
            
            # Return user-friendly error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "حدث خطأ في الخادم، يرجى المحاولة لاحقاً",
                    "detail": str(e) if logger.level == logging.DEBUG else None
                }
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """تسجيل جميع الطلبات"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the request
        log_api_call(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=duration
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """معالج تحديد عدد الطلبات (Rate Limiting)"""
    
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}  # {ip: [(timestamp, count)]}
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if current_time - ts < self.window
            ]
        
        # Count requests in window
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        request_count = sum(count for _, count in self.requests[client_ip])
        
        # Check rate limit
        if request_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "message": "تم تجاوز الحد المسموح من الطلبات، يرجى الانتظار"
                }
            )
        
        # Add current request
        self.requests[client_ip].append((current_time, 1))
        
        # Process request
        response = await call_next(request)
        return response

class CacheMiddleware(BaseHTTPMiddleware):
    """معالج التخزين المؤقت للطلبات"""
    
    def __init__(self, app, ttl: int = 300):
        super().__init__(app)
        self.ttl = ttl
        self.cache = {}  # {url: (response, timestamp)}
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Create cache key
        cache_key = str(request.url)
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.ttl:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            self.cache[cache_key] = (response, current_time)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """إضافة رؤوس الأمان"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
