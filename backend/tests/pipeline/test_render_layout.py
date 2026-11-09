"""Pure layout/geometry helpers extracted from the moviepy renderer."""

import numpy as np
import pytest

from app.pipeline.render.text.karaoke_text import (
    KaraokeLayout,
    _black_silhouette,
    clamp_to_frame,
    drop_in,
    layout_words,
    wrap_into_lines,
)
from app.pipeline.render.text.single_word import centered_full_frame_mask, font_size_for_word
from app.pipeline.render.visual import fit_within, z_ordered
from app.pipeline.render.word_timing import normalize_display_word


def test_normalize_display_word_punctuation_only_becomes_empty():
    assert normalize_display_word(" — ") == ""
    assert normalize_display_word("hello ,") == "HELLO "  # inner whitespace is kept, as before


def test_layout_scales_from_reference_resolution():
    assert KaraokeLayout.for_video((720, 1280)) == KaraokeLayout(
        video_width=720, video_height=1280, font_size=53, line_spacing=14 * (1280 / 720),
        word_gap=7, max_line_width=500, top_y=800.0, drop_offset=10.0,
    )
    small = KaraokeLayout.for_video((640, 640))
    assert (small.font_size, small.word_gap, small.max_line_width, small.top_y, small.drop_offset) == (26, 6, 444, 400.0, 5.0)


@pytest.mark.parametrize(
    ("widths", "expected"),
    [
        ([], []),
        ([10, 10, 10], [[0, 1, 2]]),  # 10 + 2 + 10 + 2 + 10 = 34 <= 34
        ([10, 10, 11], [[0, 1], [2]]),
        ([50, 5, 5], [[0], [1, 2]]),  # an over-wide word gets its own line
        ([20, 20, 20, 20], [[0], [1], [2], [3]]),
    ],
)
def test_wrap_into_lines(widths, expected):
    assert wrap_into_lines(widths, gap=2, max_width=34) == expected


def test_layout_words_centres_each_line_and_stacks_lines():
    layout = KaraokeLayout(
        video_width=100, video_height=100, font_size=10, line_spacing=2.5,
        word_gap=4, max_line_width=60, top_y=20.0, drop_offset=5.0,
    )
    positions = layout_words([20, 20, 30], layout)

    # Line 1: 20 + 4 + 20 = 44 wide -> starts at (100-60)//2 + (60-44)//2 = 28.
    assert positions == [(28, 20.0), (52, 20.0), (35, 32.5)]


def test_clamp_to_frame():
    assert clamp_to_frame((90, -5), (20, 10), (100, 100)) == (80, 0)
    assert clamp_to_frame((10, 10), (20, 10), (100, 100)) == (10, 10)
    assert clamp_to_frame((10, 10), (200, 10), (100, 100)) == (0, 10)


def test_drop_in_eases_onto_resting_position():
    position = drop_in(5, 50.0, duration=1.0, drop_offset=8.0)
    assert position(0) == (5, 58.0)
    assert position(0.5) == (5, 50.0 + 8.0 * 0.25)
    assert position(1.0) == position(3.0) == (5, 50.0)


def test_black_silhouette_thresholds_brightness_into_alpha():
    frame = np.zeros((2, 3, 3), dtype=np.uint8)
    frame[0, 0] = 255
    frame[1, 2] = 40  # below threshold
    rgba = np.asarray(_black_silhouette(frame))
    assert rgba.shape == (2, 3, 4)
    assert rgba[..., :3].max() == 0
    assert rgba[..., 3].tolist() == [[255, 0, 0], [0, 0, 0]]


@pytest.mark.parametrize(("word", "size"), [("A", 120), ("ABCD", 120), ("ABCDE", 100), ("ABCDEFG", 80), ("ABCDEFGHIJ", 60)])
def test_font_size_for_word(word, size):
    assert font_size_for_word(word) == size


class _FakeMask:
    def __init__(self, array):
        self._array = array

    def get_frame(self, t):
        return self._array


class _FakeTextClip:
    def __init__(self, array):
        self.mask = _FakeMask(array)


def test_centered_full_frame_mask():
    text = np.ones((2, 4))
    mask, (x, y) = centered_full_frame_mask(_FakeTextClip(text), (8, 6))
    assert (x, y) == (2, 2)
    assert mask.shape == (6, 8)
    assert mask.sum() == 8
    assert mask[2:4, 2:6].all()


def test_fit_within_keeps_aspect_ratio():
    assert fit_within((32, 48), (64, 64)) == (42, 64)
    assert fit_within((1920, 1080), (640, 640)) == (640, 360)
    assert fit_within((640, 640), (640, 640)) == (640, 640)


def test_z_ordered_highest_layer_first_then_start_time():
    scenes = [
        {"id": "a", "start_time": 3, "layer": 1},
        {"id": "b", "start_time": 0},
        {"id": "c", "start_time": 0, "layer": 1},
        {"id": "d", "start_time": "1.5", "layer": 2},
    ]
    assert [s["id"] for s in z_ordered(scenes)] == ["d", "c", "a", "b"]


def test_karaoke_style_requires_a_font():
    from moviepy import ColorClip

    from app.pipeline.render.builder import VideoBuilder
    from app.pipeline.render.subtitles import SubtitleGenerator

    builder = VideoBuilder({"voiceovers": []}, "o.mp4").set_subtitle_style("karaoke")
    with pytest.raises(ValueError, match="font"):
        SubtitleGenerator(builder=builder, visuals=ColorClip((8, 8), color=(0, 0, 0)).with_duration(1)).generate()
