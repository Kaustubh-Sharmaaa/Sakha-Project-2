import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.surrealdb import init_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Initialize DB before each test."""
    await init_db()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


def get_auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
