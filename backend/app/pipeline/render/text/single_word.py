"""Helpers shared by the one-word-at-a-time subtitle styles (border/neon and invert mask)."""

import random
from collections.abc import Iterable

import numpy as np
from moviepy import TextClip

# Vertical text margin (px) so ascenders/descenders are never clipped.
WORD_MARGIN = (0, 90)

# (minimum word length, font size): longer words get smaller fonts.
FONT_SIZE_BY_LENGTH = ((10, 60), (7, 80), (5, 100))
MAX_FONT_SIZE = 120


def font_size_for_word(word: str) -> int:
    for min_length, size in FONT_SIZE_BY_LENGTH:
        if len(word) >= min_length:
            return size
    return MAX_FONT_SIZE


def pick_font(fonts: Iterable[str]) -> str:
    return random.choice(list(fonts))


def centered_full_frame_mask(text_clip: TextClip, frame_size: tuple[int, int]) -> tuple[np.ndarray, tuple[int, int]]:
    """Paste the text clip's mask, centred, into a frame-sized black mask.

    Returns the mask array (height x width, floats 0..1) and the top-left (x, y)
    where the text was placed.
    """
    if text_clip.mask is None:
        text_clip = text_clip.with_mask()
    text_mask = text_clip.mask.get_frame(0)
    text_h, text_w = text_mask.shape
    frame_w, frame_h = frame_size

    x = (frame_w - text_w) // 2
    y = (frame_h - text_h) // 2
    x_end = min(x + text_w, frame_w)
    y_end = min(y + text_h, frame_h)

    mask = np.zeros((frame_h, frame_w), dtype=float)
    mask[y:y_end, x:x_end] = text_mask[: y_end - y, : x_end - x]
    return mask, (x, y)
