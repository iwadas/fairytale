from huey import SqliteHuey
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

# ── Global engine & session factory ──
# IMPORTANT: use the same DATABASE_URL as in your main FastAPI app!
DATABASE_URL = "sqlite+aiosqlite:///./film.db"  # ← adjust to your real URL
# For postgres → "postgresql+asyncpg://user:pass@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,                     # set True only for debugging
    future=True,
    # connect_args={"check_same_thread": False}  # only needed for plain sqlite (not aiosqlite)
)

# Factory for creating new AsyncSession instances
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,         # Very useful: prevents unwanted expires after commit
    autoflush=True,
)

# Huey instance (SQLite backend)
huey = SqliteHuey(
    name="my_fastapi_app",
    filename="queue.db",
    results=True,
    store_none=False,
)