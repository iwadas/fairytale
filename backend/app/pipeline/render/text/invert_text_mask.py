"""Invert-mask subtitle style: each word is a centred knockout showing the colour-inverted video."""

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from moviepy import CompositeVideoClip, ImageClip, TextClip, VideoClip, vfx

from app.pipeline.render.text.single_word import (
    WORD_MARGIN,
    centered_full_frame_mask,
    font_size_for_word,
    pick_font,
)

logger = logging.getLogger(__name__)

MASK_STROKE_WIDTH = 2  # widens the knockout slightly
BORDER_STROKE_WIDTH = 1
BORDER_COLOR = "white"
TRANSPARENT = "rgba(0,0,0,0)"


def generate_invert_mask_text(
    video_size: tuple[int, int],
    fonts: Iterable[str],
    visuals: VideoClip,
    voiceover_data: list[Mapping[str, Any]],
    add_border: bool = True,
) -> VideoClip:
    """Composite one inverted word per entry of ``voiceover_data`` (``word``, ``start``, ``end``).

    With ``add_border`` a thin white outline is drawn on top of each word.
    """
    layers: list[VideoClip] = [visuals]
    logger.debug("Available fonts: %s", fonts)
    inverted_visuals = visuals.with_effects([vfx.InvertColors()])

    for item in voiceover_data:
        word, start, end = item["word"], item["start"], item["end"]
        duration = end - start
        text_params = {
            "text": word,
            "font": pick_font(fonts),
            "font_size": font_size_for_word(word),
            "method": "label",
            "margin": WORD_MARGIN,
            "size": (video_size[0], None),
        }
        logger.debug("Processing '%s' with font: %s", word, text_params["font"])

        cutter = TextClip(**text_params, color="white", stroke_color="white", stroke_width=MASK_STROKE_WIDTH)
        mask, _ = centered_full_frame_mask(cutter, video_size)
        layers.append(
            inverted_visuals.subclipped(start, end)
            .with_mask(ImageClip(mask, is_mask=True).with_duration(duration))
            .with_start(start)
        )

        if add_border:
            border = TextClip(
                **text_params,
                color=TRANSPARENT,
                stroke_color=BORDER_COLOR,
                stroke_width=BORDER_STROKE_WIDTH,
            )
            layers.append(border.with_position(("center", "center")).with_start(start).with_duration(duration))

    return CompositeVideoClip(layers)
