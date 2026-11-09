"""In-memory stand-ins for the external providers (LLM / TTS / video diffusion)
and the video renderer.

The fixtures in ``conftest.py`` patch the provider classes' async ``create``
factories (and ``VideoBuilder.build``) on the classes themselves, so every
import site gets the fake and no network or MoviePy work happens.
"""

from typing import Any, Callable


class FakeLLM:
    """Answers ``generate`` from ``answers``, keyed by the response model name.

    An answer is either a ready value or a ``callable(messages) -> value``.
    Every call is recorded in ``calls`` as ``(response_format_name, messages)``.
    """

    def __init__(self):
        self.answers: dict[str, Any] = {}
        self.calls: list[tuple[str, Any]] = []

    async def generate(self, messages: Any = None, response_format: Any = None, temperature: float = 0.7):
        name = response_format.__name__
        self.calls.append((name, messages))
        if name not in self.answers:
            raise AssertionError(f"FakeLLM has no answer for {name}")
        answer = self.answers[name]
        value = answer(messages) if callable(answer) else answer
        if isinstance(value, dict):
            value = response_format(**value)
        return value


class FakeTTS:
    """Returns ``result`` from ``generate`` and records the requested texts."""

    def __init__(self):
        self.result: dict[str, Any] | None = None
        self.texts: list[str] = []

    async def generate(self, progress_callback: Callable | None = None, **kwargs):
        self.texts.append(kwargs.get("text"))
        return self.result


class FakeDiffusion:
    """Returns ``src`` from ``generate`` and records the call arguments."""

    def __init__(self):
        self.src = "static/videos/scenes/generated.mp4"
        self.calls: list[dict[str, Any]] = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.src


class RenderRecorder:
    """Captures what ``VideoBuilder.build`` would have rendered."""

    def __init__(self):
        self.builds: list[dict[str, Any]] = []

    def record(self, builder) -> None:
        # Private builder state; getattr keeps the recorder tolerant of renames.
        attrs = (
            "_project", "_output_filename", "_resolution", "_subtitle_type",
            "_subtitle_color", "_subtitle_special_color", "_subtitle_shadow", "_fonts",
        )
        self.builds.append({name.lstrip("_"): getattr(builder, name, None) for name in attrs})
