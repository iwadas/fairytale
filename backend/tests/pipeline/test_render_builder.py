"""VideoBuilder: fluent configuration, timeline math, visual layout and a tiny end-to-end render."""

import os

import pytest

from app.pipeline.render.builder import VideoBuilder
from app.pipeline.render.visual import VisualGenerator

from .conftest import requires_ffmpeg


def test_fluent_setters_return_builder_and_store_config():
    builder = VideoBuilder(project={}, output_filename="out.mp4")

    same = (
        builder.set_resolution(640, 640)
        .set_subtitle_style("karaoke_remotion")
        .add_font("a.ttf")
        .add_font("a.ttf")
        .add_subtitle_shadow()
        .set_subtitle_color("white")
        .set_subtitle_special_color("rgb(230, 163, 49)")
        .set_subtitle_border(width=2, color="yellow")
    )

    assert same is builder
    assert builder._resolution == (640, 640)
    assert builder._subtitle_type == "karaoke_remotion"
    assert builder._fonts == {"a.ttf"}
    assert builder._subtitle_shadow is True
    assert builder._subtitle_color == "white"
    assert builder._subtitle_special_color == "rgb(230, 163, 49)"
    assert builder._subtitle_border == {"width": 2, "color": "yellow"}


def test_defaults():
    builder = VideoBuilder(project={}, output_filename="out.mp4")
    assert builder._resolution == (720, 1280)
    assert builder._fps == 24
    assert builder._subtitle_type == "border"
    assert builder._subtitle_shadow is False
    assert builder._fonts == set()


@pytest.mark.parametrize("style", ["none", "invert_mask", "border", "karaoke", "karaoke_remotion"])
def test_supported_subtitle_styles(style):
    assert VideoBuilder({}, "o.mp4").set_subtitle_style(style)._subtitle_type == style


def test_unsupported_subtitle_style_raises():
    with pytest.raises(ValueError):
        VideoBuilder({}, "o.mp4").set_subtitle_style("comic_sans")


def test_element_duration_and_end_time_subtract_cuts():
    builder = VideoBuilder({}, "o.mp4")
    element = {"start_time": "2", "duration": 10, "cut_start": 1.5, "cut_end": "0.5"}

    assert builder.get_element_duration(element) == 8.0
    assert builder.get_element_end_time(element) == 10.0
    assert builder.get_element_duration({}) == 0.0
    assert builder.get_element_end_time({}) == 0.0


def test_project_duration_is_latest_end_over_all_tracks():
    project = {
        "scenes": [{"start_time": 0, "duration": 3}, {"start_time": 3, "duration": 3}],
        "voiceovers": [{"start_time": 1, "duration": 6.5, "cut_end": 0.25}],
        "background_music": [{"start_time": 0, "duration": 4}],
    }
    assert VideoBuilder(project, "o.mp4").get_project_duration() == 7.25
    assert VideoBuilder({}, "o.mp4").get_project_duration() == 0.0


@requires_ffmpeg
def test_visuals_fit_inside_resolution_and_order_layers(tiny_video):
    project = {
        "scenes": [
            {"video_src": tiny_video, "start_time": 0, "duration": 1, "layer": 0},
            {"video_src": tiny_video, "start_time": 0.5, "duration": 1, "cut_start": 0.5, "layer": 1},
            {"video_src": "", "start_time": 0, "duration": 1, "layer": 1},  # skipped: no source
        ]
    }
    builder = VideoBuilder(project, "o.mp4").set_resolution(64, 64)

    composite = VisualGenerator(builder).generate()

    assert composite.size == (64, 64)
    assert composite.duration == 1.0  # latest end: 0.5 + (1 - 0.5 cut)
    # Higher layers are composited first (i.e. underneath).
    assert [c.start for c in composite.clips] == [0.5, 0]
    # 32x48 scaled by min(64/32, 64/48) keeps the aspect ratio.
    assert all(c.size == (42, 64) for c in composite.clips)
    assert composite.clips[0].duration == pytest.approx(0.5)
    frame = composite.get_frame(0.25)
    assert frame.shape == (64, 64, 3)
    composite.close()


@requires_ffmpeg
def test_build_renders_a_tiny_video(tiny_video, tiny_wav, tmp_path):
    output = tmp_path / "render.mp4"
    project = {
        "scenes": [{"video_src": tiny_video, "start_time": 0, "duration": 1}],
        "voiceovers": [{"src": tiny_wav, "start_time": 0, "duration": 1, "timestamps": []}],
        "background_music": [{"src": "missing.mp3", "start_time": 0, "duration": 0.5}],
    }

    result = VideoBuilder(project, str(output)).set_resolution(64, 64).set_subtitle_style("none").build()

    assert result == str(output)
    assert os.path.getsize(output) > 0

    from moviepy import VideoFileClip

    clip = VideoFileClip(str(output))
    try:
        assert clip.size == [64, 64]
        assert clip.duration == pytest.approx(1.0, abs=0.15)
        assert clip.audio is not None
    finally:
        clip.close()
