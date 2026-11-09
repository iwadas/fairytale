"""Characterization tests for /scenes (wire format + DB side effects)."""

import os

from app.db.models import Scene, SceneImage
from tests import factories as f
from tests.api import wire

# --- LLM prompt helpers ---------------------------------------------------------


def test_generate_image_prompts(client, fake_llm):
    fake_llm.answers["ResponseScenes"] = {
        "scenes": [{"image_prompt": "a cat", "video_prompt": "pan left"}, {"image_prompt": "a dog", "video_prompt": "zoom"}]
    }

    response = client.post(
        "/scenes/generate-image-prompts",
        json={"project_id": "p1", "selected_voiceover_text_part": "The sentence.", "additional_info": "dark"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "new_scene_descriptions": [
            {"image_prompt": "a cat", "video_prompt": "pan left"},
            {"image_prompt": "a dog", "video_prompt": "zoom"},
        ]
    }
    ((_, messages),) = fake_llm.calls
    assert '"The sentence."' in messages[1]["content"]
    assert "Additional information about the generation (EXTREMELY IMPORTANT): dark" in messages[1]["content"]


def test_generate_image_prompts_includes_full_script(client, sync_db, fake_llm):
    project = f.make_project(sync_db)
    f.make_voiceover(sync_db, project, text="Second part.", start_time=5.0)
    f.make_voiceover(sync_db, project, text="First part.", start_time=0.0)
    fake_llm.answers["ResponseScenes"] = {"scenes": []}

    response = client.post(
        "/scenes/generate-image-prompts",
        json={"project_id": project.id, "selected_voiceover_text_part": "First part."},
    )

    assert response.status_code == 200
    assert response.json() == {"new_scene_descriptions": []}
    ((_, messages),) = fake_llm.calls
    assert '### FULL SCRIPT OVERVIEW:\n"First part. Second part."' in messages[0]["content"]
    assert "Additional information" not in messages[1]["content"]


def test_fix_image_prompt(client, fake_llm):
    fake_llm.answers["FixedPromptResponse"] = {"prompt": "fixed prompt"}

    response = client.post("/scenes/fix-image-prompt", json={"scene_prompt": "a cat", "style": "ignored", "style_power": 7})

    assert response.status_code == 200
    assert response.json() == {"fixed_prompt": "fixed prompt"}
    ((_, messages),) = fake_llm.calls
    assert "a cat" in messages[1]["content"]
    assert "(7.0/10)" in messages[1]["content"]
    # The request's style is overridden by a hardcoded one (audit B7).
    assert "ignored" not in messages[1]["content"]
    assert "Polished Black Obsidian" in messages[1]["content"]


def test_fix_video_prompt_updates_scene(client, sync_db, fake_llm, reload):
    project = f.make_project(sync_db)
    scene = f.make_scene(sync_db, project, layer=None)
    f.make_scene_image(sync_db, scene)
    fake_llm.answers["VideoPromptUpdate"] = {"new_video_prompt": "[Dolly in], [walks], [calm]"}

    response = client.post(
        f"/scenes/fix-video-prompt/{scene.id}", json={"new_camera_movement": "dolly in", "additional_info": "slower"}
    )

    assert response.status_code == 200
    updated = reload(Scene, scene.id)
    assert updated.video_prompt == "[Dolly in], [walks], [calm]"
    # The response is the serialized scene without its images (not loaded).
    assert response.json() == {**wire.scene(updated), "images": [], "layer": 2}
    ((_, messages),) = fake_llm.calls
    content = messages[1]["content"]
    assert "**dolly in**" in content
    assert "User provided additional adjustments: slower" in content
    assert "- Base Idea: loneliness" in content
    assert "- Current Video Prompt: slow pan" in content


def test_fix_video_prompt_requires_scene_with_images(client, sync_db, fake_llm):
    scene = f.make_scene(sync_db, f.make_project(sync_db))

    for scene_id in (scene.id, "missing"):
        response = client.post(f"/scenes/fix-video-prompt/{scene_id}", json={"new_camera_movement": "pan"})
        assert response.status_code == 404
        assert response.json() == {"detail": "Scene or images not found"}
    assert fake_llm.calls == []


# --- create / duplicate / delete ------------------------------------------------


def test_create_scene(client, sync_db, rows):
    project = f.make_project(sync_db)

    response = client.post(f"/scenes/{project.id}", json={"start_time": 4.5})

    assert response.status_code == 200
    body = response.json()
    (row,) = rows(Scene)
    assert body == {
        "id": row.id,
        "project_id": project.id,
        "video_prompt": None,
        "video_src": None,
        "characters": [],
        "places": [],
        "images": [],
        "start_time": 4.5,
        "duration": 3.0,
        "cut_start": 0.0,
        "cut_end": 0.0,
        "layer": 2,
    }
    assert (row.project_id, row.start_time, row.duration, row.layer) == (project.id, 4.5, 3, 2)


def test_create_scene_defaults_start_time(client, rows):
    response = client.post("/scenes/any-project")
    assert response.status_code == 200
    assert response.json()["start_time"] == 0.0
    (row,) = rows(Scene)
    assert row.project_id == "any-project"


def test_add_character_to_scene_is_shadowed_by_create_scene(client, rows):
    """Audit B6: ``POST /scenes/{project_id}`` is registered first and wins."""
    response = client.post("/scenes/add-character-to-scene", json={"scene_id": "s", "character_id": "c"})

    assert response.status_code == 200
    assert response.json()["project_id"] == "add-character-to-scene"
    (row,) = rows(Scene)
    assert row.project_id == "add-character-to-scene"


def test_duplicate_scene_with_defaults(client, sync_db, rows):
    project = f.make_project(sync_db)
    scene = f.make_scene(sync_db, project, start_time=2.0, duration=3, layer=1)
    f.make_scene_image(sync_db, scene, time="start")
    f.make_scene_image(sync_db, scene, time="end", src=None, prompt="p2", idea="i2", style="s2")

    response = client.post(f"/scenes/{scene.id}/duplicate", json={})

    assert response.status_code == 200
    body = response.json()
    new = next(s for s in rows(Scene) if s.id != scene.id)
    # Falsy body values fall back to the original; layer defaults to 2 (truthy).
    assert (new.start_time, new.duration, new.cut_start, new.cut_end, new.layer) == (5.0, 3, 0.25, 0.5, 2)
    assert (new.project_id, new.video_src, new.video_prompt) == (project.id, scene.video_src, scene.video_prompt)
    copies = sorted(new.images, key=lambda i: i.time)
    assert [(i.time, i.src, i.prompt, i.idea, i.style) for i in copies] == [
        ("end", None, "p2", "i2", "s2"),
        ("start", "static/images/scenes/a.png", "a lighthouse", "loneliness", "engraving"),
    ]
    # The response does not include the copied images (relationship not loaded).
    assert body == {**wire.scene(new), "images": []}


def test_duplicate_scene_with_explicit_values(client, sync_db, rows):
    scene = f.make_scene(sync_db, f.make_project(sync_db))

    response = client.post(
        f"/scenes/{scene.id}/duplicate",
        json={"start_time": 9.0, "cut_start": 0.1, "cut_end": 0.2, "duration": 2.5, "layer": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["start_time"], body["cut_start"], body["cut_end"], body["duration"], body["layer"]) == (
        9.0, 0.1, 0.2, 2.5, 5,
    )
    new = next(s for s in rows(Scene) if s.id != scene.id)
    assert (new.start_time, new.layer) == (9.0, 5)


def test_duplicate_missing_scene(client):
    response = client.post("/scenes/missing/duplicate", json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "Scene not found"}


def test_delete_scene_leaves_images_orphaned(client, sync_db, rows):
    scene = f.make_scene(sync_db, f.make_project(sync_db))
    f.make_scene_image(sync_db, scene)

    response = client.delete(f"/scenes/{scene.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Scene deleted successfully"}
    assert rows(Scene) == []
    # Bulk delete bypasses the ORM delete-orphan cascade (audit B8).
    assert len(rows(SceneImage)) == 1


def test_remove_scene_image(client, sync_db, rows):
    scene = f.make_scene(sync_db, f.make_project(sync_db))
    image = f.make_scene_image(sync_db, scene)
    keep = f.make_scene_image(sync_db, scene)

    response = client.delete(f"/scenes/remove-image/{image.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Scene image removed successfully", "scene_image_id": image.id}
    assert [i.id for i in rows(SceneImage)] == [keep.id]


def test_generate_image_is_a_stub(client):
    response = client.post("/scenes/generate-image/any", data={"prompt": "x"})
    assert response.status_code == 200
    assert response.json() is None


# --- uploads ----------------------------------------------------------------------


def test_upload_scene_video(client, sync_db, media_dirs, reload):
    scene = f.make_scene(sync_db, f.make_project(sync_db))

    response = client.put(f"/scenes/upload-video/{scene.id}", files={"video": ("clip.mov", b"not a real video")})

    assert response.status_code == 200
    body = response.json()
    src = body["video_src"]
    # Unreadable video -> duration 0.0 (the error is logged, not raised).
    assert body == {"message": "Scene video uploaded successfully", "video_src": src, "duration": 0.0}
    assert os.path.dirname(src) == media_dirs["scene_video_dir"]
    assert os.path.basename(src).startswith("scene_") and src.endswith(".mp4")
    with open(src, "rb") as fh:
        assert fh.read() == b"not a real video"
    updated = reload(Scene, scene.id)
    assert (updated.video_src, updated.duration) == (src, 0)


def test_upload_scene_video_missing_scene(client, media_dirs):
    response = client.put("/scenes/upload-video/missing", files={"video": ("clip.mp4", b"x")})
    assert response.status_code == 404
    assert response.json() == {"detail": "Scene not found"}


def test_upload_scene_image_creates_image(client, sync_db, media_dirs, rows):
    scene = f.make_scene(sync_db, f.make_project(sync_db))

    response = client.put(
        f"/scenes/upload-image/{scene.id}",
        data={"time": "mid", "scene_image_prompt": "a prompt"},
        files={"image": ("pic.jpg", b"not an image")},
    )

    assert response.status_code == 200
    body = response.json()
    (image,) = rows(SceneImage)
    assert body == {
        "message": "Scene image uploaded successfully",
        "scene_image": {"id": image.id, "time": "mid", "prompt": "a prompt", "src": image.src, "style": None, "idea": None},
    }
    assert image.scene_id == scene.id
    assert os.path.dirname(image.src) == media_dirs["scene_image_dir"]
    assert image.src.endswith(".png")
    with open(image.src, "rb") as fh:
        assert fh.read() == b"not an image"


def test_upload_scene_image_updates_existing(client, sync_db, media_dirs, reload):
    scene = f.make_scene(sync_db, f.make_project(sync_db))
    image = f.make_scene_image(sync_db, scene)

    response = client.put(
        f"/scenes/upload-image/{scene.id}",
        data={"time": "end", "scene_image_id": image.id},
        files={"image": ("pic.png", b"png bytes")},
    )

    assert response.status_code == 200
    updated = reload(SceneImage, image.id)
    assert response.json() == {"message": "Scene image uploaded successfully", "scene_image": wire.scene_image(updated)}
    # No prompt sent -> prompt kept; src and time replaced.
    assert (updated.time, updated.prompt, updated.idea) == ("end", "a lighthouse", "loneliness")
    assert updated.src != "static/images/scenes/a.png"


def test_upload_scene_image_missing_scene(client, media_dirs):
    response = client.put("/scenes/upload-image/missing", data={"time": "start"}, files={"image": ("a.png", b"x")})
    assert response.status_code == 404
    assert response.json() == {"detail": "Scene not found"}


# --- background video generation --------------------------------------------------


def test_generate_scene_video_runs_in_background(client, sync_db, fake_diffusion, reload):
    scene = f.make_scene(sync_db, f.make_project(sync_db))
    f.make_scene_image(sync_db, scene, time="start", src="static/images/scenes/s.png")
    f.make_scene_image(sync_db, scene, time="end", src=None)

    with client.websocket_connect("/ws/responses") as responses:
        response = client.post(f"/scenes/generate-video/{scene.id}", json={"prompt": "pan", "duration": 5})
        pending = responses.receive_json()
        completed = responses.receive_json()

    assert response.status_code == 200
    assert response.json() == {"message": "Video generation started in background"}
    assert fake_diffusion.calls == [
        {
            "prompt": "pan",
            "frames": [{"src": "static/images/scenes/s.png", "time": "start"}],
            "duration": 5,
            "filename": f"scene_{scene.id}",
        }
    ]
    updated = reload(Scene, scene.id)
    assert (updated.video_src, updated.duration) == (fake_diffusion.src, 5)
    task_id = f"scene_video_generation_{scene.id}"
    assert pending == {"type": "scene_video_generation", "status": "pending", "task_id": task_id, "data": None}
    assert completed == {
        "type": "scene_video_generation",
        "status": "completed",
        "task_id": task_id,
        "data": {"video_src": fake_diffusion.src},
        "source": {"scene_id": scene.id},
    }


def test_generate_scene_video_failure_is_reported_not_raised(client, sync_db, fake_diffusion, reload):
    scene = f.make_scene(sync_db, f.make_project(sync_db))

    async def boom(**kwargs):
        raise RuntimeError("provider down")

    fake_diffusion.generate = boom

    with client.websocket_connect("/ws") as notifications:
        response = client.post(f"/scenes/generate-video/{scene.id}", json={"prompt": "pan"})
        messages = [notifications.receive_json() for _ in range(3)]

    assert response.status_code == 200
    assert [(m["type"], m["status"]) for m in messages] == [
        ("scene_video_generation", "init"),
        ("scene_video_generation", "in_progress"),
        ("scene_video_generation", "failed"),
    ]
    assert messages[2]["data"] == "❌ Video generation failed. Error: provider down"
    assert reload(Scene, scene.id).video_src == "static/videos/scenes/a.mp4"


def test_generate_scene_video_missing_scene(client, fake_diffusion):
    response = client.post("/scenes/generate-video/missing", json={"prompt": "pan"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Scene not found"}
    assert fake_diffusion.calls == []


def test_create_scene_null_start_time_falls_back_to_default(client, rows):
    """An explicit JSON ``null`` behaves like an omitted field (former ``Body(0.0)``)."""
    response = client.post("/scenes/any-project", json={"start_time": None})
    assert response.status_code == 200
    assert response.json()["start_time"] == 0.0
    (row,) = rows(Scene)
    assert row.start_time == 0.0


def test_generate_video_requires_prompt_even_when_null(client):
    response = client.post("/scenes/generate-video/any-scene", json={"prompt": None})
    assert response.status_code == 422
