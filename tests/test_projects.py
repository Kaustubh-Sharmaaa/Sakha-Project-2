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


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    token = await get_token(client, "projuser@example.com")
    resp = await client.post("/api/v1/projects/", json={
        "name": "My Project",
        "description": "A test project",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert data["description"] == "A test project"
    assert "id" in data
    assert "org_id" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    token = await get_token(client, "listproj@example.com")
    await client.post("/api/v1/projects/", json={"name": "Project A"}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/projects/", json={"name": "Project B"}, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    token = await get_token(client, "getproj@example.com")
    create_resp = await client.post("/api/v1/projects/", json={"name": "Get Test"}, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    token = await get_token(client, "notfoundproj@example.com")
    resp = await client.get("/api/v1/projects/project:doesnotexist", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    token = await get_token(client, "updateproj@example.com")
    create_resp = await client.post("/api/v1/projects/", json={"name": "Old Name"}, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/projects/{project_id}", json={"name": "New Name"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    token = await get_token(client, "deleteproj@example.com")
    create_resp = await client.post("/api/v1/projects/", json={"name": "To Delete"}, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    # Verify deleted
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_project_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/projects/", json={"name": "No Auth Project"})
    assert resp.status_code == 401
