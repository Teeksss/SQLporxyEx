from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = ["/", "/docs", "/redoc", "/openapi.json", "/health", "/api/auth/login"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
        
        response = await call_next(request)
        return response