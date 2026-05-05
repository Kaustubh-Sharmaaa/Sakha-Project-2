from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectOut
from app.core.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


def _v(val):
    return val.id if hasattr(val, 'id') else val


def _uid(rid):
    """Convert 'user:xxx' or 'xxx' → returns tuple of (table, local_id)."""
    if hasattr(rid, 'id'):
        return (rid.table_name, rid.id)
    if ':' in str(rid):
        parts = str(rid).split(':', 1)
        return (parts[0], parts[1])
    return (None, str(rid))


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(project_in: ProjectCreate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    project_id = f"project:{uuid.uuid4().hex[:8]}"
    result = await db.query(f"""
        CREATE project SET
            id = '{project_id}',
            name = '{project_in.name}',
            description = '{project_in.description or ''}',
            org_id = '{user['org_id']}',
            created_by = '{user['user_id']}',
            created_at = time::now()
        RETURN AFTER
    """)
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _v(rec["org_id"]),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.get("/", response_model=list[ProjectOut])
async def list_projects(user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM project WHERE org_id = '{user['org_id']}'"
    )
    return [
        {
            "id": _v(r["id"]),
            "name": r.get("name"),
            "description": r.get("description"),
            "org_id": _v(r["org_id"]),
            "created_by": _v(r["created_by"]),
            "created_at": r.get("created_at"),
        }
        for r in result
    ]


def _build_id_cond(field: str, record_id: str) -> str:
    """
    Build a SurrealDB WHERE id condition.
    Handles both 'project:xxx' and 'xxx' formats.
    Returns e.g. "id = project:abc" (unquoted record literal).
    """
    if ':' in record_id:
        table, local = record_id.split(':', 1)
        return f"{field} = {table}:{local}"
    # Assume project table prefix
    return f"{field} = project:{record_id}"


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    id_cond = _build_id_cond("id", project_id)
    result = await db.query(
        f"SELECT * FROM project WHERE {id_cond} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _v(rec["org_id"]),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, update_in: ProjectUpdate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    sets = []
    if update_in.name is not None:
        sets.append(f"name = '{update_in.name}'")
    if update_in.description is not None:
        sets.append(f"description = '{update_in.description}'")

    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")

    id_cond = _build_id_cond("id", project_id)
    result = await db.query(
        f"UPDATE project SET {', '.join(sets)} "
        f"WHERE {id_cond} AND org_id = '{user['org_id']}' "
        f"RETURN AFTER"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _v(rec["org_id"]),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    id_cond = _build_id_cond("id", project_id)
    await db.query(
        f"DELETE FROM project WHERE {id_cond} AND org_id = '{user['org_id']}'"
    )
