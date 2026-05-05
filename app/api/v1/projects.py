from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectOut
from app.core.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


def _full(record_id) -> str:
    """Convert RecordID or 'local' string to 'table:local' format."""
    if hasattr(record_id, 'id'):
        return f"{record_id.table_name}:{record_id.id}"
    s = str(record_id)
    if ':' in s:
        return s
    return f"project:{s}"


def _local(record_id) -> str:
    """Extract local id from RecordID or 'table:local' string."""
    if hasattr(record_id, 'id'):
        return record_id.id
    s = str(record_id)
    return s.split(':', 1)[1] if ':' in s else s


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(project_in: ProjectCreate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    project_id = uuid.uuid4().hex[:8]   # LOCAL id only
    await db.query(f"""
        CREATE project SET
            id = '{project_id}',
            name = '{project_in.name}',
            description = '{project_in.description or ''}',
            org_id = '{user['org_id']}',
            created_by = '{user['user_id']}',
            created_at = time::now()
    """)
    result = await db.query(
        f"SELECT * FROM project WHERE id = project:{project_id} LIMIT 1"
    )
    rec = result[0]
    return {
        "id": _full(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _full(rec["org_id"]),
        "created_by": _full(rec["created_by"]),
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
            "id": _full(r["id"]),
            "name": r.get("name"),
            "description": r.get("description"),
            "org_id": _full(r["org_id"]),
            "created_by": _full(r["created_by"]),
            "created_at": r.get("created_at"),
        }
        for r in result
    ]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    local = project_id.split(':')[1] if ':' in project_id else project_id
    result = await db.query(
        f"SELECT * FROM project WHERE id = project:{local} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    rec = result[0]
    return {
        "id": _full(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _full(rec["org_id"]),
        "created_by": _full(rec["created_by"]),
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

    local = project_id.split(':')[1] if ':' in project_id else project_id
    result = await db.query(
        f"UPDATE project SET {', '.join(sets)} "
        f"WHERE id = project:{local} AND org_id = '{user['org_id']}' "
        f"RETURN AFTER"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    rec = result[0]
    return {
        "id": _full(rec["id"]),
        "name": rec.get("name"),
        "description": rec.get("description"),
        "org_id": _full(rec["org_id"]),
        "created_by": _full(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    local = project_id.split(':')[1] if ':' in project_id else project_id
    await db.query(
        f"DELETE FROM project WHERE id = project:{local} AND org_id = '{user['org_id']}'"
    )
