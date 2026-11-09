"""Characterization tests for /music (wire format + DB side effects)."""

import os

from app.db.models import Music
from tests import factories as f
from tests.api import wire


def test_create_music(client, sync_db, rows):
    project = f.make_project(sync_db)

    response = client.post(f"/music/{project.id}", json={"start_time": 5.0})

    assert response.status_code == 200
    (row,) = rows(Music)
    assert response.json() == {
        "id": row.id,
        "project_id": project.id,
        "name": "",
        "src": "",
        "start_time": 5.0,
        "duration": 30.0,
        "cut_start": 0.0,
        "cut_end": 0.0,
        "layer": 4,
    }
    assert (row.name, row.src, row.start_time, row.duration, row.layer) == ("", "", 5.0, 30.0, 4)


def test_create_music_requires_start_time(client):
    assert client.post("/music/p", json={}).status_code == 422


def test_duplicate_music(client, sync_db, rows):
    track = f.make_music(sync_db, f.make_project(sync_db), start_time=2.0, duration=10.0, cut_start=1.0)

    response = client.post(f"/music/{track.id}/duplicate", json={"cut_end": 0.5})

    assert response.status_code == 200
    new = next(m for m in rows(Music) if m.id != track.id)
    # Falsy body values fall back to the original; layer defaults to 2 (truthy).
    assert (new.start_time, new.duration, new.cut_start, new.cut_end, new.layer) == (12.0, 10.0, 1.0, 0.5, 2)
    assert (new.project_id, new.name, new.src) == (track.project_id, track.name, track.src)
    assert response.json() == wire.music(new)


def test_duplicate_missing_music(client):
    response = client.post("/music/missing/duplicate", json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "Music not found"}


def test_upload_music(client, sync_db, media_dirs, reload):
    track = f.make_music(sync_db, f.make_project(sync_db))

    response = client.put(f"/music/upload-music/{track.id}", files={"music_file": ("my song.mp3", b"not audio")})

    assert response.status_code == 200
    updated = reload(Music, track.id)
    assert response.json() == {"message": "Music uploaded successfully", "music": wire.music(updated)}
    assert updated.name == "my_song.mp3"
    # Undecodable audio -> duration 0.0 (the error is logged, not raised).
    assert updated.duration == 0.0
    assert os.path.dirname(updated.src) == media_dirs["music_dir"]
    assert updated.src.endswith(".mp3")
    with open(updated.src, "rb") as fh:
        assert fh.read() == b"not audio"


def test_upload_music_missing(client, media_dirs):
    response = client.put("/music/upload-music/missing", files={"music_file": ("a.mp3", b"x")})
    assert response.status_code == 404
    assert response.json() == {"detail": "Music not found"}


def test_update_music_src(client, sync_db, reload):
    track = f.make_music(sync_db, f.make_project(sync_db))

    response = client.put(f"/music/{track.id}", json={"src": "static/music/does not exist.mp3"})

    assert response.status_code == 200
    updated = reload(Music, track.id)
    assert response.json() == wire.music(updated)
    # Missing file -> duration 0.0; name derived from the last path segment.
    assert (updated.src, updated.name, updated.duration) == (
        "static/music/does not exist.mp3", "does_not_exist.mp3", 0.0,
    )


def test_update_missing_music(client):
    response = client.put("/music/missing", json={"src": "x.mp3"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Music not found"}


def test_delete_music(client, sync_db, rows):
    project = f.make_project(sync_db)
    track = f.make_music(sync_db, project)
    keep = f.make_music(sync_db, project)

    response = client.delete(f"/music/{track.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Music deleted successfully"}
    assert [m.id for m in rows(Music)] == [keep.id]
