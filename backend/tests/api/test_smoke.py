"""Read-only smoke tests against an empty (temp) database. No provider calls."""

import json

import pytest

from app.db.models import Project, Settings

SETTINGS_KEYS = {
    "id",
    "selected_tts_provider",
    "selected_llm_provider",
    "selected_diffusion_provider",
    "tts_provider_settings",
    "diffusion_provider_settings",
    "llm_provider_settings",
    "selected_script_generation_template",
    "script_generation_templates",
}


@pytest.fixture
def project(sync_db):
    row = Project(name="Smoke project", type="BASIC")
    sync_db.add(row)
    sync_db.commit()
    return {"id": row.id, "name": row.name}


@pytest.fixture
def settings_row(sync_db):
    row = Settings(
        selected_llm_provider="xai",
        llm_provider_settings=json.dumps({"xai": {"ai_model": "test-model"}}),
    )
    sync_db.add(row)
    sync_db.commit()
    return row.id


def test_list_projects_empty(client):
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects(client, project):
    response = client.get("/projects")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert {"id", "name", "type", "created_at", "thumbnail"} <= set(item)
    assert item["id"] == project["id"]
    assert item["name"] == project["name"]
    assert item["thumbnail"] is None


def test_get_project(client, project):
    response = client.get(f"/projects/{project['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == project["id"]
    assert body["name"] == project["name"]
    for relation in ("scenes", "voiceovers", "background_music"):
        assert body[relation] == []


def test_get_project_missing_returns_null(client):
    response = client.get("/projects/does-not-exist")
    assert response.status_code == 200
    assert response.json() is None


def test_get_settings_empty_returns_null(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json() is None


def test_get_settings(client, settings_row):
    response = client.get("/settings")
    assert response.status_code == 200
    body = response.json()
    assert SETTINGS_KEYS <= set(body)
    assert body["id"] == settings_row
    assert body["selected_llm_provider"] == "xai"
    assert body["llm_provider_settings"] == {"xai": {"ai_model": "test-model"}}
    assert body["tts_provider_settings"] == {}
