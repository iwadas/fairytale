"""Project soundtrack: background music and voiceovers mixed onto a silent timeline."""

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from pydub import AudioSegment

if TYPE_CHECKING:
    from app.pipeline.render.builder import VideoBuilder

MS_PER_SECOND = 1000


def _ms(seconds: Any) -> int:
    return int(float(seconds) * MS_PER_SECOND)


def _by_start_time(elements: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(elements, key=lambda element: float(element.get("start_time", 0)))


class AudioGenerator:
    def __init__(self, builder: "VideoBuilder", output_path: str):
        self._builder = builder
        self._output_path = output_path

    def generate(self) -> str:
        """Mix all music, then all voiceovers (each by start time) and export a WAV; returns its path."""
        project = self._builder._project
        audio = AudioSegment.silent(duration=self._builder.get_project_duration() * MS_PER_SECOND)

        for element in _by_start_time(project.get("background_music", [])):
            audio = self._overlay(audio, element)
        for element in _by_start_time(project.get("voiceovers", [])):
            audio = self._overlay(audio, element)

        audio.export(self._output_path, format="wav")
        return self._output_path

    @staticmethod
    def _overlay(audio: AudioSegment, element: Mapping[str, Any]) -> AudioSegment:
        """Overlay the element's trimmed audio at its start time; missing files are skipped."""
        src = element.get("src")
        if not src or not os.path.exists(src):
            return audio

        try:
            segment = AudioSegment.from_file(src)
        except Exception as e:
            raise RuntimeError(f"Cannot load audio {src}: {e}") from e

        cut_start = _ms(element.get("cut_start", 0))
        cut_end = _ms(element.get("cut_end", 0))
        trimmed = segment[cut_start : len(segment) - cut_end] if cut_end else segment[cut_start:]
        return audio.overlay(trimmed, position=_ms(element.get("start_time", 0)))
