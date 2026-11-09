"""Turn a script into timed parts, each with LLM-generated scene prompts.

Pipeline per script part (parts run concurrently, bounded by a semaphore):
  1. Agent 1 brainstorms scene ideas, each tied to a style from ``AVAILABLE_STYLES``.
  2. Agent 2 expands every idea into an image prompt and a video prompt (concurrently).
"""
from __future__ import annotations

import asyncio
import logging
import math
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from app.pipeline.script.scene_prompts import (
    build_expansion_messages,
    build_idea_messages,
    format_style_catalogue,
)
from app.pipeline.script.styles import AVAILABLE_STYLES

if TYPE_CHECKING:
    from app.ai.llm import LLM

__all__ = [
    "AVAILABLE_STYLES",
    "SceneIdea",
    "SceneIdeasResponse",
    "ScenePromptsResponse",
    "estimate_duration",
    "split_script",
    "generate_scenes",
]

logger = logging.getLogger(__name__)

ProgressCallback = Callable[..., Awaitable[Any]]

# ------------------------------------------
# Timing
# ------------------------------------------
WORDS_PER_MINUTE = 200.0
CHARS_PER_MINUTE = WORDS_PER_MINUTE * 5
SCRIPT_PART_SEPARATOR = "<br>"
PAUSE_AFTER_SEPARATOR_SECONDS = 2.0

# One scene idea per 1.5 s of narration. This mirrors the layout in
# api/routers/projects.py::create_project, which places every generated scene as
# a 3.0 s clip alternating between two layers (layer 2, then layer 1, ...) and
# only advances the timeline after each layer-1 clip. Two 3 s scenes therefore
# cover 3 s of timeline, i.e. 1.5 s per scene. Change both places together.
SECONDS_OF_NARRATION_PER_SCENE = 1.5

# ------------------------------------------
# LLM settings
# ------------------------------------------
IDEA_TEMPERATURE = 0.8
EXPANSION_TEMPERATURE = 0.5
DEFAULT_MAX_CONCURRENT_PARTS = 5  # adjust to the API tier's rate limits


def estimate_duration(text: str) -> float:
    """Rough narration length in seconds (word rate plus half a character-rate term)."""
    words = len(text.split())
    chars = len(text.replace(" ", ""))
    seconds = round((words / WORDS_PER_MINUTE * 60) + (chars / CHARS_PER_MINUTE * 60) / 2, 1)
    return seconds


def split_script(script: str) -> list[dict[str, Any]]:
    """Split on ``<br>`` into ``{start_time, text, duration}`` parts.

    Each separator adds a fixed pause to the running start time.
    """
    parts = re.split(f"({SCRIPT_PART_SEPARATOR})", script)
    sentences: list[dict[str, Any]] = []

    current_time: float = 0
    for part in parts:
        part = part.strip()
        if part and part != SCRIPT_PART_SEPARATOR:
            duration = estimate_duration(part)
            sentences.append({
                "start_time": current_time,
                "text": part,
                "duration": duration,
            })
            current_time += duration
        elif part == SCRIPT_PART_SEPARATOR:
            current_time += PAUSE_AFTER_SEPARATOR_SECONDS

    logger.debug("Split script into sentences with timing:")
    for sentence in sentences:
        logger.debug(
            "Start: %ss, Duration: %ss, Text: %s",
            sentence["start_time"], sentence["duration"], sentence["text"],
        )
    return sentences


# ------------------------------------------
# Structured LLM outputs
# ------------------------------------------
class SceneIdea(BaseModel):
    style: str = Field(
        description="Name of the best suiting style for this generation.",
        json_schema_extra={"enum": list(AVAILABLE_STYLES.keys())}
    )
    idea: str = Field(description="Brief description of the visual scene, concise—focus on the core visual subject and environment")
    reasoning: str = Field(description="Why visual fits the context")


class SceneIdeasResponse(BaseModel):
    scenes: list[SceneIdea]


