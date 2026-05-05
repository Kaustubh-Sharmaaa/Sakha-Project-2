from fastapi import APIRouter, HTTPException, Request, status
import uuid
from app.db.surrealdb import get_db
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectOut

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(project_in: ProjectCreate, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    project_id = f"project:{uuid.uuid4().hex[:8]}"
    result = await db.query(f"""
        CREATE project SET
            id = '{project_id}',
            name = '{project_in.name}',
            description = '{project_in.description or ''}',
            org_id = '{request.state.org_id}',
            created_by = '{request.state.user_id}',
            created_at = time::now()
    """)
    data = result[0].get("result", [{}])[0]
    return data


@router.get("/", response_model=list[ProjectOut])
async def list_projects(request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM project WHERE org_id = '{request.state.org_id}'"
    )
    return result[0].get("result", [])


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db.query(
        f"SELECT * FROM project WHERE id = '{project_id}' AND org_id = '{request.state.org_id}' LIMIT 1"
    )
    data = result[0].get("result", [])
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data[0]


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, update_in: ProjectUpdate, request: Request):
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

    result = await db.query(
        f"UPDATE project SET {', '.join(sets)} "
        f"WHERE id = '{project_id}' AND org_id = '{request.state.org_id}' "
        f"RETURN AFTER"
    )
    data = result[0].get("result", [])
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data[0]


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, request: Request):
    db = await get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    await db.query(
        f"DELETE FROM project WHERE id = '{project_id}' AND org_id = '{request.state.org_id}'"
    )
