import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    # Register + login
    await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "password": "password123",
        "name": "Me",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "me@example.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_users_admin(client: AsyncClient):
    # Register admin
    await client.post("/api/v1/auth/register", json={
        "email": "admin2@example.com",
        "password": "password123",
        "name": "Admin Two",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "admin2@example.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/users/", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_users_non_admin(client: AsyncClient):
    # Register + login (default user role)
    await client.post("/api/v1/auth/register", json={
        "email": "regular@example.com",
        "password": "password123",
        "name": "Regular User",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "regular@example.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/users/", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 403
