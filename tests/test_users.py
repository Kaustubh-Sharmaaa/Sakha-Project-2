import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
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
async def test_list_users_admin(client: AsyncClient, admin_user: str):
    """Admin can list all users in their org."""
    resp = await client.get("/api/v1/users/", headers={
        "Authorization": f"Bearer {admin_user}",
    })
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_users_non_admin(client: AsyncClient, regular_user: str):
    """Non-admin cannot list users — gets 403."""
    resp = await client.get("/api/v1/users/", headers={
        "Authorization": f"Bearer {regular_user}",
    })
    assert resp.status_code == 403
