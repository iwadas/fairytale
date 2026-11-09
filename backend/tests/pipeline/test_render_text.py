"""Subtitle overlays: karaoke layout, neon/border and invert-mask word styles, Remotion overlay.

These build tiny moviepy clips in memory (no file is written except the Remotion overlay fixture).
"""

import numpy as np
import pytest

from app.pipeline.render.text.border_text_generator import NEON_COLOR_RGB, generate_border_text, neon_edges
from app.pipeline.render.text.invert_text_mask import generate_invert_mask_text
from app.pipeline.render.text.karaoke_text import generate_karaoke_text

from .conftest import requires_ffmpeg

KARAOKE_SIZE = (640, 640)


def _solid(size, color=(10, 20, 30), duration=1.0):
    from moviepy import ColorClip

    return ColorClip(size=size, color=color).with_duration(duration)


def _gradient(size, duration=1.0):
    from moviepy import ImageClip

    w, h = size
    row = np.linspace(0, 255, w, dtype=np.uint8)
    img = np.dstack([np.tile(row, (h, 1))] * 3)
    return ImageClip(img).with_duration(duration)


def _karaoke(font_path, words, shadow):
    segments = [{"start": 0.0, "end": 1.0, "words": words}]
    return generate_karaoke_text(
        segments=segments,
        visuals=_solid(KARAOKE_SIZE),
        font=font_path,
        color="white",
        shadow=shadow,
        video_size=KARAOKE_SIZE,
    )


def _final_pos(clip):
    return clip.pos(10.0)  # long after every drop animation finished


TWO_WORDS = [
    {"word": "Hello", "start": 0.0, "end": 0.3, "is_special": False},
    {"word": "world", "start": 0.3, "end": 0.6, "is_special": True},
]


# --- neon edge transform -----------------------------------------------------------------------


def test_neon_edges_on_flat_frame_is_black():
    out = neon_edges(np.full((16, 16, 3), 128, dtype=np.uint8))
    assert out.shape == (16, 16, 3)
    assert out.dtype == np.uint8
    assert out.max() == 0


def test_neon_edges_tints_edges_with_neon_colour():
    frame = np.zeros((16, 16, 3), dtype=np.uint8)
    frame[:, 8:] = 255
    out = neon_edges(frame)
    peak = out.reshape(-1, 3).max(axis=0)
    assert peak == pytest.approx(np.array(NEON_COLOR_RGB), abs=1)


# --- karaoke ---------------------------------------------------------------------------------------


def test_karaoke_with_shadow_adds_two_glows_per_word_on_one_centred_line(font_path):
    final = _karaoke(font_path, TWO_WORDS, shadow=True)

    overlays = final.clips[1:]
    assert len(overlays) == 3 * len(TWO_WORDS)
    glow_wide, glow_tight, hello, glow_wide_2, glow_tight_2, world = overlays

    (hx, hy), (wx, wy) = _final_pos(hello), _final_pos(world)
    assert hy == wy == 800 * KARAOKE_SIZE[1] / 1280
    assert wx > hx + hello.w
    left, right = hx, wx + world.w
    assert abs((left + right) / 2 - KARAOKE_SIZE[0] / 2) <= 2

    # Glows are padded/blurred copies, offset up-left by 2 * int(radius * 0.6).
    assert _final_pos(glow_tight) == (hx - 6, hy - 6)
    assert _final_pos(glow_wide) == (hx - 14, hy - 14)
    assert glow_wide.w > glow_tight.w > hello.w

    # Timing: each word appears at its own start and stays until the segment end.
    assert (hello.start, hello.end) == (0.0, 1.0)
    assert (world.start, world.end) == (0.3, 1.0)
    assert (glow_wide_2.start, glow_tight_2.start) == (0.3, 0.3)

    # The drop animation starts above-below the resting line and lands on it.
    assert hello.pos(0)[1] > hy
    assert final.get_frame(0.5).shape == (*KARAOKE_SIZE[::-1], 3)


