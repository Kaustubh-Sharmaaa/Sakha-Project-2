from fastapi import Depends, HTTPException, Request
import jwt
from app.core.security import ALGORITHM, SECRET_KEY

ALGORITHM = "HS256"
SECRET_KEY = "sakha-secret-key-change-in-production-2024"


def get_token_from_header(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return auth_header.split(" ", 1)[1]


def get_current_user(request: Request) -> dict:
    """Decodes JWT, validates it, returns user dict with org_id/user_id/role."""
    token = get_token_from_header(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role", "user")

    if not sub or not org_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {
        "user_id": sub,        # LOCAL id, e.g. 'abc12345'
        "org_id": org_id,      # LOCAL id, e.g. 'def67890'
        "role": role,
    }


def require_admin(request: Request) -> dict:
    user = get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
