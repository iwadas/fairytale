from unittest import result
from xmlrpc import client
import time
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from typing import Optional
from dotenv import load_dotenv
import time
from datetime import datetime
import uuid
import json
import os
import requests
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from fastapi import Depends
from db import async_session_maker, Project, Scene, Character, Voiceover

# OpenAI
from openai import OpenAI
import instructor

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend origin
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

from routers.characters import router as characters_router
from routers.projects import router as projects_router
from routers.generators import router as generators_router
from routers.scenes import router as scenes_router
from routers.voiceovers import router as voiceovers_router

app.include_router(characters_router)
app.include_router(projects_router)
app.include_router(generators_router)
app.include_router(scenes_router)
app.include_router(voiceovers_router)