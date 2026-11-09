"""FastAPI dependencies shared by the routers."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker


async def get_session() -> AsyncIterator[AsyncSession]:
    """One AsyncSession per request.

    Services own the transaction (they commit once per use-case); anything not
    committed is rolled back when the session closes.
    """
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
