from functools import wraps
from .config import async_session_maker

def with_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 1. Check if a session was manually passed (for transactions)
        if "session" in kwargs and kwargs["session"] is not None:
            return await func(*args, **kwargs)
        
        # 2. If no session, create one automatically
        async with async_session_maker() as session:
            try:
                kwargs["session"] = session
                result = await func(*args, **kwargs)
                # Auto-commit if the function was successful
                await session.commit() 
                return result
            except Exception as e:
                await session.rollback() # Auto-rollback on error
                raise e
    return wrapper