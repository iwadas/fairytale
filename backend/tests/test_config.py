"""AppSettings: defaults, env overrides, and secret handling."""

from pathlib import Path

from pydantic import SecretStr

from app.core.config import BACKEND_DIR, REPO_ROOT, AppSettings

ENV_VARS = [
    "DATABASE_URL", "SQL_ECHO", "CORS_ORIGINS", "LOG_LEVEL", "STATIC_DIR",
    "SCENE_VIDEO_DIR", "SCENE_IMAGE_DIR", "MUSIC_DIR", "VOICEOVER_DIR", "RENDER_OUTPUT_DIR",
    "REMOTION_APP_DIR", "OPENAI_API_KEY", "XAI_API_KEY", "GROQ_API_KEY", "RUNWARE_API_KEY",
    "XAI_BASE_URL",
]


def _isolated(monkeypatch, **env) -> AppSettings:
    """Build settings from a clean environment, ignoring backend/.env."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return AppSettings(_env_file=None)


def test_defaults(monkeypatch):
    s = _isolated(monkeypatch)
    assert s.database_url == "sqlite+aiosqlite:///./film.db"
    assert s.sync_database_url == "sqlite:///./film.db"
    assert s.sql_echo is False
    assert s.cors_origins == ["*"]
    assert s.log_level == "INFO"
    assert s.static_dir == "static"
    assert s.scene_video_dir == "static/videos/scenes"
    assert s.scene_image_dir == "static/images/scenes"
    assert s.music_dir == "static/music"
    assert s.voiceover_dir == "voiceovers"
    assert s.render_output_dir == "videos"
    assert s.remotion_app_dir == REPO_ROOT / "services" / "render-engine" / "remotion-app"
    assert s.xai_base_url == "https://api.x.ai/v1"
    for key in (s.openai_api_key, s.xai_api_key, s.groq_api_key, s.runware_api_key):
        assert key is None


def test_paths_are_anchored_to_backend_dir():
    assert (BACKEND_DIR / "app" / "core" / "config.py").is_file()
    assert REPO_ROOT == BACKEND_DIR.parent


def test_env_override(monkeypatch):
    s = _isolated(
        monkeypatch,
        DATABASE_URL="sqlite+aiosqlite:///./other.db",
        SQL_ECHO="true",
        CORS_ORIGINS='["http://localhost:5173"]',
        LOG_LEVEL="DEBUG",
        SCENE_VIDEO_DIR="media/videos",
        REMOTION_APP_DIR="/opt/remotion",
    )
    assert s.database_url == "sqlite+aiosqlite:///./other.db"
    assert s.sync_database_url == "sqlite:///./other.db"
    assert s.sql_echo is True
    assert s.cors_origins == ["http://localhost:5173"]
    assert s.log_level == "DEBUG"
    assert s.scene_video_dir == "media/videos"
    assert s.remotion_app_dir == Path("/opt/remotion")


def test_secrets_do_not_leak(monkeypatch):
    secret = "sk-super-secret-value"
    s = _isolated(monkeypatch, OPENAI_API_KEY=secret, RUNWARE_API_KEY=secret)
    assert isinstance(s.openai_api_key, SecretStr)
    assert isinstance(s.runware_api_key, SecretStr)
    assert s.openai_api_key.get_secret_value() == secret
    assert secret not in repr(s)
    assert secret not in str(s)
    assert secret not in repr(s.openai_api_key)
