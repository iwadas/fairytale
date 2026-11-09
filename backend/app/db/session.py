from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_settings = get_settings()

DATABASE_URL = _settings.database_url

engine = create_async_engine(DATABASE_URL, echo=_settings.sql_echo, future=True)

async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
