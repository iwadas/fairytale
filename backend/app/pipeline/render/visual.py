"""Scene videos composited into the project timeline."""

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from moviepy import CompositeVideoClip, VideoClip, VideoFileClip

if TYPE_CHECKING:
    from app.pipeline.render.builder import VideoBuilder

logger = logging.getLogger(__name__)

Scene = Mapping[str, Any]


def fit_within(size: tuple[int, int], bounds: tuple[int, int]) -> tuple[int, int]:
    """Largest size with the same aspect ratio as ``size`` that fits inside ``bounds``."""
    scale = min(bounds[0] / size[0], bounds[1] / size[1])
    return int(size[0] * scale), int(size[1] * scale)


def z_ordered(scenes: list[Scene]) -> list[Scene]:
    """Composite order: highest ``layer`` first (i.e. at the bottom), then by start time."""
    by_start = sorted(scenes, key=lambda scene: float(scene["start_time"]))
    return sorted(by_start, key=lambda scene: scene.get("layer", 0), reverse=True)  # stable


class VisualGenerator:
    def __init__(self, builder: "VideoBuilder"):
        self._builder = builder

    def generate(self) -> VideoClip:
        """Each scene: ``video_src``, ``start_time``, ``duration``, optional ``cut_start``/``cut_end``/``layer``."""
        scenes = self._builder._project.get("scenes", [])
        clips = [clip for scene in z_ordered(scenes) if (clip := self._scene_clip(scene)) is not None]
        return CompositeVideoClip(clips, size=self._builder._resolution).with_duration(
            self._builder.get_project_duration()
        )

    def _scene_clip(self, scene: Scene) -> VideoClip | None:
        src = scene.get("video_src")
        start_time = float(scene["start_time"])
        if not src or not str(src).strip():
            logger.warning("Skipping scene at %ss - no video_src: %s", start_time, scene)
            return None

        try:
            clip = VideoFileClip(src)
        except Exception as e:
            raise RuntimeError(f"Cannot load scene video {src}: {e}") from e

        cut_start = float(scene.get("cut_start", 0))
        clip = clip.subclipped(cut_start, self._builder.get_element_duration(scene) + cut_start).with_start(start_time)

        resolution = self._builder._resolution
        if (clip.w, clip.h) != tuple(resolution):
            # Letterbox: keep the aspect ratio and centre the clip.
            clip = clip.resized(new_size=fit_within((clip.w, clip.h), resolution)).with_position("center")
        return clip
