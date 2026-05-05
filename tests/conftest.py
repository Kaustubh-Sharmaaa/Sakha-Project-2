import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.surrealdb import init_db, get_db
from app.core.security import create_access_token, get_password_hash


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    await init_db()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(client: AsyncClient):
    """
    Create an admin user directly in the DB (bypasses register role logic)
    and return a valid JWT token.
    """
    db = await get_db()
    local_uid = uuid.uuid4().hex[:8]
    local_org = uuid.uuid4().hex[:8]
    await db.query(f"""
        CREATE user SET
            id = '{local_uid}',
            email = 'admin@test.com',
            name = 'Admin User',
            password_hash = '{get_password_hash("adminpass")}',
            org_id = '{local_org}',
            role = 'admin',
            created_at = time::now()
    """)
    token = create_access_token({
        "sub": local_uid,
        "email": "admin@test.com",
        "org_id": local_org,
        "role": "admin",
    })
    return token


@pytest_asyncio.fixture
async def regular_user(client: AsyncClient):
    """Create a regular non-admin user and return token."""
    await client.post("/api/v1/auth/register", json={
        "email": "regular@test.com",
        "password": "regularpass",
        "name": "Regular User",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "regular@test.com",
        "password": "regularpass",
    })
    return resp.json()["access_token"]
