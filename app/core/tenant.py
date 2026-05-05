from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.security import decode_token


PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if any(request.url.path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # Auth endpoints are also public (no tenant needed)
        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid token"},
            )

        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        request.state.org_id = payload.get("org_id")
        request.state.user_id = payload.get("sub")
        request.state.role = payload.get("role", "user")

        return await call_next(request)
