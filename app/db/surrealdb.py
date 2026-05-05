import surrealdb
from app.core.config import get_settings

settings = get_settings()
db = None


async def init_db():
    global db
    db = surrealdb.Surreal()
    await db.connect(settings.surrealdb_url)
    await db.use("test", "test")
    return db


async def get_db():
    return db
