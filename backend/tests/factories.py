"""Test-data factories: insert ORM rows through a *sync* session.

Every factory commits, so the row is visible to the app (which uses its own
async engine on the same temp SQLite file). Pass any column as a keyword to
override the defaults.
"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Music, Project, Scene, SceneImage, Settings, Voiceover

CREATED_AT = datetime(2026, 1, 2, 3, 4, 5)


def _save(db: Session, row, overrides: dict):
    db.add(row)
    db.commit()
    # The ORM skips explicit None for columns with a Python default (it inserts the
    # default instead), so write requested NULLs with a follow-up UPDATE.
    nulls = [name for name, value in overrides.items() if value is None]
    if nulls:
        for name in nulls:
            setattr(row, name, None)
        db.commit()
    return row


def make_project(db: Session, **overrides) -> Project:
    values = {"name": "Test project", "type": "BASIC", "created_at": CREATED_AT}
    return _save(db, Project(**{**values, **overrides}), overrides)


def make_scene(db: Session, project: Project, **overrides) -> Scene:
    values = {
        "project_id": project.id,
        "start_time": 1.5,
        "duration": 3,
        "video_prompt": "slow pan",
        "video_src": "static/videos/scenes/a.mp4",
        "cut_start": 0.25,
        "cut_end": 0.5,
        "layer": 1,
    }
    return _save(db, Scene(**{**values, **overrides}), overrides)


def make_scene_image(db: Session, scene: Scene, **overrides) -> SceneImage:
    values = {
        "scene_id": scene.id,
        "time": "start",
        "prompt": "a lighthouse",
        "idea": "loneliness",
        "src": "static/images/scenes/a.png",
        "style": "engraving",
    }
    return _save(db, SceneImage(**{**values, **overrides}), overrides)


def make_voiceover(db: Session, project: Project, **overrides) -> Voiceover:
    values = {
        "project_id": project.id,
        "text": "Hello world.",
        "text_with_pauses": json.dumps([{"word": "Hello"}, {"word": "[PAUSE]"}]),
        "timestamps": json.dumps([{"word": "Hello", "start": 0.0, "end": 0.4}]),
        "src": "static/voiceovers/a.wav",
        "start_time": 0.0,
        "duration": 2.5,
        "cut_start": 0.0,
        "cut_end": 0.0,
        "layer": 3,
    }
    return _save(db, Voiceover(**{**values, **overrides}), overrides)


def make_music(db: Session, project: Project, **overrides) -> Music:
    values = {
        "project_id": project.id,
        "name": "theme.mp3",
        "src": "static/music/theme.mp3",
        "start_time": 0.0,
        "duration": 30.0,
        "cut_start": 0.0,
        "cut_end": 0.0,
        "layer": 4,
    }
    return _save(db, Music(**{**values, **overrides}), overrides)


def make_settings(db: Session, **overrides) -> Settings:
    values = {
        "selected_tts_provider": "gemini",
        "selected_llm_provider": "xai",
        "selected_diffusion_provider": "runware",
        "tts_provider_settings": json.dumps({"gemini": {"voice": "Kore"}}),
        "llm_provider_settings": json.dumps({"xai": {"ai_model": "grok"}}),
        "diffusion_provider_settings": json.dumps({"runware": {"model": "bytedance"}}),
        "selected_script_generation_template": "essay",
        "script_generation_templates": json.dumps({"essay": "Write an essay"}),
    }
    return _save(db, Settings(**{**values, **overrides}), overrides)
