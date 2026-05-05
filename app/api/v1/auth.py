from fastapi import APIRouter, HTTPException, status
from app.db.surrealdb import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    RefreshRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
async def register(user_in: UserCreate):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Check if user exists
    existing = await db.query(
        f"SELECT * FROM user WHERE email = '{user_in.email}' LIMIT 1"
    )
    if existing and existing[0].get("result"):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Set default role; only admins can create users in other orgs
    role = "admin" if not user_in.org_id else "user"
    import uuid
    user_id = f"user:{uuid.uuid4().hex[:8]}"
    org_id = user_in.org_id or f"org:{uuid.uuid4().hex[:8]}"

    result = await db.query(f"""
        CREATE user SET
            id = '{user_id}',
            email = '{user_in.email}',
            name = '{user_in.name}',
            password_hash = '{get_password_hash(user_in.password)}',
            org_id = '{org_id}',
            role = '{role}',
            created_at = time::now()
    """)
    result_data = result[0].get("result", [{}])[0]

    return {
        "id": result_data.get("id"),
        "email": result_data.get("email"),
        "name": result_data.get("name"),
        "org_id": result_data.get("org_id"),
        "role": result_data.get("role"),
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE email = '{credentials.email}' LIMIT 1"
    )
    result_data = result[0].get("result", [])
    if not result_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result_data[0]
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_payload = {
        "sub": user["id"],
        "email": user["email"],
        "org_id": user["org_id"],
        "role": user["role"],
    }
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_payload = {
        "sub": payload["sub"],
        "email": payload["email"],
        "org_id": payload["org_id"],
        "role": payload["role"],
    }
    return TokenResponse(
        access_token=create_access_token(new_payload),
        refresh_token=create_refresh_token(new_payload),
    )
