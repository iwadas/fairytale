"""Fixtures for the moviepy render pipeline tests (tiny media generated on the fly, no network)."""

from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
FONT_PATH = str(BACKEND_DIR / "static" / "default" / "fonts" / "Unna-Regular.ttf")


def _ffmpeg_available() -> bool:
    try:
        import imageio_ffmpeg

        return Path(imageio_ffmpeg.get_ffmpeg_exe()).exists()
    except Exception:
        return False


requires_ffmpeg = pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg binary not available")


@pytest.fixture(scope="session")
def font_path() -> str:
    if not Path(FONT_PATH).exists():
        pytest.skip(f"font not found: {FONT_PATH}")
    return FONT_PATH


@pytest.fixture(scope="session")
def tiny_video(tmp_path_factory) -> str:
    """A 1 s, 32x48, 10 fps solid-colour mp4."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg binary not available")
    from moviepy import ColorClip

    path = tmp_path_factory.mktemp("media") / "scene.mp4"
    clip = ColorClip(size=(32, 48), color=(200, 30, 30)).with_duration(1).with_fps(10)
    clip.write_videofile(str(path), codec="libx264", audio=False, logger=None)
    clip.close()
    return str(path)


@pytest.fixture(scope="session")
def tiny_wav(tmp_path_factory) -> str:
    """A 1 s silent wav (pydub reads/writes wav without ffmpeg)."""
    from pydub import AudioSegment

    path = tmp_path_factory.mktemp("media") / "voice.wav"
    AudioSegment.silent(duration=1000).export(str(path), format="wav")
    return str(path)
