"""Characterization tests for /voiceovers (wire format + DB side effects)."""

import json

import pytest

from app.db.models import Voiceover
from tests import factories as f
from tests.api import wire


def test_create_voiceover(client, sync_db, rows):
    project = f.make_project(sync_db)

    response = client.post(f"/voiceovers/{project.id}", json={"start_time": 3.0})

    assert response.status_code == 200
    (row,) = rows(Voiceover)
    body = response.json()
    body.pop("text_with_pauses")  # see test_create_voiceover_stores_null_text_with_pauses
    assert body == {
        "id": row.id,
        "project_id": project.id,
        "src": None,
        "text": "",
        "timestamps": [],
        "start_time": 3.0,
        "duration": 4.0,
        "cut_start": 0.0,
        "cut_end": 0.0,
        "layer": 3,
    }
    assert (row.text, row.start_time, row.duration, row.layer, row.timestamps) == ("", 3.0, 4.0, 3, None)


def test_create_voiceover_stores_null_text_with_pauses(client, rows):
    """Audit B4: the inverted ``is None`` check stored the string "null"."""
    response = client.post("/voiceovers/p", json={})
    (row,) = rows(Voiceover)
    assert row.text_with_pauses is None
    assert row.start_time == 0.0
    assert response.json()["text_with_pauses"] == []


def test_duplicate_voiceover(client, sync_db, rows):
    """Audit B4: duplicating passed the decoded list straight into a Text column."""
    project = f.make_project(sync_db)
    vo = f.make_voiceover(sync_db, project, start_time=1.0, duration=2.5, layer=3)

    response = client.post(f"/voiceovers/{vo.id}/duplicate", json={})

    assert response.status_code == 200
    new = next(v for v in rows(Voiceover) if v.id != vo.id)
    # Falsy body values fall back to the original; layer defaults to 2 (truthy).
    assert (new.start_time, new.duration, new.cut_start, new.cut_end, new.layer) == (3.5, 2.5, 0.0, 0.0, 2)
    assert (new.project_id, new.src, new.text) == (project.id, vo.src, vo.text)
    assert json.loads(new.text_with_pauses) == json.loads(vo.text_with_pauses)
    assert json.loads(new.timestamps) == json.loads(vo.timestamps)
    assert response.json() == wire.voiceover(new)


def test_duplicate_missing_voiceover(client):
    response = client.post("/voiceovers/missing/duplicate", json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "Voiceover not found"}


def test_combine_voiceovers(client, sync_db, rows):
    """Audit B3: combine used attribute access on dicts and crashed."""
    project = f.make_project(sync_db)
    other = f.make_project(sync_db)
    f.make_voiceover(sync_db, project, text="Second.", start_time=4.0)
    f.make_voiceover(sync_db, project, text="First.", start_time=0.0)
    untouched = f.make_voiceover(sync_db, other, text="Other project.")

    response = client.post(f"/voiceovers/combine/{project.id}")

    assert response.status_code == 200
    (combined,) = rows(Voiceover, project_id=project.id)
    assert combined.text == "First. Second."
    assert (combined.start_time, combined.duration, combined.src) == (0.0, 4.0, None)
    assert response.json() == wire.voiceover(combined)
    assert [v.id for v in rows(Voiceover, project_id=other.id)] == [untouched.id]


def test_combine_voiceovers_is_atomic(client, sync_db, rows, monkeypatch):
    """If creating the combined voiceover fails, the originals are not deleted."""
    from app.repositories import voiceovers as voiceover_repo

    project = f.make_project(sync_db)
    f.make_voiceover(sync_db, project)

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(voiceover_repo, "add", fail)

    with pytest.raises(RuntimeError):
        client.post(f"/voiceovers/combine/{project.id}")
    assert len(rows(Voiceover, project_id=project.id)) == 1


def test_combine_without_voiceovers_creates_empty_one(client, rows):
    response = client.post("/voiceovers/combine/p")
    assert response.status_code == 200
    (row,) = rows(Voiceover)
    assert (row.project_id, row.text) == ("p", "")
    assert response.json()["text"] == ""


def test_delete_voiceover(client, sync_db, rows):
    project = f.make_project(sync_db)
    vo = f.make_voiceover(sync_db, project)
    keep = f.make_voiceover(sync_db, project)

    response = client.delete(f"/voiceovers/{vo.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Voiceover deleted successfully"}
    assert [v.id for v in rows(Voiceover)] == [keep.id]


TTS_RESULT = {
    "src": "voiceovers/generated.wav",
    "duration": 1.75,
    "text": "Hello there.",
    "timestamps": [{"word": "Hello", "start": 0.0, "end": 0.5}, {"word": "there.", "start": 0.5, "end": 1.0}],
    "text_with_pauses": [{"word": "Hello"}, {"word": "there."}, {"word": "[PAUSE]"}],
}


def test_generate_voiceover(client, sync_db, fake_tts, reload):
    vo = f.make_voiceover(sync_db, f.make_project(sync_db), text="old text")
    fake_tts.result = dict(TTS_RESULT)

    response = client.post(f"/voiceovers/generate/{vo.id}", json={"text": "Hello there."})

    assert response.status_code == 200
    assert response.json() == {
        "message": "voiceover generated successfully",
        "voiceover_id": vo.id,
        "src": "voiceovers/generated.wav",
        "duration": 1.75,
        "timestamps": TTS_RESULT["timestamps"],
    }
    assert fake_tts.texts == ["Hello there."]
    updated = reload(Voiceover, vo.id)
    assert (updated.src, updated.duration, updated.text) == ("voiceovers/generated.wav", 1.75, "Hello there.")
    assert json.loads(updated.timestamps) == TTS_RESULT["timestamps"]
    assert json.loads(updated.text_with_pauses) == TTS_RESULT["text_with_pauses"]


def test_generate_voiceover_with_empty_stored_text_raises(client, sync_db, fake_tts):
    vo = f.make_voiceover(sync_db, f.make_project(sync_db), text="")
    # A ValueError escapes as an unhandled 500 (audit B10).
    with pytest.raises(ValueError, match="Voiceover text is empty"):
        client.post(f"/voiceovers/generate/{vo.id}", json={"text": "x"})
    assert fake_tts.texts == []


def test_generate_missing_voiceover_raises(client, fake_tts):
    with pytest.raises(ValueError, match="Voiceover not found"):
        client.post("/voiceovers/generate/missing", json={"text": "x"})


def test_create_voiceover_null_start_time_falls_back_to_default(client, sync_db, rows):
    """An explicit JSON ``null`` behaves like an omitted field (former ``Body(0.0)``)."""
    project = f.make_project(sync_db)
    response = client.post(f"/voiceovers/{project.id}", json={"start_time": None})
    assert response.status_code == 200
    (row,) = rows(Voiceover)
    assert row.start_time == 0.0
