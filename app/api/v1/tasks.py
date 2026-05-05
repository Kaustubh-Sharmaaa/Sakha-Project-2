from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import TaskCreate, TaskUpdate, TaskOut
from app.core.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _full(record_id) -> str:
    if hasattr(record_id, 'id'):
        return f"{record_id.table_name}:{record_id.id}"
    s = str(record_id)
    return s if ':' in s else f"task:{s}"


def _local(record_id, default_table: str) -> str:
    if hasattr(record_id, 'id'):
        return record_id.id
    s = str(record_id)
    if ':' in s:
        return s.split(':', 1)[1]
    return f"{default_table}:{s}"


def _proj_local(project_id: str) -> str:
    """Extract local project id from 'project:xxx' or 'xxx'."""
    if ':' in project_id:
        return project_id.split(':', 1)[1]
    return project_id


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(task_in: TaskCreate, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    proj_local = _proj_local(task_in.project_id)
    proj_result = await db.query(
        f"SELECT id FROM project WHERE id = project:{proj_local} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not proj_result:
        raise HTTPException(status_code=404, detail="Project not found in your organization")

    task_local = uuid.uuid4().hex[:8]
    task_in_proj_local = _proj_local(task_in.project_id)
    result = await db.query(f"""
        CREATE task SET
            id = '{task_local}',
            title = '{task_in.title}',
            description = '{task_in.description or ''}',
            project_id = '{task_in_proj_local}',
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
        "id": _full(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _full(rec["project_id"]),
        "org_id": _full(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _full(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.get("/", response_model=list[TaskOut])
async def list_tasks(user: dict = Depends(get_current_user), project_id: str | None = None):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    if project_id:
        proj_local = _proj_local(project_id)
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{user['org_id']}' AND project_id = project:{proj_local}"
        )
    else:
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{user['org_id']}'"
        )
    return [
        {
            "id": _full(r["id"]),
            "title": r.get("title"),
            "description": r.get("description"),
            "project_id": _full(r["project_id"]),
            "org_id": _full(r["org_id"]),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "assigned_to": r.get("assigned_to"),
            "created_by": _full(r["created_by"]),
            "created_at": r.get("created_at"),
        }
        for r in result
    ]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    local = task_id.split(':')[1] if ':' in task_id else task_id
    result = await db.query(
        f"SELECT * FROM task WHERE id = task:{local} AND org_id = '{user['org_id']}' LIMIT 1"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    rec = result[0]
    return {
        "id": _full(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _full(rec["project_id"]),
        "org_id": _full(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _full(rec["created_by"]),
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

    local = task_id.split(':')[1] if ':' in task_id else task_id
    result = await db.query(
        f"UPDATE task SET {', '.join(sets)} "
        f"WHERE id = task:{local} AND org_id = '{user['org_id']}' "
        f"RETURN AFTER"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    rec = result[0]
    return {
        "id": _full(rec["id"]),
        "title": rec.get("title"),
        "description": rec.get("description"),
        "project_id": _full(rec["project_id"]),
        "org_id": _full(rec["org_id"]),
        "status": rec.get("status"),
        "priority": rec.get("priority"),
        "assigned_to": rec.get("assigned_to"),
        "created_by": _full(rec["created_by"]),
        "created_at": rec.get("created_at"),
    }


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    local = task_id.split(':')[1] if ':' in task_id else task_id
    await db.query(
        f"DELETE FROM task WHERE id = task:{local} AND org_id = '{user['org_id']}'"
    )
