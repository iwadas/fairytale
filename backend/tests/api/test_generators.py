"""Characterization tests for /generators: every endpoint is a TODO stub."""


def test_fix_character_prompt_stub_takes_query_param(client):
    assert client.post("/generators/fix-character-prompt", params={"request": "x"}).json() is None
    assert client.post("/generators/fix-character-prompt").status_code == 422


def test_fix_scene_image_prompt_stub(client):
    response = client.post("/generators/fix-scene-image-prompt", json={"prompt": "p", "style": None, "style_power": 3})
    assert response.status_code == 200
    assert response.json() is None


def test_fix_scene_video_prompt_stub(client):
    response = client.post("/generators/fix-scene-video-prompt", json={"image_prompt": None, "video_prompt": "v"})
    assert response.status_code == 200
    assert response.json() is None
