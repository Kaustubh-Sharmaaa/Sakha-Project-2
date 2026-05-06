from fastapi import APIRouter, HTTPException, Depends
from app.db.surrealdb import get_db
from app.core.auth import get_current_user, require_admin
from app.core.security import get_password_hash
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class UserDelete(BaseModel):
    user_id: Optional[str] = None

router = APIRouter(prefix="/users", tags=["Users"])


def _full(record_id) -> str:
    if hasattr(record_id, 'id'):
        return f"{record_id.table_name}:{record_id.id}"
    s = str(record_id)
    return s if ':' in s else f"user:{s}"


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE id = user:{user['user_id']} LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    rec = result[0]
    return {
        "success": True,
        "data": {
            "id": _full(rec["id"]),
            "email": rec.get("email"),
            "name": rec.get("name"),
            "orgId": rec.get("org_id"),
            "role": rec.get("role"),
        }
    }


@router.get("/")
async def list_users(user: dict = Depends(require_admin)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE org_id = '{user['org_id']}'"
    )
    return {
        "success": True,
        "data": [
            {
                "id": _full(r["id"]),
                "email": r.get("email"),
                "name": r.get("name"),
                "orgId": r.get("org_id"),
                "role": r.get("role"),
            }
            for r in result
        ]
    }


@router.post("/", status_code=201)
async def create_user(body: UserCreate, admin: dict = Depends(require_admin)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    existing = await db.query(
        f"SELECT * FROM user WHERE email = '{body.email}' LIMIT 1"
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    local_id = uuid.uuid4().hex[:8]
    # Admin-created users get a temporary password; they should reset via auth flow
    temp_password = get_password_hash(uuid.uuid4().hex)

    await db.query(f"""
        CREATE user SET
            id = '{local_id}',
            email = '{body.email}',
            name = '{body.name}',
            password_hash = '{temp_password}',
            org_id = '{admin['org_id']}',
            role = '{body.role}',
            created_at = time::now()
    """)
    return {
        "success": True,
        "data": {
            "id": f"user:{local_id}",
            "name": body.name,
            "email": body.email,
            "role": body.role,
            "orgId": admin["org_id"],
        }
    }


@router.patch("/{user_id}")
async def update_user(user_id: str, body: UserUpdate, admin: dict = Depends(require_admin)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    resolved_id = body.user_id if body.user_id else user_id
    local_id = resolved_id.split(":")[-1]

    existing = await db.query(
        f"SELECT * FROM user WHERE id = user:{local_id} AND org_id = '{admin['org_id']}' LIMIT 1"
    )
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    fields = {k: v for k, v in body.model_dump().items() if v is not None and k != "user_id"}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = '{v}'" for k, v in fields.items())
    await db.query(f"UPDATE user:{local_id} SET {set_clause}")

    updated = await db.query(
        f"SELECT * FROM user WHERE id = user:{local_id} LIMIT 1"
    )
    rec = updated[0]
    return {
        "success": True,
        "data": {
            "id": _full(rec["id"]),
            "email": rec.get("email"),
            "name": rec.get("name"),
            "orgId": rec.get("org_id"),
            "role": rec.get("role"),
        }
    }


@router.delete("/{user_id}")
async def delete_user(user_id: str, body: UserDelete = None, admin: dict = Depends(require_admin)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Body user_id takes precedence over path param
    resolved_id = (body.user_id if body and body.user_id else user_id)
    local_id = resolved_id.split(":")[-1]

    existing = await db.query(
        f"SELECT * FROM user WHERE id = user:{local_id} AND org_id = '{admin['org_id']}' LIMIT 1"
    )
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    await db.query(f"DELETE user:{local_id}")
    return {"success": True, "data": {"message": "User deleted"}}
