"""Characterization tests for /projects (wire format + DB side effects)."""

import json
import os
from datetime import datetime

import pytest

from app.db.models import Music, Project, Scene, Voiceover
from app.pipeline.script.scene_generator import AVAILABLE_STYLES, split_script
from app.pipeline.script.script_generator import ScriptGenerator
from tests import factories as f
from tests.api import wire

# --- GET /projects --------------------------------------------------------------


def test_list_projects_newest_first_with_thumbnail(client, sync_db):
    old = f.make_project(sync_db, name="Old", created_at=datetime(2025, 1, 1, 0, 0, 0))
    new = f.make_project(sync_db, name="New", type=None, created_at=datetime(2026, 5, 6, 7, 8, 9))
    # Thumbnail = first non-empty image src, ordered by scene id then image id.
    scene_b = f.make_scene(sync_db, old, id="b-scene")
    scene_a = f.make_scene(sync_db, old, id="a-scene")
    f.make_scene_image(sync_db, scene_a, id="2", src="")
    f.make_scene_image(sync_db, scene_a, id="3", src="static/images/scenes/a3.png")
    f.make_scene_image(sync_db, scene_b, id="1", src="static/images/scenes/b1.png")

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == [
        {"id": new.id, "name": "New", "created_at": "2026-05-06T07:08:09", "type": None, "thumbnail": None},
        {
            "id": old.id,
            "name": "Old",
            "created_at": "2025-01-01T00:00:00",
            "type": "BASIC",
            "thumbnail": "static/images/scenes/a3.png",
        },
    ]


# --- GET /projects/{id} ---------------------------------------------------------


def test_get_project_returns_raw_graph(client, sync_db):
    project = f.make_project(sync_db)
    scene = f.make_scene(sync_db, project)
    image = f.make_scene_image(sync_db, scene)
    bare_scene = f.make_scene(sync_db, project, cut_start=None, cut_end=None, layer=None, video_src=None)
    vo = f.make_voiceover(sync_db, project)
    null_vo = f.make_voiceover(sync_db, project, text_with_pauses="null", timestamps=None, src=None)
    track = f.make_music(sync_db, project)

    response = client.get(f"/projects/{project.id}")

    assert response.status_code == 200
    body = response.json()
    scenes = sorted(body.pop("scenes"), key=lambda s: s["id"])
    assert scenes == sorted([wire.raw_scene(scene, [image]), wire.raw_scene(bare_scene)], key=lambda s: s["id"])
    assert sorted(body.pop("voiceovers"), key=lambda v: v["id"]) == sorted(
        [wire.raw_voiceover(vo), wire.raw_voiceover(null_vo)], key=lambda v: v["id"]
    )
    assert body == {
        "id": project.id,
        "name": "Test project",
        "created_at": "2026-01-02T03:04:05",
        "type": "BASIC",
        "places": [],
        "characters": [],
        "background_music": [wire.raw_music(track)],
    }


def test_get_project_raw_format_keeps_json_columns_as_strings(client, sync_db):
    project = f.make_project(sync_db)
    f.make_voiceover(sync_db, project, timestamps='[{"word": "a"}]', text_with_pauses="null")
    f.make_scene(sync_db, project, cut_start=None, layer=None, duration=3)

    body = client.get(f"/projects/{project.id}").json()

    assert body["voiceovers"][0]["timestamps"] == '[{"word": "a"}]'
    assert body["voiceovers"][0]["text_with_pauses"] == "null"
    assert body["scenes"][0]["cut_start"] is None
    assert body["scenes"][0]["layer"] is None
    assert body["scenes"][0]["duration"] == 3


def test_get_project_missing_returns_null(client):
    response = client.get("/projects/nope")
    assert response.status_code == 200
    assert response.json() is None


# --- POST /projects/generate-script ---------------------------------------------


SCRIPT_REQUEST = {
    "topic": "Stoicism",
    "duration": 60,
    "description": "short",
    "data": "facts",
    "gather_data": False,
    "persistant_characters": True,
    "reference_stories": None,
}


