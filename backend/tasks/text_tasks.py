from worker import huey, async_session_maker
import asyncio
from typing import Any, Dict, List
from pydantic import BaseModel

from sqlalchemy import select
from db import Scene, SceneImage # ← your models + Base
from services import generate_video, filename_from_name  # your video generator

@huey.task()  # add retries=2, retry_delay=30 if you want auto-retry
def generate_text_task(
    client: Any,
    model: str,
    response_model: BaseModel,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
):
    print(f"Starting text generation task")  # ← you should see this in worker logs

    # This is the cleanest way in Python 3.7+
    result = asyncio.run(run_generate_text_task_async(client, model, response_model, messages, temperature))
    return result


async def run_generate_text_task_async(client: Any, model: str, response_model: BaseModel, messages: List[Dict[str, str]], temperature: float):
    """All the async code lives here"""
    async with async_session_maker() as session:
        async with session.begin():
            print(f"Sending request to text generation model {model}...")
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_model=response_model
            )
            print(f"Response received from model {model}.")
            result = response.choices[0].message.content
            return result
