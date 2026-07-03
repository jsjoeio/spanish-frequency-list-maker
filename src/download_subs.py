#!/usr/bin/env python3
"""Download or transcribe Spanish speech from source URLs and update the frequency list."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from src.transcription import download_captions, transcribe_urls
from src.utils import (
    DEFAULT_FREQUENCY_CSV,
    DEFAULT_LEMMA_GOAL,
    DEFAULT_SOURCES_FILE,
    PROJECT_ROOT,
    SUBTITLES_DIR,
    collect_input_files,
    load_spacy_model,
    print_frequency_summary,
    process_file,
    read_source_urls,
    save_frequency,
)

AUDIO_DIR = PROJECT_ROOT / "subtitles" / "audio"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download or transcribe speech from source URLs and update data/frequency.csv. "
            "By default, audio is extracted with yt-dlp and transcribed with Whisper."
        )
    )
    parser.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES_FILE),
        help=f"Text file with one URL per line (default: {DEFAULT_SOURCES_FILE})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SUBTITLES_DIR),
        help=f"Directory for transcripts/subtitles (default: {SUBTITLES_DIR})",
    )
    parser.add_argument(
        "--audio-dir",
        default=str(AUDIO_DIR),
        help=f"Directory for downloaded audio files (default: {AUDIO_DIR})",
    )
    parser.add_argument(
        "--frequency",
        default=str(DEFAULT_FREQUENCY_CSV),
        help=f"Frequency CSV to update (default: {DEFAULT_FREQUENCY_CSV})",
    )
    parser.add_argument(
        "--method",
        choices=("whisper", "captions"),
        default="whisper",
        help="Acquisition method: whisper (default) or YouTube captions",
    )
    parser.add_argument(
        "--whisper-model",
        default="medium",
        help="Whisper model size (default: medium)",
    )
    parser.add_argument(
        "--lang",
        default="es",
        help="Language code for Whisper or captions (default: es)",
    )
    parser.add_argument(
        "--model",
        default="es_core_news_sm",
        help="spaCy Spanish model name (default: es_core_news_sm)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Only reprocess transcripts already in the output directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and re-transcribe even if a transcript already exists",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top lemmas to print (default: 20, use 0 to skip)",
    )
    parser.add_argument(
        "--goal",
        type=int,
        default=DEFAULT_LEMMA_GOAL,
        help=f"Target unique lemma count for progress estimate (default: {DEFAULT_LEMMA_GOAL})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sources_path = Path(args.sources)
    output_dir = Path(args.output_dir)
    audio_dir = Path(args.audio_dir)
    frequency_path = Path(args.frequency)

    if not args.skip_download:
        if not sources_path.exists():
            print(f"Sources file not found: {sources_path}", file=sys.stderr)
            return 1

        urls = read_source_urls(sources_path)
        if not urls:
            print(f"No URLs found in {sources_path}", file=sys.stderr)
            return 1

        try:
            if args.method == "whisper":
                transcribe_urls(
                    urls,
                    output_dir,
                    audio_dir,
                    whisper_model_name=args.whisper_model,
                    language=args.lang,
                    force=args.force,
                )
            else:
                download_captions(urls, output_dir, lang=args.lang)
        except (FileNotFoundError, ImportError) as exc:
            print(exc, file=sys.stderr)
            return 1

    try:
        input_files = collect_input_files([output_dir])
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not input_files:
        print(f"No subtitle files found in {output_dir}", file=sys.stderr)
        return 1

    try:
        nlp = load_spacy_model(args.model)
    except OSError:
        print(
            f"spaCy model '{args.model}' is not installed.\n"
            f"Run: python -m spacy download {args.model}",
            file=sys.stderr,
        )
        return 1

    freq: Counter[str] = Counter()

    for file_path in input_files:
        print(f"Processing {file_path}...")
        freq = process_file(file_path, nlp, freq)

    save_frequency(freq, frequency_path)

    print_frequency_summary(freq, input_files, goal=args.goal)

    if args.top > 0:
        print(f"\nTop {args.top} lemmas:")
        for lemma, count in freq.most_common(args.top):
            print(f"{lemma}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())