class ScenePromptsResponse(BaseModel):
    image_prompt: str = Field(description="Highly descriptive image prompt including subject, environment, lighting, and style integration.")
    video_prompt: str = Field(description="Motion-focused video prompt. Format: [Camera Movement], [Subject Movement], [Speed/Vibe]")


# ------------------------------------------
# Agents
# ------------------------------------------
def scene_count_for(duration: float) -> int:
    return math.ceil(duration / SECONDS_OF_NARRATION_PER_SCENE)


async def _generate_ideas(
    llm_client: LLM, script: str, script_part: dict[str, Any]
) -> SceneIdeasResponse:
    """Agent 1: brainstorm style-driven scene ideas for one script part."""
    messages = build_idea_messages(
        script=script,
        sentence=script_part["text"],
        num_scenes=scene_count_for(script_part["duration"]),
        style_catalogue=format_style_catalogue(AVAILABLE_STYLES),
    )
    return await llm_client.generate(
        messages=messages, response_format=SceneIdeasResponse, temperature=IDEA_TEMPERATURE
    )


async def _expand_single_prompt(llm_client: LLM, local_idx: int, idea_obj: SceneIdea) -> dict[str, Any]:
    """Agent 2: expand one idea into image and video prompts."""
    style_prompt = AVAILABLE_STYLES.get(idea_obj.style, {}).get("technical_prompt", "")
    messages = build_expansion_messages(
        idea=idea_obj.idea, reasoning=idea_obj.reasoning, style_prompt=style_prompt
    )
    prompts_response = await llm_client.generate(
        messages=messages, response_format=ScenePromptsResponse, temperature=EXPANSION_TEMPERATURE
    )
    return {
        "local_id": local_idx,
        "style": idea_obj.style,
        "idea": idea_obj.idea,
        "reasoning": idea_obj.reasoning,
        "image_prompt": prompts_response.image_prompt,
        "video_prompt": prompts_response.video_prompt,
    }


async def _process_script_part(
    i: int,
    script_part: dict[str, Any],
    llm_client: LLM,
    script: str,
    total_parts: int,
    semaphore: asyncio.Semaphore,
    progress_callback: ProgressCallback | None,
) -> dict[str, Any]:
    """Run Agent 1 then Agent 2 for one script part."""
    async def report(message: str) -> None:
        if progress_callback:
            await progress_callback(status="in_progress", message=message)

    part_label = f"Part {i+1}/{total_parts}"

    async with semaphore:
        await report(f"🎬 {part_label}: Agent 1 brainstorming...")
        ideas_response = await _generate_ideas(llm_client, script, script_part)

        await report(f"🎨 {part_label}: Agent 2 expanding prompts...")
        scenes = await asyncio.gather(*[
            _expand_single_prompt(llm_client, local_idx, idea_obj)
            for local_idx, idea_obj in enumerate(ideas_response.scenes)
        ])

        # Agent 3 (camera-movement harmonization) was removed; this progress
        # message is kept so callers receive the same message sequence.
        await report(f"🎥 {part_label}: Agent 3 harmonizing flow...")

        return {
            "text": script_part["text"],
            "duration": script_part["duration"],
            "start_time": script_part["start_time"],
            "scenes": scenes,
        }


async def generate_scenes(
    llm_client: LLM,
    script: str,
    splitted_script: list[dict[str, Any]],
    progress_callback: ProgressCallback | None = None,
    max_concurrent_parts: int = DEFAULT_MAX_CONCURRENT_PARTS,
) -> list[dict[str, Any]]:
    """Generate scenes for every part of ``splitted_script`` (from ``split_script``).

    Returns the parts in input order, each with a ``scenes`` list.
    """
    total_parts = len(splitted_script)
    semaphore = asyncio.Semaphore(max_concurrent_parts)

    script_parts_with_scenes = await asyncio.gather(*[
        _process_script_part(i, part, llm_client, script, total_parts, semaphore, progress_callback)
        for i, part in enumerate(splitted_script)
    ])

    if progress_callback:
        await progress_callback(status="complete", message="✅ Pipeline finished asynchronously!")

    return list(script_parts_with_scenes)
