from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import TaskCreate, TaskUpdate, TaskOut
from app.core.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _v(val):
    return val.id if hasattr(val, 'id') else val


def _rec_id(rid: str, default_table: str) -> str:
    """Build 'table:local' from 'xxx' or 'table:xxx' input."""
    if ':' in rid:
        t, local = rid.split(':', 1)
        return f"{t}:{local}"
    return f"{default_table}:{rid}"


def _build_id_cond(field: str, record_id: str, default_table: str) -> str:
    """Build a SurrealDB id WHERE condition using unquoted record literal."""
    full = _rec_id(record_id, default_table)
    table, local = full.split(':', 1)
    return f"{field} = {table}:{local}"


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(task_in: TaskCreate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Verify project belongs to the same org
    proj_id_cond = _build_id_cond("id", task_in.project_id, "project")
    proj_result = await db.query(
        f"SELECT id FROM project WHERE {proj_id_cond} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not proj_result:
        raise HTTPException(status_code=404, detail="Project not found in your organization")

    task_id = f"task:{uuid.uuid4().hex[:8]}"
    result = await db.query(f"""
        CREATE task SET
            id = '{task_id}',
            title = '{task_in.title}',
            description = '{task_in.description or ''}',
            project_id = '{task_in.project_id}',
            org_id = '{user['org_id']}',
            status = '{task_in.status or 'todo'}',
            priority = '{task_in.priority or 'medium'}',
            assigned_to = null,
            created_by = '{user['user_id']}',
            created_at = time::now()
        RETURN AFTER
    """)
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _v(rec["project_id"]),
        "org_id": _v(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.get("/", response_model=list[TaskOut])
async def list_tasks(user: dict = Depends(get_current_user), project_id: str | None = None):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    if project_id:
        pid_cond = _build_id_cond("project_id", project_id, "project")
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{user['org_id']}' AND {pid_cond}"
        )
    else:
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{user['org_id']}'"
        )
    return [
        {
            "id": _v(r["id"]),
            "title": r.get("title"),
            "description": r.get("description"),
            "project_id": _v(r["project_id"]),
            "org_id": _v(r["org_id"]),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "assigned_to": r.get("assigned_to"),
            "created_by": _v(r["created_by"]),
            "created_at": r.get("created_at"),
        }
        for r in result
    ]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    id_cond = _build_id_cond("id", task_id, "task")
    result = await db.query(
        f"SELECT * FROM task WHERE {id_cond} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _v(rec["project_id"]),
        "org_id": _v(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, update_in: TaskUpdate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    sets = []
    if update_in.title is not None:
        sets.append(f"title = '{update_in.title}'")
    if update_in.description is not None:
        sets.append(f"description = '{update_in.description}'")
    if update_in.status is not None:
        sets.append(f"status = '{update_in.status}'")
    if update_in.priority is not None:
        sets.append(f"priority = '{update_in.priority}'")

    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")

    id_cond = _build_id_cond("id", task_id, "task")
    result = await db.query(
        f"UPDATE task SET {', '.join(sets)} "
        f"WHERE {id_cond} AND org_id = '{user['org_id']}' "
        f"RETURN AFTER"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    rec = result[0]
    return {
        "id": _v(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _v(rec["project_id"]),
        "org_id": _v(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _v(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    id_cond = _build_id_cond("id", task_id, "task")
    await db.query(
        f"DELETE FROM task WHERE {id_cond} AND org_id = '{user['org_id']}'"
    )