def test_generate_script(client, fake_llm, monkeypatch):
    seen = []

    async def generate(self):
        seen.append(self)
        return f"script about {self.topic}"

    monkeypatch.setattr(ScriptGenerator, "generate", generate)

    response = client.post("/projects/generate-script", json=SCRIPT_REQUEST)

    assert response.status_code == 200
    assert response.json() == {"scripts": ["script about Stoicism"]}
    (generator,) = seen
    assert generator.llm_client is fake_llm
    assert generator.description == "short"
    assert generator.story_data == "facts"
    assert generator.reference_stories is None
    assert generator.persistant_characters is True
    assert generator.word_limit == 180.0  # 180 words per minute


def test_generate_script_reads_provider_settings_from_db(client, sync_db, monkeypatch):
    """The real LLM.create() loads its provider config via settings_service (no network)."""
    f.make_settings(sync_db, llm_provider_settings=json.dumps({"xai": {"ai_model": "grok", "api_key": "k"}}))
    seen = []

    async def generate(self):
        seen.append(self.llm_client)
        return "script"

    monkeypatch.setattr(ScriptGenerator, "generate", generate)

    assert client.post("/projects/generate-script", json=SCRIPT_REQUEST).status_code == 200
    (llm,) = seen
    assert (llm.provider, llm.provider_settings) == ("xai", {"ai_model": "grok", "api_key": "k"})


def test_generate_script_provider_error_becomes_500(client):
    # No settings row: the real LLM.create() fails before any network call.
    response = client.post("/projects/generate-script", json=SCRIPT_REQUEST)

    assert response.status_code == 500
    assert response.json() == {"detail": "Settings not found in database."}


def test_generate_script_optional_fields_are_required(client):
    body = {k: v for k, v in SCRIPT_REQUEST.items() if k != "description"}
    assert client.post("/projects/generate-script", json=body).status_code == 422


# --- POST /projects/create-project ----------------------------------------------


IDEAS = ["idea-one", "idea-two", "idea-three"]
STYLE = next(iter(AVAILABLE_STYLES))


@pytest.fixture
def scene_llm(fake_llm):
    """Fake LLM for the scene pipeline: 3 ideas per script part."""
    fake_llm.answers["SceneIdeasResponse"] = {
        "scenes": [{"style": STYLE, "idea": idea, "reasoning": "why"} for idea in IDEAS]
    }

    def prompts(messages):
        idea = next(i for i in IDEAS if i in json.dumps(messages))
        return {"image_prompt": f"image of {idea}", "video_prompt": f"video of {idea}"}

    fake_llm.answers["ScenePromptsResponse"] = prompts
    return fake_llm


def test_create_project_persists_voiceovers_and_two_layer_scenes(client, scene_llm, rows):
    script = "The first sentence is here.<br>And the second one."
    parts = split_script(script)

    response = client.post("/projects/create-project", json={"topic": "My topic", "script": script})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"message", "project_id"}
    assert body["message"] == "Project created successfully"
    project_id = body["project_id"]

    (project,) = rows(Project)
    assert (project.id, project.name, project.type) == (project_id, "My topic", "BASIC")

    voiceovers = sorted(rows(Voiceover, project_id=project_id), key=lambda v: v.start_time)
    assert [(v.text, v.start_time, v.duration) for v in voiceovers] == [
        (p["text"], float(p["start_time"]), p["duration"]) for p in parts
    ]
    for vo in voiceovers:
        assert (vo.src, vo.timestamps, vo.cut_start, vo.cut_end, vo.layer) == (None, None, 0.0, 0.0, 3)

    scenes = rows(Scene, project_id=project_id)
    assert len(scenes) == 3 * len(parts)
    placed = sorted((s.start_time, s.layer, s.images[0].idea) for s in scenes)
    expected = []
    for part in parts:
        t = float(part["start_time"])
        # Layer toggles 2, 1, 2, ...; time advances 3s after every layer-1 scene.
        expected += [(t, 2, "idea-one"), (t, 1, "idea-two"), (t + 3.0, 2, "idea-three")]
    assert placed == sorted(expected)
    for s in scenes:
        (image,) = s.images
        assert s.duration == 3
        assert s.video_prompt == f"video of {image.idea}"
        assert (s.video_src, s.cut_start, s.cut_end) == (None, 0.0, 0.0)
        assert (image.prompt, image.time, image.style, image.src) == (f"image of {image.idea}", "start", STYLE, "")


