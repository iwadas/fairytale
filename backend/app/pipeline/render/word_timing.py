"""Turn voiceover word timestamps into absolute subtitle timelines (pure functions).

Timestamps inside a voiceover are relative to the voiceover; every function here
shifts them by the voiceover's ``start_time`` so they are relative to the project.
"""

from collections.abc import Iterable, Mapping
from typing import Any, TypedDict

# Punctuation stripped from the edges of words shown one at a time.
GLUE_PUNCTUATION = ",.?!:;-–—"
# Marker that TTS inserts into ``text_with_pauses`` between karaoke segments.
PAUSE_TOKEN = "[PAUSE]"

Voiceover = Mapping[str, Any]


class KaraokeWord(TypedDict):
    word: str
    is_special: bool
    start: float
    end: float


class KaraokeSegment(TypedDict):
    words: list[KaraokeWord]
    start: float
    end: float | None


def normalize_display_word(word: str) -> str:
    """Upper-case the word and strip surrounding whitespace and glue punctuation."""
    return word.strip().upper().strip(GLUE_PUNCTUATION)


def single_word_timings(voiceovers: Iterable[Voiceover]) -> list[dict[str, Any]]:
    """One entry per spoken word (from ``timestamps``), with absolute times.

    Extra keys of each timestamp are kept; ``word`` is normalised for display.
    """
    result = []
    for voiceover in voiceovers:
        offset = float(voiceover.get("start_time", 0.0))
        for stamp in voiceover.get("timestamps", []):
            result.append(
                {
                    **stamp,
                    "word": normalize_display_word(stamp["word"]),
                    "start": float(stamp["start"]) + offset,
                    "end": float(stamp["end"]) + offset,
                }
            )
    return result


def karaoke_segments(voiceovers: Iterable[Voiceover]) -> list[KaraokeSegment]:
    """Split each voiceover's ``text_with_pauses`` into segments at every ``[PAUSE]``.

    Special words are upper-cased. A segment ending in a pause is kept even when it
    has no words (e.g. two pauses in a row); a trailing segment without words is not.
    """
    segments: list[KaraokeSegment] = []
    for voiceover in voiceovers:
        offset = float(voiceover.get("start_time", 0.0))
        segment: KaraokeSegment | None = None

        for item in voiceover.get("text_with_pauses", []):
            if segment is None:
                # Legacy key: TTS items carry start/end, not `time`, so this is usually
                # just the voiceover start. The renderer does not use segment["start"].
                segment = {"words": [], "start": float(item.get("time", 0.0)) + offset, "end": None}

            if item.get("word") == PAUSE_TOKEN:
                segments.append(segment)
                segment = None
                continue

            word = _karaoke_word(item, offset)
            segment["words"].append(word)
            segment["end"] = word["end"]

        if segment is not None and segment["words"]:
            segments.append(segment)
    return segments


def _karaoke_word(item: Mapping[str, Any], offset: float) -> KaraokeWord:
    is_special = item.get("is_special", False)
    word = item.get("word", "")
    return {
        "word": word.upper() if is_special else word,
        "is_special": is_special,
        "start": float(item.get("start", 0.0)) + offset,
        "end": float(item.get("end", 0.0)) + offset,
    }
