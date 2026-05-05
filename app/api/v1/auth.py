from fastapi import APIRouter, HTTPException
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
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _uid(record_id) -> str:
    """Return LOCAL id (no table prefix) from a RecordID or 'table:local' string."""
    if hasattr(record_id, 'id'):
        return record_id.id  # RecordID.id is already local
    s = str(record_id)
    if ':' in s:
        return s.split(':', 1)[1]
    return s


@router.post("/register", status_code=201)
async def register(user_in: UserCreate):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE email = '{user_in.email}' LIMIT 1"
    )
    if result:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = "user"
    local_uid = uuid.uuid4().hex[:8]           # 'abc12345' — LOCAL id only
    local_org = user_in.org_id or uuid.uuid4().hex[:8]  # 'org12345' — LOCAL only

    await db.query(f"""
        CREATE user SET
            id = '{local_uid}',
            email = '{user_in.email}',
            name = '{user_in.name}',
            password_hash = '{get_password_hash(user_in.password)}',
            org_id = '{local_org}',
            role = '{role}',
            created_at = time::now()
    """)
    return {
        "id": f"user:{local_uid}",
        "email": user_in.email,
        "name": user_in.name,
        "org_id": f"org:{local_org}",
        "role": role,
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE email = '{credentials.email}' LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result[0]
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    local_uid = _uid(user["id"])
    local_org = _uid(user["org_id"])
    token_payload = {
        "sub": local_uid,
        "email": user["email"],
        "org_id": local_org,
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
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )
