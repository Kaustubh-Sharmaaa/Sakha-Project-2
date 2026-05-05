import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "name": email.split("@")[0],
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123",
    })
    return login_resp.json()["access_token"]


async def create_project(client: AsyncClient, token: str, name: str = "Test Project") -> str:
    resp = await client.post("/api/v1/projects/", json={"name": name}, headers={"Authorization": f"Bearer {token}"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    token = await get_token(client, "taskuser@example.com")
    project_id = await create_project(client, token)
    resp = await client.post("/api/v1/tasks/", json={
        "title": "Fix the bug",
        "description": "There is a bug in login",
        "project_id": project_id,
        "status": "todo",
        "priority": "high",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Fix the bug"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_task_invalid_project(client: AsyncClient):
    token = await get_token(client, "badtask@example.com")
    resp = await client.post("/api/v1/tasks/", json={
        "title": "Orphan Task",
        "project_id": "project:doesnotexist",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient):
    token = await get_token(client, "listtasks@example.com")
    project_id = await create_project(client, token)
    await client.post("/api/v1/tasks/", json={"title": "Task 1", "project_id": project_id}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/tasks/", json={"title": "Task 2", "project_id": project_id}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/api/v1/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_list_tasks_by_project(client: AsyncClient):
    token = await get_token(client, "filtertasks@example.com")
    project_a = await create_project(client, token, "Project A")
    project_b = await create_project(client, token, "Project B")
    await client.post("/api/v1/tasks/", json={"title": "Task A", "project_id": project_a}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/tasks/", json={"title": "Task B", "project_id": project_b}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get(f"/api/v1/tasks/?project_id={project_a}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    tasks = resp.json()
    assert all(t["project_id"] == project_a for t in tasks)


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient):
    token = await get_token(client, "gettask@example.com")
    project_id = await create_project(client, token)
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Get Me", "project_id": project_id}, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    token = await get_token(client, "updatetask@example.com")
    project_id = await create_project(client, token)
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Old Title", "status": "todo", "project_id": project_id}, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New Title", "status": "done"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["status"] == "done"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    token = await get_token(client, "deletetask@example.com")
    project_id = await create_project(client, token)
    create_resp = await client.post("/api/v1/tasks/", json={"title": "To Delete", "project_id": project_id}, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_task_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/tasks/", json={"title": "No Auth Task", "project_id": "project:fake"})
    assert resp.status_code == 401
