from fastapi import APIRouter, HTTPException, Request, status
from app.db.surrealdb import get_db
from app.models.schemas import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


def require_admin(request: Request):
    if request.state.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/me", response_model=UserOut)
async def get_me(request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE id = '{request.state.user_id}' LIMIT 1"
    )
    data = result[0].get("result", [])
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data[0]


@router.get("/", response_model=list[UserOut])
async def list_users(request: Request):
    require_admin(request)
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM user WHERE org_id = '{request.state.org_id}'"
    )
    return result[0].get("result", [])
