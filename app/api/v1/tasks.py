from fastapi import APIRouter, HTTPException, Request, status
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(task_in: TaskCreate, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    # Verify project belongs to the same org
    proj_result = await db.query(
        f"SELECT id FROM project WHERE id = '{task_in.project_id}' AND org_id = '{request.state.org_id}' LIMIT 1"
    )
    if not proj_result[0].get("result"):
        raise HTTPException(status_code=404, detail="Project not found in your organization")

    task_id = f"task:{uuid.uuid4().hex[:8]}"
    result = await db.query(f"""
        CREATE task SET
            id = '{task_id}',
            title = '{task_in.title}',
            description = '{task_in.description or ''}',
            project_id = '{task_in.project_id}',
            org_id = '{request.state.org_id}',
            status = '{task_in.status or 'todo'}',
            priority = '{task_in.priority or 'medium'}',
            assigned_to = null,
            created_by = '{request.state.user_id}',
            created_at = time::now()
    """)
    data = result[0].get("result", [{}])[0]
    return data


@router.get("/", response_model=list[TaskOut])
async def list_tasks(request: Request, project_id: str | None = None):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    if project_id:
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{request.state.org_id}' AND project_id = '{project_id}'"
        )
    else:
        result = await db.query(
            f"SELECT * FROM task WHERE org_id = '{request.state.org_id}'"
        )
    return result[0].get("result", [])


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM task WHERE id = '{task_id}' AND org_id = '{request.state.org_id}' LIMIT 1"
    )
    data = result[0].get("result", [])
    if not data:
        raise HTTPException(status_code=404, detail="Task not found")
    return data[0]


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, update_in: TaskUpdate, request: Request):
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

    result = await db.query(
        f"UPDATE task SET {', '.join(sets)} "
        f"WHERE id = '{task_id}' AND org_id = '{request.state.org_id}' "
        f"RETURN AFTER"
    )
    data = result[0].get("result", [])
    if not data:
        raise HTTPException(status_code=404, detail="Task not found")
    return data[0]


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    await db.query(
        f"DELETE FROM task WHERE id = '{task_id}' AND org_id = '{request.state.org_id}'"
    )
