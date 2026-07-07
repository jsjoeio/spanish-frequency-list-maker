"""Tests for Whisper transcription helpers."""

from pathlib import Path

from src.transcription import (
    format_vtt_timestamp,
    get_video_id,
    prefer_whisper_transcripts,
    segments_to_vtt,
)


def test_format_vtt_timestamp_zero():
    assert format_vtt_timestamp(0.0) == "00:00:00.000"


def test_format_vtt_timestamp_with_fraction():
    assert format_vtt_timestamp(61.5) == "00:01:01.500"


def test_format_vtt_timestamp_hours():
    assert format_vtt_timestamp(3661.123) == "01:01:01.123"


def test_segments_to_vtt_skips_empty_segments():
    vtt = segments_to_vtt(
        [
            {"start": 0.0, "end": 1.0, "text": "hola"},
            {"start": 1.0, "end": 2.0, "text": "   "},
            {"start": 2.0, "end": 3.5, "text": "mundo"},
        ]
    )
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:01.000" in vtt
    assert "hola" in vtt
    assert "mundo" in vtt
    assert vtt.count("-->") == 2


def test_get_video_id_from_watch_url():
    assert (
        get_video_id("https://www.youtube.com/watch?v=Wqn7OlSW4yY")
        == "Wqn7OlSW4yY"
    )


def test_prefer_whisper_transcripts_drops_caption_duplicates():
    files = [
        Path("subtitles/raw/Wqn7OlSW4yY.vtt"),
        Path("subtitles/raw/Wqn7OlSW4yY.es.vtt"),
        Path("subtitles/raw/WLOn6QPlEds.es.vtt"),
    ]
    assert prefer_whisper_transcripts(files) == [
        Path("subtitles/raw/Wqn7OlSW4yY.vtt"),
        Path("subtitles/raw/WLOn6QPlEds.es.vtt"),
    ]