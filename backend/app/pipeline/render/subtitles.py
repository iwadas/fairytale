"""Subtitle overlay for the configured ``VideoBuilder`` subtitle style."""

import logging
import os
from typing import TYPE_CHECKING

from moviepy import CompositeVideoClip, VideoClip, VideoFileClip

from app.core.config import get_settings
from app.pipeline.render.text.border_text_generator import generate_border_text
from app.pipeline.render.text.invert_text_mask import generate_invert_mask_text
from app.pipeline.render.text.karaoke_text import generate_karaoke_text
from app.pipeline.render.word_timing import karaoke_segments, single_word_timings

if TYPE_CHECKING:
    from app.pipeline.render.builder import VideoBuilder

logger = logging.getLogger(__name__)

SUBTITLE_STYLES = ("none", "invert_mask", "border", "karaoke", "karaoke_remotion")
DEFAULT_SUBTITLE_COLOR = "white"
DEFAULT_SUBTITLE_SPECIAL_COLOR = "rgb(230, 163, 49)"
# Pre-rendered transparent subtitle overlay, relative to the Remotion app directory.
REMOTION_OVERLAY_PATH = os.path.join("out", "video.mov")


class SubtitleGenerator:
    def __init__(self, builder: "VideoBuilder", visuals: VideoClip | None = None):
        self._builder = builder
        self._visuals = visuals

    def generate(self) -> VideoClip:
        renderers = {
            "invert_mask": self._invert_mask,
            "border": self._border,
            "karaoke": self._karaoke,
            "karaoke_remotion": self._remotion_overlay,
        }
        style = self._builder._subtitle_type
        render = renderers.get(style)
        if render is None:
            if style != "none":
                logger.warning("Unknown subtitle type: %s. Defaulting to 'None'", style)
            return self._visuals
        return render()

    @property
    def _voiceovers(self) -> list:
        return self._builder._project.get("voiceovers", [])

    def _invert_mask(self) -> VideoClip:
        return generate_invert_mask_text(
            video_size=self._builder._resolution,
            voiceover_data=single_word_timings(self._voiceovers),
            fonts=self._builder._fonts,
            visuals=self._visuals,
            add_border=self._builder._subtitle_border is not None,
        )

    def _border(self) -> VideoClip:
        return generate_border_text(
            video_size=self._builder._resolution,
            voiceover_data=single_word_timings(self._voiceovers),
            fonts=self._builder._fonts,
            visuals=self._visuals,
        )

    def _karaoke(self) -> VideoClip:
        fonts = self._builder._fonts
        if not fonts:
            raise ValueError("Karaoke subtitles need a font: call VideoBuilder.add_font() first")
        return generate_karaoke_text(
            segments=karaoke_segments(self._voiceovers),
            visuals=self._visuals,
            font=next(iter(fonts)),
            color=self._builder._subtitle_color or DEFAULT_SUBTITLE_COLOR,
            shadow=self._builder._subtitle_shadow,
            video_size=self._builder._resolution,
        )

    def _remotion_overlay(self) -> VideoClip:
        """Composite the pre-rendered Remotion subtitle video (its luminance is the mask)."""
        overlay_path = os.path.join(str(get_settings().remotion_app_dir), REMOTION_OVERLAY_PATH)
        overlay = VideoFileClip(overlay_path)
        overlay = overlay.with_mask(overlay.to_mask()).with_duration(self._visuals.duration)
        return CompositeVideoClip([self._visuals, overlay])