def test_create_project_is_atomic(client, scene_llm, rows, monkeypatch):
    """A failure while saving scenes leaves no project/voiceover/scene behind."""
    from app.repositories import scenes as scene_repo

    real_add = scene_repo.add
    calls = []

    def flaky_add(session, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            raise RuntimeError("disk full")
        return real_add(session, **kwargs)

    monkeypatch.setattr(scene_repo, "add", flaky_add)

    with pytest.raises(RuntimeError, match="disk full"):
        client.post("/projects/create-project", json={"topic": "T", "script": "One sentence."})

    assert (rows(Project), rows(Voiceover), rows(Scene)) == ([], [], [])


# --- DELETE /projects/{id} ------------------------------------------------------


def test_delete_project_leaves_children_orphaned(client, sync_db, rows):
    project = f.make_project(sync_db)
    other = f.make_project(sync_db, name="Other")
    scene = f.make_scene(sync_db, project)
    f.make_voiceover(sync_db, project)

    response = client.delete(f"/projects/{project.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Project deleted successfully"}
    assert [p.id for p in rows(Project)] == [other.id]
    # Bulk delete bypasses ORM cascades and SQLite FKs are off (audit B8).
    assert [s.id for s in rows(Scene)] == [scene.id]
    assert len(rows(Voiceover)) == 1


# --- PUT /projects/{id} (timeline) ----------------------------------------------


def test_update_timeline(client, sync_db, reload):
    project = f.make_project(sync_db)
    scene = f.make_scene(sync_db, project)
    vo = f.make_voiceover(sync_db, project)
    track = f.make_music(sync_db, project)
    pauses = [{"word": "Hi"}, {"word": "[PAUSE]"}]

    response = client.put(
        f"/projects/{project.id}",
        json={
            "timeline_elements": [
                {
                    "id": scene.id, "type": "scene", "start_time": 7.0, "duration": 2.0,
                    "layer": 1, "cut_start": 0.5, "cut_end": 0.25, "video_prompt": "zoom",
                },
                {
                    "id": vo.id, "type": "voiceover", "start_time": 1.0, "duration": 3.5,
                    "layer": 3, "cut_start": 0.0, "cut_end": 0.0, "text": "Hi", "text_with_pauses": pauses,
                },
                # Missing keys fall back: start 0.0, duration 4.0, layer 0, cut_* None (audit B11).
                {"id": track.id, "type": "music"},
                {"id": "unknown", "type": "scene"},
                {"id": vo.id, "type": "something-else"},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Update successful"}
    s = reload(Scene, scene.id)
    assert (s.start_time, s.duration, s.layer, s.cut_start, s.cut_end, s.video_prompt) == (7.0, 2, 1, 0.5, 0.25, "zoom")
    v = reload(Voiceover, vo.id)
    assert (v.start_time, v.duration, v.layer, v.text) == (1.0, 3.5, 3, "Hi")
    assert json.loads(v.text_with_pauses) == pauses
    m = reload(Music, track.id)
    assert (m.start_time, m.duration, m.layer, m.cut_start, m.cut_end) == (0.0, 4.0, 0, None, None)
    assert (m.name, m.src) == ("theme.mp3", "static/music/theme.mp3")


def test_update_timeline_is_atomic(client, sync_db, reload):
    """An invalid element (no id) rolls back the updates applied before it."""
    project = f.make_project(sync_db)
    scene = f.make_scene(sync_db, project, start_time=1.5)

    with pytest.raises(KeyError):
        client.put(
            f"/projects/{project.id}",
            json={"timeline_elements": [{"id": scene.id, "type": "scene", "start_time": 9.0}, {"type": "scene"}]},
        )

    assert reload(Scene, scene.id).start_time == 1.5


def test_update_timeline_requires_embedded_list(client):
    assert client.put("/projects/x", json=[]).status_code == 422


# --- POST /projects/download/{id} -----------------------------------------------


def test_download_renders_serialized_project(client, sync_db, render_recorder, media_dirs):
    project = f.make_project(sync_db, name='My: "video" / 1')
    scene = f.make_scene(sync_db, project, layer=None)
    image = f.make_scene_image(sync_db, scene)
    vo = f.make_voiceover(sync_db, project)
    track = f.make_music(sync_db, project)

    response = client.post(f"/projects/download/{project.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    (build,) = render_recorder.builds
    assert build["output_filename"] == os.path.join(media_dirs["render_output_dir"], "My_video__1.mp4")
    assert os.path.isdir(media_dirs["render_output_dir"])
    assert build["resolution"] == (640, 640)
    assert build["subtitle_type"] == "karaoke_remotion"
    assert build["subtitle_color"] == "white"
    assert build["subtitle_special_color"] == "rgb(230, 163, 49)"
    assert build["subtitle_shadow"] is True
    assert build["fonts"] == {"static/default/fonts/Unna-Regular.ttf"}
    assert build["project"] == {
        "id": project.id,
        "name": 'My: "video" / 1',
        "created_at": "2026-01-02T03:04:05",
        "type": "BASIC",
        "characters": [],
        "places": [],
        "scenes": [wire.scene(scene, [image])],
        "voiceovers": [wire.voiceover(vo)],
        "background_music": [wire.music(track)],
    }
    assert build["project"]["scenes"][0]["layer"] == 2


# --- POST /projects/add-translations/{id} ---------------------------------------


def test_add_translations_is_a_stub(client):
    response = client.post("/projects/add-translations/anything")
    assert response.status_code == 200
    assert response.json() is None


# --- POST /projects/copy/{id} ---------------------------------------------------


def test_copy_project_without_voiceovers(client, sync_db, rows):
    project = f.make_project(sync_db, name="Source", type=None)
    scene = f.make_scene(sync_db, project, layer=None, cut_start=None)
    f.make_scene_image(sync_db, scene, time="end")
    track = f.make_music(sync_db, project, layer=None)

    response = client.post(f"/projects/copy/{project.id}")

    assert response.status_code == 200
    body = response.json()
    new_id = body.pop("new_project_id")
    assert body == {"success": True, "message": "Project copied successfully"}
    copy = next(p for p in rows(Project) if p.id == new_id)
    # type=None is passed through, and the ORM then applies the column default.
    assert (copy.name, copy.type) == ("Source (Copy)", "BASIC")

    (new_scene,) = rows(Scene, project_id=new_id)
    assert new_scene.id != scene.id
    # Copies go through the serialized form, so defaults are materialised.
    assert (new_scene.start_time, new_scene.duration, new_scene.layer, new_scene.cut_start, new_scene.cut_end) == (
        1.5, 3, 2, 0.0, 0.5,
    )
    assert (new_scene.video_prompt, new_scene.video_src) == (scene.video_prompt, scene.video_src)
    (new_image,) = new_scene.images
    assert (new_image.time, new_image.prompt, new_image.src, new_image.idea, new_image.style) == (
        "end", "a lighthouse", "static/images/scenes/a.png", "loneliness", "engraving",
    )
    (new_track,) = rows(Music, project_id=new_id)
    assert new_track.id != track.id
    assert (new_track.name, new_track.src, new_track.layer, new_track.duration) == ("theme.mp3", track.src, 4, 30.0)
    # Source untouched.
    assert len(rows(Scene, project_id=project.id)) == 1


def test_copy_project_with_voiceovers(client, sync_db, rows):
    """Audit B4: a list ``text_with_pauses`` used to be bound raw to a Text column."""
    project = f.make_project(sync_db)
    vo = f.make_voiceover(sync_db, project)
    f.make_voiceover(sync_db, project, text_with_pauses=None, timestamps=None, start_time=5.0)

    response = client.post(f"/projects/copy/{project.id}")

    assert response.status_code == 200
    new_id = response.json()["new_project_id"]
    copies = sorted(rows(Voiceover, project_id=new_id), key=lambda v: v.start_time)
    assert len(copies) == 2
    assert json.loads(copies[0].text_with_pauses) == json.loads(vo.text_with_pauses)
    assert json.loads(copies[0].timestamps) == json.loads(vo.timestamps)
    assert (copies[0].text, copies[0].src, copies[0].duration) == (vo.text, vo.src, vo.duration)
    # Empty pauses/timestamps round-trip through the serialized form as "[]".
    assert (copies[1].text_with_pauses, copies[1].timestamps) == ("[]", "[]")
