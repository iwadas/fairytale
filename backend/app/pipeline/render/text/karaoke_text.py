"""Karaoke subtitles rendered with moviepy: words of a segment drop in one by one,
optionally with a soft dark glow, and stay until the segment ends.

Legacy renderer; the live export path uses a Remotion overlay instead.
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from moviepy import ColorClip, CompositeVideoClip, ImageClip, TextClip, VideoClip
from moviepy.video.fx import CrossFadeIn
from PIL import Image, ImageFilter

from app.pipeline.render.word_timing import KaraokeSegment

logger = logging.getLogger(__name__)

DEFAULT_VIDEO_SIZE = (720, 1280)
DEFAULT_TEXT_COLOR = "white"

# Layout values are tuned for a 720x1280 portrait frame and scaled to the actual one
# (see KaraokeLayout.for_video): font size and line spacing by height/720, word gap and
# line width by width/720, vertical position and drop distance by height/1280.
BASE_FONT_SIZE = 30
BASE_LINE_SPACING = 14
BASE_WORD_GAP = 7
BASE_MAX_LINE_WIDTH = 500
BASE_TOP_Y = 800
BASE_DROP_OFFSET = 10
REFERENCE_SHORT_SIDE = 720
REFERENCE_LONG_SIDE = 1280

TEXT_MARGIN = (0, 30)
TRANSPARENT_RGBA = (0, 0, 0, 0)
PLACEHOLDER_EXTRA_HEIGHT = 10

# Glow (shadow): two blurred black silhouettes behind each word, widest first.
GLOW_BLUR_RADII = (12, 5)
GLOW_OFFSET_RATIO = 0.6
GLOW_PADDING_FACTOR = 3
SILHOUETTE_THRESHOLD = 50

Position = tuple[float, float]


@dataclass(frozen=True)
class KaraokeLayout:
    video_width: int
    video_height: int
    font_size: int
    line_spacing: float
    word_gap: int
    max_line_width: int
    top_y: float
    drop_offset: float

    @classmethod
    def for_video(cls, video_size: tuple[int, int]) -> "KaraokeLayout":
        width, height = video_size
        return cls(
            video_width=width,
            video_height=height,
            font_size=int(BASE_FONT_SIZE * (height / REFERENCE_SHORT_SIDE)),
            line_spacing=BASE_LINE_SPACING * (height / REFERENCE_SHORT_SIDE),
            word_gap=int(BASE_WORD_GAP * (width / REFERENCE_SHORT_SIDE)),
            max_line_width=int(BASE_MAX_LINE_WIDTH * (width / REFERENCE_SHORT_SIDE)),
            top_y=BASE_TOP_Y * (height / REFERENCE_LONG_SIDE),
            drop_offset=BASE_DROP_OFFSET * (height / REFERENCE_LONG_SIDE),
        )


# --- Layout math (pure) ---------------------------------------------------------------------


def wrap_into_lines(widths: Sequence[int], gap: int, max_width: int) -> list[list[int]]:
    """Greedy word wrap on pixel widths; returns the word indices of each line.

    A word wider than ``max_width`` still gets a line of its own.
    """
    lines: list[list[int]] = []
    current: list[int] = []
    current_width = 0
    for index, width in enumerate(widths):
        added = width + gap if current_width > 0 else width
        if current_width + added > max_width and current:
            lines.append(current)
            current, current_width = [index], width
        else:
            current.append(index)
            current_width += added
    if current:
        lines.append(current)
    return lines


def layout_words(widths: Sequence[int], layout: KaraokeLayout) -> list[Position]:
    """Resting (x, y) of every word: lines stacked from ``top_y``, each centred horizontally."""
    gap, max_width = layout.word_gap, layout.max_line_width
    positions: list[Position] = [(0, 0)] * len(widths)
    y = layout.top_y
    for line in wrap_into_lines(widths, gap, max_width):
        line_width = sum(widths[i] + gap for i in line) - gap
        x = (layout.video_width - max_width) // 2 + (max_width - line_width) // 2
        for i in line:
            positions[i] = (x, y)
            x += widths[i] + gap
        y += layout.font_size + layout.line_spacing
    return positions


def clamp_to_frame(position: Position, size: tuple[int, int], frame_size: tuple[int, int]) -> Position:
    """Shift a clip so it stays inside the frame (top-left wins if it is larger)."""
    x = max(0, min(position[0], frame_size[0] - size[0]))
    y = max(0, min(position[1], frame_size[1] - size[1]))
    return x, y


def drop_in(x: float, y: float, duration: float, drop_offset: float) -> Callable[[float], Position]:
    """Position over time: start ``drop_offset`` px low and ease out (quadratic) onto (x, y)."""

    def position(t: float) -> Position:
        if t < duration:
            eased = 1 - (1 - t / duration) ** 2
            return x, y + drop_offset * (1 - eased)
        return x, y

    return position


# --- Clip building -----------------------------------------------------------------------------


def generate_karaoke_text(
    segments: Sequence[KaraokeSegment],
    visuals: VideoClip,
    *,
    font: str,
    color: str = DEFAULT_TEXT_COLOR,
    shadow: bool = False,
    video_size: tuple[int, int] = DEFAULT_VIDEO_SIZE,
) -> VideoClip:
    """Composite karaoke subtitles for ``segments`` (see ``word_timing.karaoke_segments``) over ``visuals``.

    Each word appears at its own ``start``, drops in over its own duration and stays
    until the segment ``end``.
    """
    layout = KaraokeLayout.for_video(video_size)
    clips: list[VideoClip] = []

    for segment in segments:
        words = segment["words"]
        widths = [_text_width(word["word"], font, layout.font_size) for word in words]

        for word, width, position in zip(words, widths, layout_words(widths, layout)):
            try:
                clips += _word_clips(
                    text=word["word"],
                    start=word["start"],
                    end=segment["end"],
                    animation_duration=word["end"] - word["start"],
                    width=width,
                    position=position,
                    font=font,
                    color=color,
                    shadow=shadow,
                    layout=layout,
                )
            except Exception:
                logger.exception("Failed to create TextClip for word: '%s'", word["word"])

    return CompositeVideoClip([visuals, *clips])


def _text_width(text: str, font: str, font_size: int) -> int:
    probe = TextClip(text=text, font=font, font_size=font_size, method="label")
    width = probe.size[0]
    probe.close()
    return width


def _word_clips(
    *,
    text: str,
    start: float,
    end: float,
    animation_duration: float,
    width: int,
    position: Position,
    font: str,
    color: str,
    shadow: bool,
    layout: KaraokeLayout,
) -> list[VideoClip]:
    """The word clip, preceded by its glow clips when ``shadow`` is on (bottom to top)."""
    clip = TextClip(
        text=text,
        font_size=layout.font_size,
        color=color,
        font=font,
        bg_color=TRANSPARENT_RGBA,
        margin=TEXT_MARGIN,
        method="label",
        size=(width, None),
    )
    if clip.w == 0 or clip.h == 0:
        logger.warning("TextClip has zero size; falling back to a placeholder ColorClip")
        clip = ColorClip(size=(width, layout.font_size + PLACEHOLDER_EXTRA_HEIGHT), color=color).with_duration(end - start)

    x, y = clamp_to_frame(position, clip.size, (layout.video_width, layout.video_height))
    fade_in = animation_duration / 2
    clip = (
        clip.with_position(drop_in(x, y, animation_duration, layout.drop_offset))
        .with_start(start)
        .with_duration(end - start)
        .with_effects([CrossFadeIn(fade_in)])
    )
    if not shadow:
        return [clip]

    glows = [
        _glow_clip(clip, radius, (x, y), start, end - start, fade_in, layout.drop_offset)
        for radius in GLOW_BLUR_RADII
    ]
    return [*glows, clip]


def _black_silhouette(frame: np.ndarray) -> Image.Image:
    """Opaque black where the frame is bright (the text), transparent elsewhere."""
    gray = np.asarray(Image.fromarray(frame.astype("uint8")).convert("L"))
    rgba = np.zeros((*gray.shape, 4), dtype=np.uint8)
    rgba[..., 3] = np.where(gray > SILHOUETTE_THRESHOLD, 255, 0)
    return Image.fromarray(rgba)  # 4 x uint8 -> RGBA


def _glow_clip(
    text_clip: VideoClip,
    blur_radius: int,
    position: Position,
    start: float,
    duration: float,
    animation_duration: float,
    drop_offset: float,
) -> VideoClip:
    """A blurred black silhouette of ``text_clip`` placed slightly up-left of ``position``."""
    silhouette = _black_silhouette(text_clip.get_frame(0))
    offset = int(blur_radius * GLOW_OFFSET_RATIO)
    padding = blur_radius * GLOW_PADDING_FACTOR

    canvas = Image.new("RGBA", (silhouette.width + padding, silhouette.height + padding), TRANSPARENT_RGBA)
    canvas.paste(silhouette, (blur_radius + offset, blur_radius + offset), silhouette)
    glow = canvas.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    x, y = position[0] - 2 * offset, position[1] - 2 * offset
    return (
        ImageClip(np.array(glow))
        .with_duration(duration)
        .with_start(start)
        .with_position(drop_in(x, y, animation_duration, drop_offset))
        .with_effects([CrossFadeIn(animation_duration / 2)])
    )
