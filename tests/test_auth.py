import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "password123",
        "name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice"
    assert "org_id" in data
    assert "role" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {
        "email": "bob@example.com",
        "password": "password123",
        "name": "Bob",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "password123",
        "name": "Carol",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "carol@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dave@example.com",
        "password": "password123",
        "name": "Dave",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "dave@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "eve@example.com",
        "password": "password123",
        "name": "Eve",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "eve@example.com",
        "password": "password123",
    })
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert resp.status_code == 401
