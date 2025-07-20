"""
Middleware for LogBERT Hadoop RCA API

This module contains custom middleware for logging, error handling,
and other cross-cutting concerns.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging and timing.
    """
    
    def __init__(self, app: ASGIApp, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = log_level.upper()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and response with logging.
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "content_length": request.headers.get("content-length", 0),
            }
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "response_size": response.headers.get("content-length", 0),
                }
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time_ms": round(process_time * 1000, 2),
                },
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling and response formatting.
    """
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Handle errors and format responses consistently.
        """
        try:
            response = await call_next(request)
            return response
            
        except ValueError as e:
            # Validation errors
            return JSONResponse(
                status_code=400,
                content={
                    "error": "ValidationError",
                    "detail": str(e),
                    "type": "validation_error",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except FileNotFoundError as e:
            # File not found errors
            return JSONResponse(
                status_code=404,
                content={
                    "error": "NotFound",
                    "detail": str(e),
                    "type": "not_found_error",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except PermissionError as e:
            # Permission errors
            return JSONResponse(
                status_code=403,
                content={
                    "error": "PermissionDenied",
                    "detail": str(e),
                    "type": "permission_error",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except TimeoutError as e:
            # Timeout errors
            return JSONResponse(
                status_code=408,
                content={
                    "error": "RequestTimeout",
                    "detail": str(e),
                    "type": "timeout_error",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except Exception as e:
            # Generic server errors
            error_detail = str(e) if self.debug else "An internal error occurred"
            error_type = type(e).__name__ if self.debug else "InternalError"
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "detail": error_detail,
                    "type": error_type,
                    "request_id": getattr(request.state, "request_id", None),
                }
            )


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security headers and basic protection.
    """
    
    def __init__(self, app: ASGIApp, enable_security_headers: bool = True):
        super().__init__(app)
        self.enable_security_headers = enable_security_headers
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers and perform basic security checks.
        """
        # Process request
        response = await call_next(request)
        
        # Add security headers
        if self.enable_security_headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        enable_rate_limiting: bool = True
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.enable_rate_limiting = enable_rate_limiting
        self.request_counts: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Apply rate limiting based on client IP.
        """
        if not self.enable_rate_limiting:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitExceeded",
                    "detail": f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                    "retry_after": 60,
                }
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than 1 minute."""
        cutoff_time = current_time - 60
        
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = {
                k: v for k, v in self.request_counts[ip].items()
                if v > cutoff_time
            }
            
            if not self.request_counts[ip]:
                del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited."""
        if client_ip not in self.request_counts:
            return False
        
        # Count requests in the last minute
        cutoff_time = current_time - 60
        recent_requests = sum(
            1 for timestamp in self.request_counts[client_ip].values()
            if timestamp > cutoff_time
        )
        
        return recent_requests >= self.requests_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting."""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        # Use UUID to handle multiple requests at same timestamp
        request_key = str(uuid.uuid4())
        self.request_counts[client_ip][request_key] = current_time
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """Get remaining requests for client."""
        if client_ip not in self.request_counts:
            return self.requests_per_minute
        
        cutoff_time = current_time - 60
        recent_requests = sum(
            1 for timestamp in self.request_counts[client_ip].values()
            if timestamp > cutoff_time
        )
        
        return max(0, self.requests_per_minute - recent_requests)


