"""Neon subtitle style.

Each word is filled with a neon edge-detected copy of the video and outlined with
a thin neon stroke, centred on the frame.
"""

import logging
from collections.abc import Iterable, Mapping
from typing import Any

import cv2
import numpy as np
from moviepy import CompositeVideoClip, ImageClip, TextClip, VideoClip

from app.pipeline.render.text.single_word import (
    WORD_MARGIN,
    centered_full_frame_mask,
    font_size_for_word,
    pick_font,
)

logger = logging.getLogger(__name__)

NEON_COLOR_RGB = (242, 228, 124)
SOBEL_KERNEL_SIZE = 5  # larger kernel -> thicker, smoother "neon tube" edges
EDGE_BRIGHTNESS_GAIN = 2.5
OUTLINE_STROKE_WIDTH = 2  # thinner gets eaten by the neon glow
TRANSPARENT = "rgba(0,0,0,0)"


def neon_edges(frame: np.ndarray) -> np.ndarray:
    """Turn an RGB frame into bright neon-coloured edges on black."""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=SOBEL_KERNEL_SIZE)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=SOBEL_KERNEL_SIZE)
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    magnitude = np.uint8(np.clip(magnitude * EDGE_BRIGHTNESS_GAIN, 0, 255))

    channels = [(magnitude * (component / 255.0)).astype(np.uint8) for component in NEON_COLOR_RGB]
    return np.dstack(channels)


def generate_border_text(
    video_size: tuple[int, int],
    fonts: Iterable[str],
    visuals: VideoClip,
    voiceover_data: list[Mapping[str, Any]],
) -> VideoClip:
    """Composite one neon word per entry of ``voiceover_data`` (``word``, ``start``, ``end``)."""
    layers: list[VideoClip] = [visuals]
    logger.info("Generating neon edges + borders for %d segments...", len(voiceover_data))

    for item in voiceover_data:
        word, start, end = item["word"], item["start"], item["end"]
        duration = end - start
        # Shared so the fill mask and the outline align exactly.
        text_params = {
            "text": word,
            "font": pick_font(fonts),
            "font_size": font_size_for_word(word),
            "method": "label",
            "size": (video_size[0], None),  # full width, so the text's x origin is 0
            "margin": WORD_MARGIN,
        }

        mask, (_, text_y) = centered_full_frame_mask(TextClip(**text_params, color="white"), video_size)
        fill = (
            visuals.subclipped(start, end)
            .image_transform(neon_edges)
            .with_mask(ImageClip(mask, is_mask=True).with_duration(duration))  # full-frame: no positioning
            .with_start(start)
        )
        outline = (
            TextClip(
                **text_params,
                color=TRANSPARENT,  # transparent interior so the neon fill shows through
                stroke_color=NEON_COLOR_RGB,
                stroke_width=OUTLINE_STROKE_WIDTH,
            )
            .with_start(start)
            .with_duration(duration)
            .with_position((0, text_y))
        )
        layers += [fill, outline]

    return CompositeVideoClip(layers)
