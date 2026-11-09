"""Word-timing normalisation and karaoke segmentation (pure functions, no moviepy rendering)."""

import copy

import pytest

from app.pipeline.render.word_timing import karaoke_segments, normalize_display_word, single_word_timings


def single_word(voiceovers):
    return single_word_timings(copy.deepcopy(voiceovers))


def karaoke(voiceovers):
    return karaoke_segments(copy.deepcopy(voiceovers))


# --- single-word timings (border / invert_mask styles) ---------------------------------------


def test_single_word_offsets_by_voiceover_start_and_uppercases():
    voiceovers = [
        {"start_time": 2.0, "timestamps": [{"word": "hello", "start": 0.0, "end": 0.5}]},
        {"start_time": "10", "timestamps": [{"word": "world", "start": "0.25", "end": 1.0}]},
    ]

    result = single_word(voiceovers)

    assert result == [
        {"word": "HELLO", "start": 2.0, "end": 2.5},
        {"word": "WORLD", "start": 10.25, "end": 11.0},
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  hello, ", "HELLO"),
        ("...wait?!", "WAIT"),
        ("—dash–", "DASH"),
        ("don't", "DON'T"),
        ("mid-word", "MID-WORD"),
        ("x", "X"),
    ],
)
def test_single_word_strips_glue_punctuation_at_edges_only(raw, expected):
    result = single_word([{"start_time": 0, "timestamps": [{"word": raw, "start": 0, "end": 1}]}])
    assert result[0]["word"] == expected


def test_single_word_keeps_extra_keys_and_defaults():
    result = single_word([{"timestamps": [{"word": "a", "start": 1, "end": 2, "is_special": True}]}])
    assert result == [{"word": "A", "start": 1.0, "end": 2.0, "is_special": True}]


def test_single_word_handles_missing_timestamps():
    assert single_word([{"start_time": 1.0}]) == []
    assert single_word([]) == []


# --- karaoke segments --------------------------------------------------------------------------


def _w(word, start, end, **extra):
    return {"word": word, "start": start, "end": end, **extra}


PAUSE = {"word": "[PAUSE]", "start": 0, "end": 0}


def test_karaoke_splits_on_pause_and_offsets_times():
    voiceovers = [
        {
            "start_time": 10.0,
            "text_with_pauses": [
                _w("Once", 0.0, 0.3),
                _w("upon", 0.3, 0.6, is_special=True),
                PAUSE,
                _w("a", 1.0, 1.1),
                _w("time", 1.1, 1.5),
            ],
        }
    ]

    segments = karaoke(voiceovers)

    assert segments == [
        {
            "start": 10.0,
            "end": 10.6,
            "words": [
                {"word": "Once", "is_special": False, "start": 10.0, "end": 10.3},
                {"word": "UPON", "is_special": True, "start": 10.3, "end": 10.6},
            ],
        },
        {
            "start": 10.0,  # segment start comes from the legacy `time` key (absent -> 0)
            "end": 11.5,
            "words": [
                {"word": "a", "is_special": False, "start": 11.0, "end": 11.1},
                {"word": "time", "is_special": False, "start": 11.1, "end": 11.5},
            ],
        },
    ]


def test_karaoke_segment_start_uses_legacy_time_key():
    segments = karaoke([{"start_time": 1.0, "text_with_pauses": [{"word": "hi", "time": 0.5, "start": 0.5, "end": 1}]}])
    assert segments[0]["start"] == 1.5


def test_karaoke_drops_trailing_empty_segment_but_keeps_empty_ones_between_pauses():
    segments = karaoke(
        [{"start_time": 0, "text_with_pauses": [_w("one", 0, 1), PAUSE, PAUSE, _w("two", 2, 3), PAUSE]}]
    )

    assert [[w["word"] for w in s["words"]] for s in segments] == [["one"], [], ["two"]]
    assert segments[1] == {"words": [], "start": 0.0, "end": None}


def test_karaoke_multiple_voiceovers_are_concatenated():
    segments = karaoke(
        [
            {"start_time": 0, "text_with_pauses": [_w("a", 0, 1)]},
            {"start_time": 5, "text_with_pauses": [_w("b", 0, 1)]},
        ]
    )
    assert [(s["start"], s["end"], s["words"][0]["word"]) for s in segments] == [(0.0, 1.0, "a"), (5.0, 6.0, "b")]


def test_karaoke_empty_inputs():
    assert karaoke([]) == []
    assert karaoke([{"start_time": 3}]) == []
