from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from .security import decode_token

# Simple in-memory store for demo. In production, use Redis or DB.
tenant_context = {}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip tenant check for auth endpoints
        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Attach tenant info to request state
        request.state.org_id = payload.get("org_id")
        request.state.user_id = payload.get("sub")
        request.state.role = payload.get("role", "user")

        return await call_next(request)
