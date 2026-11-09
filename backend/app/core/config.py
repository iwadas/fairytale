"""Application configuration: the single source of environment-driven settings.

Values come from (highest precedence first) real environment variables,
then ``backend/.env``, then the defaults below. See ``backend/.env.example``.

Note: provider credentials stored in the database (the ``Settings`` model,
edited from the UI) are separate from this class; call sites decide which
source wins for each provider.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Filesystem anchors derived once from this file's location.
BACKEND_DIR = Path(__file__).resolve().parents[2]  # .../backend
REPO_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    # Relative SQLite paths resolve against the CWD (run the app from backend/).
    database_url: str = "sqlite+aiosqlite:///./film.db"
    sql_echo: bool = False

    # --- HTTP ---
    cors_origins: list[str] = ["*"]

    # --- Logging ---
    log_level: str = "INFO"

    # --- Static files / media output directories ---
    # CWD-relative strings on purpose: generated paths are stored in the DB and
    # served under /static as-is, so they must keep their current form.
    static_dir: str = "static"
    scene_video_dir: str = "static/videos/scenes"
    scene_image_dir: str = "static/images/scenes"
    music_dir: str = "static/music"
    voiceover_dir: str = "voiceovers"
    render_output_dir: str = "videos"  # final rendered project videos

    # --- External tools ---
    remotion_app_dir: Path = REPO_ROOT / "services" / "render-engine" / "remotion-app"

    # --- Provider API keys read from the environment ---
    openai_api_key: SecretStr | None = None
    xai_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    runware_api_key: SecretStr | None = None

    # --- Third-party endpoints ---
    xai_base_url: str = "https://api.x.ai/v1"

    @property
    def sync_database_url(self) -> str:
        """Database URL with the async driver swapped for a sync one (for Alembic)."""
        return self.database_url.replace("+aiosqlite", "")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
