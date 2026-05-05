from fastapi import Depends, HTTPException, Request, status

ALGORITHM = "HS256"
SECRET_KEY = "sakha-secret-key-change-in-production-2024"


def get_token_from_header(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return auth_header.split(" ", 1)[1]


def get_current_user(request: Request) -> dict:
    """
    Decodes JWT, validates it, and returns user dict with org_id/user_id/role.
    """
    import jwt
    token = get_token_from_header(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    org_id = payload.get("org_id")
    user_id = payload.get("sub")
    role = payload.get("role", "user")
    
    if not org_id or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {
        "org_id": org_id,
        "user_id": user_id,
        "role": role,
    }


def require_admin(request: Request) -> dict:
    """Require admin role. Use as Depends(require_admin)."""
    user = get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
