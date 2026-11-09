"""The JSON shapes the frontend currently receives, built from seeded ORM rows.

Two formats exist for the same entities:

* **raw** (``GET /projects`` and ``GET /projects/{id}``): every column as stored,
  so ``timestamps`` / ``text_with_pauses`` are JSON *strings* and nullable
  columns stay ``None``.
* **serialized** (create / duplicate / update responses, and the project dict
  handed to ``VideoBuilder``): JSON text columns decoded, ``cut_*`` / ``layer``
  falling back to defaults, unloaded relationships as ``[]``.
"""

import json


# --- raw ----------------------------------------------------------------------


def raw_scene_image(image) -> dict:
    return {
        "id": image.id,
        "scene_id": image.scene_id,
        "time": image.time,
        "prompt": image.prompt,
        "idea": image.idea,
        "src": image.src,
        "style": image.style,
    }


def raw_scene(scene, images=()) -> dict:
    return {
        "id": scene.id,
        "project_id": scene.project_id,
        "start_time": scene.start_time,
        "duration": scene.duration,
        "video_prompt": scene.video_prompt,
        "video_src": scene.video_src,
        "cut_start": scene.cut_start,
        "cut_end": scene.cut_end,
        "layer": scene.layer,
        "images": [raw_scene_image(i) for i in images],
        "characters": [],
        "places": [],
    }


def raw_voiceover(vo) -> dict:
    return {
        "id": vo.id,
        "project_id": vo.project_id,
        "text": vo.text,
        "text_with_pauses": vo.text_with_pauses,
        "src": vo.src,
        "start_time": vo.start_time,
        "timestamps": vo.timestamps,
        "duration": vo.duration,
        "cut_start": vo.cut_start,
        "cut_end": vo.cut_end,
        "layer": vo.layer,
    }


def raw_music(music) -> dict:
    return {
        "id": music.id,
        "project_id": music.project_id,
        "name": music.name,
        "src": music.src,
        "start_time": music.start_time,
        "duration": music.duration,
        "cut_start": music.cut_start,
        "cut_end": music.cut_end,
        "layer": music.layer,
    }


# --- serialized ---------------------------------------------------------------


def scene_image(image) -> dict:
    return {
        "id": image.id,
        "time": image.time,
        "prompt": image.prompt,
        "src": image.src,
        "style": image.style,
        "idea": image.idea,
    }


def scene(row, images=()) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "video_prompt": row.video_prompt,
        "video_src": row.video_src,
        "characters": [],
        "places": [],
        "images": [scene_image(i) for i in images],
        "start_time": row.start_time,
        "duration": row.duration,
        "cut_start": row.cut_start or 0.0,
        "cut_end": row.cut_end or 0.0,
        "layer": row.layer or 2,
    }


def voiceover(row) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "src": row.src,
        "text": row.text,
        "text_with_pauses": json.loads(row.text_with_pauses) if row.text_with_pauses else [],
        "timestamps": json.loads(row.timestamps) if row.timestamps else [],
        "start_time": row.start_time,
        "duration": row.duration,
        "cut_start": row.cut_start or 0.0,
        "cut_end": row.cut_end or 0.0,
        "layer": row.layer or 3,
    }


def music(row) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "name": row.name,
        "src": row.src,
        "start_time": row.start_time,
        "duration": row.duration,
        "cut_start": row.cut_start or 0.0,
        "cut_end": row.cut_end or 0.0,
        "layer": row.layer or 4,
    }


def settings(row) -> dict:
    def decode(value):
        return json.loads(value) if value else {}

    return {
        "id": row.id,
        "selected_tts_provider": row.selected_tts_provider,
        "selected_llm_provider": row.selected_llm_provider,
        "selected_diffusion_provider": row.selected_diffusion_provider,
        "tts_provider_settings": decode(row.tts_provider_settings),
        "diffusion_provider_settings": decode(row.diffusion_provider_settings),
        "llm_provider_settings": decode(row.llm_provider_settings),
        "selected_script_generation_template": row.selected_script_generation_template,
        "script_generation_templates": decode(row.script_generation_templates),
    }
