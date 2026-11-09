"""Shared pytest fixtures.

The app reads its configuration (app.core.config) and creates the DB engine at
import time, so the environment is prepared at the top of this module, BEFORE
anything from ``app`` is imported.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

# The app expects CWD = backend/ (static mount and media paths are CWD-relative).
os.chdir(BACKEND_DIR)

_TMP_DIR = Path(tempfile.mkdtemp(prefix="fairytaile-tests-"))
TEST_DB_PATH = _TMP_DIR / "test.db"

# Real env vars take precedence over backend/.env, so these win over local secrets.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SQL_ECHO"] = "false"
# Some legacy modules build OpenAI-compatible clients at import time and need a key
# to exist; tests never call providers, so a dummy value is enough.
os.environ["XAI_API_KEY"] = "test-dummy-key"
os.environ["OPENAI_API_KEY"] = "test-dummy-key"
for _name in ("GROQ_API_KEY", "RUNWARE_API_KEY"):
    os.environ.pop(_name, None)

from sqlalchemy import create_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: E402,F401  (registers all tables on Base.metadata)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Create the schema on the temp DB.

    Uses ``Base.metadata.create_all`` rather than Alembic: the migration chain
    cannot build an empty database from scratch (its first revision assumes
    pre-existing tables).
    """
    from app.db import session as db_session

    # Safety net: never create/clean tables anywhere but the temp test DB.
    assert db_session.DATABASE_URL == os.environ["DATABASE_URL"], db_session.DATABASE_URL
    assert TEST_DB_PATH.as_posix() in get_settings().sync_database_url

    engine = create_engine(get_settings().sync_database_url)
    Base.metadata.create_all(engine)
    engine.dispose()
    yield
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture
def sync_db():
    """A sync SQLAlchemy session on the test DB, for seeding/cleanup in tests."""
    from sqlalchemy.orm import Session

    engine = create_engine(get_settings().sync_database_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    """Empty every table after each test so tests stay independent."""
    yield
    engine = create_engine(get_settings().sync_database_url)
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    engine.dispose()


@pytest.fixture(scope="session")
def client(_schema):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


# --- Helpers for API tests -------------------------------------------------


@pytest.fixture
def reload(sync_db):
    """``reload(Model, id)``: re-read a row from the DB, bypassing the session cache."""

    def _reload(model, row_id):
        sync_db.expire_all()
        return sync_db.get(model, row_id)

    return _reload


@pytest.fixture
def rows(sync_db):
    """``rows(Model, **filters)``: all matching rows, freshly read from the DB."""

    def _rows(model, **filters):
        sync_db.expire_all()
        return sync_db.query(model).filter_by(**filters).all()

    return _rows


@pytest.fixture
def media_dirs(tmp_path, monkeypatch):
    """Redirect every media output directory to a temp dir (never write to static/)."""
    settings = get_settings()
    dirs = {}
    for name in ("scene_video_dir", "scene_image_dir", "music_dir", "voiceover_dir", "render_output_dir"):
        target = (tmp_path / name).as_posix()
        monkeypatch.setattr(settings, name, target)
        dirs[name] = target
    return dirs


@pytest.fixture
def fake_llm(monkeypatch):
    from app.ai.llm import LLM
    from tests.fakes import FakeLLM

    fake = FakeLLM()

    async def create(cls):
        return fake

    monkeypatch.setattr(LLM, "create", classmethod(create))
    return fake


@pytest.fixture
def fake_tts(monkeypatch):
    from app.ai.tts import TTS
    from tests.fakes import FakeTTS

    fake = FakeTTS()

    async def create(cls):
        return fake

    monkeypatch.setattr(TTS, "create", classmethod(create))
    return fake


@pytest.fixture
def fake_diffusion(monkeypatch):
    from app.ai.video_generation import Diffusion
    from tests.fakes import FakeDiffusion

    fake = FakeDiffusion()

    async def create(cls):
        return fake

    monkeypatch.setattr(Diffusion, "create", classmethod(create))
    return fake


@pytest.fixture
def render_recorder(monkeypatch):
    from app.pipeline.render.builder import VideoBuilder
    from tests.fakes import RenderRecorder

    recorder = RenderRecorder()
    monkeypatch.setattr(VideoBuilder, "build", lambda self: recorder.record(self))
    return recorder
