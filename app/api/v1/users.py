from fastapi import APIRouter, HTTPException, Depends
from app.db.surrealdb import get_db
from app.models.schemas import UserOut
from app.core.auth import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])


def _full(record_id) -> str:
    if hasattr(record_id, 'id'):
        return f"{record_id.table_name}:{record_id.id}"
    s = str(record_id)
    return s if ':' in s else f"user:{s}"


@router.get("/me", response_model=UserOut)
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
        "id": _full(rec["id"]),
        "email": rec.get("email"),
        "name": rec.get("name"),
        "org_id": _full(rec["org_id"]),
        "role": rec.get("role"),
        "created_at": rec.get("created_at"),
    }


@router.get("/", response_model=list[UserOut])
async def list_users(user: dict = Depends(require_admin)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE org_id = '{user['org_id']}'"
    )
    return [
        {
            "id": _full(r["id"]),
            "email": r.get("email"),
            "name": r.get("name"),
            "org_id": _full(r["org_id"]),
            "role": r.get("role"),
            "created_at": r.get("created_at"),
        }
        for r in result
    ]