def test_karaoke_wraps_long_segments_into_lines(font_path):
    words = [{"word": w, "start": i * 0.05, "end": i * 0.05 + 0.05} for i, w in enumerate("the quick brown fox jumps over the lazy dog again and again".split())]
    final = _karaoke(font_path, words, shadow=True)

    word_clips = final.clips[1:][2::3]
    ys = sorted({_final_pos(c)[1] for c in word_clips})
    assert len(ys) >= 2
    line_step = int(30 * 640 / 720) + 14 * 640 / 720
    assert ys[1] - ys[0] == pytest.approx(line_step)
    max_line = int(500 * 640 / 720)
    for y in ys:
        line = [c for c in word_clips if _final_pos(c)[1] == y]
        span = max(_final_pos(c)[0] + c.w for c in line) - min(_final_pos(c)[0] for c in line)
        assert span <= max_line


def test_karaoke_without_shadow_keeps_every_word(font_path):
    """Regression: with shadow disabled every word used to be dropped (UnboundLocalError)."""
    final = _karaoke(font_path, TWO_WORDS, shadow=False)

    overlays = final.clips[1:]
    assert len(overlays) == len(TWO_WORDS)
    assert [c.start for c in overlays] == [0.0, 0.3]
    assert final.get_frame(0.5).shape == (*KARAOKE_SIZE[::-1], 3)


# --- border (neon) and invert-mask single-word styles ----------------------------------------------

WORD_SIZE = (360, 360)
WORDS = [{"word": "HI", "start": 0.0, "end": 0.5}, {"word": "WONDERLAND", "start": 0.5, "end": 1.0}]


def test_border_text_adds_fill_and_outline_per_word(font_path):
    visuals = _gradient(WORD_SIZE)
    final = generate_border_text(video_size=WORD_SIZE, fonts={font_path}, visuals=visuals, voiceover_data=WORDS)

    assert final.clips[0] is visuals
    fill, outline = final.clips[1], final.clips[2]
    assert len(final.clips) == 1 + 2 * len(WORDS)
    assert fill.start == 0.0 and fill.duration == 0.5
    assert fill.mask.size == WORD_SIZE
    assert outline.pos(0)[0] == 0
    assert final.get_frame(0.25).shape == (WORD_SIZE[1], WORD_SIZE[0], 3)
    assert final.get_frame(0.75).shape == (WORD_SIZE[1], WORD_SIZE[0], 3)


@pytest.mark.parametrize("add_border", [True, False])
def test_invert_mask_text(font_path, add_border):
    visuals = _gradient(WORD_SIZE)
    final = generate_invert_mask_text(
        video_size=WORD_SIZE, fonts={font_path}, visuals=visuals, voiceover_data=WORDS, add_border=add_border
    )

    per_word = 2 if add_border else 1
    assert len(final.clips) == 1 + per_word * len(WORDS)
    inverted = final.clips[1]
    assert inverted.start == 0.0 and inverted.duration == 0.5
    assert inverted.mask.size == WORD_SIZE
    # The mask is a centred knockout of the word: inside the text the frame is inverted.
    frame = final.get_frame(0.25)
    assert frame.shape == (WORD_SIZE[1], WORD_SIZE[0], 3)
    assert not np.array_equal(frame, visuals.get_frame(0.25))


# --- Remotion overlay (live export path) -------------------------------------------------------------


@requires_ffmpeg
def test_remotion_overlay_is_composited_over_visuals(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from moviepy import ColorClip

    from app.pipeline.render import subtitles
    from app.pipeline.render.builder import VideoBuilder

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    overlay = ColorClip(size=(64, 64), color=(255, 255, 255)).with_duration(0.5).with_fps(10)
    overlay.write_videofile(str(out_dir / "video.mov"), codec="libx264", audio=False, logger=None)
    monkeypatch.setattr(subtitles, "get_settings", lambda: SimpleNamespace(remotion_app_dir=tmp_path))

    builder = VideoBuilder({}, "o.mp4").set_resolution(64, 64).set_subtitle_style("karaoke_remotion")
    visuals = _solid((64, 64), duration=2.0)

    final = subtitles.SubtitleGenerator(builder=builder, visuals=visuals).generate()

    assert final.clips[0] is visuals
    assert final.duration == 2.0
    assert final.clips[1].duration == 2.0
    assert final.size == (64, 64)
    final.clips[1].close()


def test_subtitle_style_none_returns_visuals_unchanged():
    from app.pipeline.render.builder import VideoBuilder
    from app.pipeline.render.subtitles import SubtitleGenerator

    visuals = _solid((8, 8))
    builder = VideoBuilder({}, "o.mp4").set_subtitle_style("none")
    assert SubtitleGenerator(builder=builder, visuals=visuals).generate() is visuals
