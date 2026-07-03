"""Whisper transcription helpers for the subtitle download pipeline."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.utils import PROJECT_ROOT


def find_ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if binary:
        return binary

    raise FileNotFoundError(
        "ffmpeg not found. Install it with your system package manager "
        "(e.g. sudo apt install ffmpeg)."
    )


def find_yt_dlp() -> str:
    binary = shutil.which("yt-dlp")
    if binary:
        return binary

    project_binary = PROJECT_ROOT / "yt-dlp"
    if project_binary.is_file():
        return str(project_binary)

    raise FileNotFoundError(
        "yt-dlp not found. Install it with: pip install yt-dlp\n"
        "Or download the binary: "
        "curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp"
    )


def get_video_id(url: str) -> str:
    yt_dlp = find_yt_dlp()
    result = subprocess.run(
        [yt_dlp, "--print", "id", url],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Could not resolve video id for {url}: {stderr}")

    video_id = result.stdout.strip().splitlines()[-1]
    if not video_id:
        raise RuntimeError(f"Could not resolve video id for {url}")
    return video_id


def download_audio(url: str, audio_dir: Path, video_id: str) -> Path:
    find_ffmpeg()

    audio_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(audio_dir / f"{video_id}.%(ext)s")

    command = [
        find_yt_dlp(),
        "-x",
        "--audio-format",
        "mp3",
        "--no-playlist",
        "-o",
        output_template,
        url,
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"yt-dlp audio download failed for {url}: {stderr}")

    candidates = sorted(audio_dir.glob(f"{video_id}.*"))
    if not candidates:
        raise RuntimeError(f"Audio file not found after download for {url}")

    return candidates[0]


def format_vtt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def segments_to_vtt(segments: list[dict[str, Any]]) -> str:
    lines = ["WEBVTT", ""]
    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        start = format_vtt_timestamp(float(segment.get("start", 0.0)))
        end = format_vtt_timestamp(float(segment.get("end", 0.0)))
        lines.extend([f"{start} --> {end}", text, ""])
    return "\n".join(lines).rstrip() + "\n"


def load_whisper_model(model_name: str) -> Any:
    try:
        import whisper
    except ImportError as exc:
        raise ImportError(
            "openai-whisper is not installed. Run: pip install openai-whisper"
        ) from exc

    print(f"Loading Whisper model '{model_name}'...")
    return whisper.load_model(model_name)


def transcribe_audio(
    model: Any,
    audio_path: Path,
    output_path: Path,
    *,
    language: str = "es",
) -> Path:
    print(f"Transcribing {audio_path.name} with Whisper...")
    result = model.transcribe(str(audio_path), language=language)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(segments_to_vtt(result.get("segments", [])), encoding="utf-8")
    print(f"Saved transcript to {output_path}")
    return output_path


def download_captions(urls: list[str], output_dir: Path, lang: str = "es") -> None:
    yt_dlp = find_yt_dlp()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(id)s")

    for url in urls:
        print(f"Downloading subtitles for {url}...")
        command = [
            yt_dlp,
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang",
            lang,
            "--skip-download",
            "-o",
            output_template,
            url,
        ]
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print(
                f"Warning: yt-dlp failed for {url} (exit code {result.returncode})",
                file=sys.stderr,
            )


def transcribe_urls(
    urls: list[str],
    output_dir: Path,
    audio_dir: Path,
    *,
    whisper_model_name: str = "medium",
    language: str = "es",
    force: bool = False,
) -> None:
    find_ffmpeg()
    model = load_whisper_model(whisper_model_name)

    for url in urls:
        try:
            video_id = get_video_id(url)
        except RuntimeError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
            continue

        transcript_path = output_dir / f"{video_id}.vtt"
        if transcript_path.exists() and not force:
            print(f"Skipping {url} — transcript already exists at {transcript_path}")
            continue

        try:
            audio_path = download_audio(url, audio_dir, video_id)
            transcribe_audio(model, audio_path, transcript_path, language=language)
        except (RuntimeError, OSError) as exc:
            print(f"Warning: failed to transcribe {url}: {exc}", file=sys.stderr)