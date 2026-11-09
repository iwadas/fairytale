"""``VideoBuilder``: fluent configuration + render of a project to an mp4 with moviepy.

Legacy renderer, to be superseded by the Remotion service.
"""

import logging
import os
import shutil
import tempfile
import uuid
from collections.abc import Mapping
from typing import Any

from moviepy import AudioFileClip

from app.pipeline.render.audio import AudioGenerator
from app.pipeline.render.subtitles import (
    DEFAULT_SUBTITLE_COLOR,
    DEFAULT_SUBTITLE_SPECIAL_COLOR,
    SUBTITLE_STYLES,
    SubtitleGenerator,
)
from app.pipeline.render.visual import VisualGenerator

logger = logging.getLogger(__name__)

DEFAULT_RESOLUTION = (720, 1280)
DEFAULT_FPS = 24
DEFAULT_SUBTITLE_STYLE = "border"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
RENDER_THREADS = 4

# Serialized project: "scenes", "voiceovers" and "background_music" lists of timeline elements.
Project = Mapping[str, Any]


class VideoBuilder:
    def __init__(self, project: Project, output_filename: str):
        self._project = project
        self._output_filename = output_filename
        self._resolution = DEFAULT_RESOLUTION
        self._fps = DEFAULT_FPS
        self._subtitle_type = DEFAULT_SUBTITLE_STYLE
        self._subtitle_color = DEFAULT_SUBTITLE_COLOR
        self._subtitle_special_color = DEFAULT_SUBTITLE_SPECIAL_COLOR
        self._fonts: set[str] = set()
        self._subtitle_shadow = False
        self._subtitle_border = {"width": 0, "color": "white"}

    # --- Fluent configuration ---

    def set_resolution(self, width: int, height: int) -> "VideoBuilder":
        self._resolution = (width, height)
        return self

    def set_subtitle_style(self, style: str) -> "VideoBuilder":
        if style not in SUBTITLE_STYLES:
            raise ValueError(f"Unsupported subtitle style: {style}, must be one of {', '.join(SUBTITLE_STYLES)}")
        self._subtitle_type = style
        return self

    def set_subtitle_border(self, width: int, color: str) -> "VideoBuilder":
        self._subtitle_border = {"width": width, "color": color}
        return self

    def set_subtitle_color(self, color: str) -> "VideoBuilder":
        self._subtitle_color = color
        return self

    def set_subtitle_special_color(self, color: str) -> "VideoBuilder":
        # Currently has no visual effect: special karaoke words are only upper-cased.
        self._subtitle_special_color = color
        return self

    def add_subtitle_shadow(self) -> "VideoBuilder":
        self._subtitle_shadow = True
        return self

    def add_font(self, font_path: str) -> "VideoBuilder":
        self._fonts.add(font_path)
        return self

    # --- Timeline math ---

    def get_element_duration(self, element: Mapping[str, Any]) -> float:
        """Visible duration: ``duration`` minus ``cut_start`` and ``cut_end``."""
        return (
            float(element.get("duration", 0.0))
            - float(element.get("cut_end", 0.0))
            - float(element.get("cut_start", 0.0))
        )

    def get_element_end_time(self, element: Mapping[str, Any]) -> float:
        return float(element.get("start_time", 0.0)) + self.get_element_duration(element)

    def get_project_duration(self) -> float:
        """End of the latest scene, voiceover or music element."""
        elements = [
            *self._project.get("scenes", []),
            *self._project.get("voiceovers", []),
            *self._project.get("background_music", []),
        ]
        return max([0.0, *(self.get_element_end_time(element) for element in elements)])

    # --- Render ---

    def build(self) -> str:
        """Render the project to ``output_filename`` and return that path."""
        logger.info("Building %s...", self._output_filename)

        temp_dir = tempfile.mkdtemp(prefix="proj_render_")
        try:
            audio_path = AudioGenerator(
                self, output_path=os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.wav")
            ).generate()

            visuals = VisualGenerator(self).generate()
            with_subtitles = SubtitleGenerator(builder=self, visuals=visuals).generate()

            final = (
                with_subtitles.with_audio(AudioFileClip(audio_path))
                .with_duration(self.get_project_duration())
                .with_fps(self._fps)
            )
            final.write_videofile(
                self._output_filename,
                fps=self._fps,
                codec=VIDEO_CODEC,
                audio_codec=AUDIO_CODEC,
                threads=RENDER_THREADS,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return self._output_filename
