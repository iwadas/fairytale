"""Characterization tests for /settings (wire format + merge semantics)."""

import json

from app.db.models import Settings
from tests import factories as f
from tests.api import wire


def test_get_settings(client, sync_db):
    row = f.make_settings(sync_db, diffusion_provider_settings=None)

    response = client.get("/settings")

    assert response.status_code == 200
    assert response.json() == {
        "id": row.id,
        "selected_tts_provider": "gemini",
        "selected_llm_provider": "xai",
        "selected_diffusion_provider": "runware",
        "tts_provider_settings": {"gemini": {"voice": "Kore"}},
        "diffusion_provider_settings": {},
        "llm_provider_settings": {"xai": {"ai_model": "grok"}},
        "selected_script_generation_template": "essay",
        "script_generation_templates": {"essay": "Write an essay"},
    }


def test_get_settings_empty(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json() is None


def test_update_settings_creates_row(client, rows):
    response = client.put(
        "/settings",
        json={
            "selected_llm_provider": "openai",
            "llm_provider_settings": {"ai_model": "gpt"},
            "script_generation_templates": {"a": "A", "b": None},
        },
    )

    assert response.status_code == 200
    (row,) = rows(Settings)
    # The row is serialized before the INSERT, so its generated id is not known yet.
    assert response.json() == {
        "message": "Settings updated successfully",
        "settings": {**wire.settings(row), "id": None},
    }
    assert row.selected_llm_provider == "openai"
    assert json.loads(row.llm_provider_settings) == {"openai": {"ai_model": "gpt"}}
    assert json.loads(row.script_generation_templates) == {"a": "A"}
    assert (row.selected_tts_provider, row.tts_provider_settings) == (None, None)


def test_update_settings_merges_into_existing_row(client, sync_db, reload):
    row = f.make_settings(
        sync_db,
        tts_provider_settings=json.dumps({"gemini": {"voice": "Kore"}, "camb": {"voice": 1}}),
        script_generation_templates=json.dumps({"essay": "Write an essay", "old": "drop me"}),
    )

    response = client.put(
        "/settings",
        json={
            "selected_tts_provider": "camb",
            "tts_provider_settings": {"voice": 2},
            "selected_diffusion_provider": "other",
            "selected_script_generation_template": "story",
            "script_generation_templates": {"story": "Tell a story", "old": None},
        },
    )

    assert response.status_code == 200
    # An update returns a message dict under "settings" (audit B15).
    assert response.json() == {
        "message": "Settings updated successfully",
        "settings": {"message": "Settings updated successfully"},
    }
    updated = reload(Settings, row.id)
    assert updated.selected_tts_provider == "camb"
    assert json.loads(updated.tts_provider_settings) == {"gemini": {"voice": "Kore"}, "camb": {"voice": 2}}
    # Selecting a provider without settings stores None for it.
    assert updated.selected_diffusion_provider == "other"
    assert json.loads(updated.diffusion_provider_settings) == {"runware": {"model": "bytedance"}, "other": None}
    assert updated.selected_script_generation_template == "story"
    assert json.loads(updated.script_generation_templates) == {"essay": "Write an essay", "story": "Tell a story"}
    # Untouched fields stay as they were.
    assert updated.selected_llm_provider == "xai"
    assert json.loads(updated.llm_provider_settings) == {"xai": {"ai_model": "grok"}}


def test_update_settings_with_empty_body_is_a_noop(client, sync_db, reload):
    row = f.make_settings(sync_db)
    before = wire.settings(row)

    response = client.put("/settings", json={})

    assert response.status_code == 200
    assert wire.settings(reload(Settings, row.id)) == before
