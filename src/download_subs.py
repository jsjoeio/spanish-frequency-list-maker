#!/usr/bin/env python3
"""Download Spanish subtitles from source URLs and update the frequency list."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from src.utils import (
    DEFAULT_FREQUENCY_CSV,
    DEFAULT_SOURCES_FILE,
    SUBTITLES_DIR,
    collect_input_files,
    load_spacy_model,
    process_file,
    read_source_urls,
    save_frequency,
)


def find_yt_dlp() -> str:
    binary = shutil.which("yt-dlp")
    if binary:
        return binary

    project_binary = Path(__file__).resolve().parent.parent / "yt-dlp"
    if project_binary.is_file():
        return str(project_binary)

    raise FileNotFoundError(
        "yt-dlp not found. Install it with: pip install yt-dlp\n"
        "Or download the binary: "
        "curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp"
    )


def download_subtitles(urls: list[str], output_dir: Path, lang: str = "es") -> None:
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
            print(f"Warning: yt-dlp failed for {url} (exit code {result.returncode})", file=sys.stderr)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download subtitles from source URLs and update data/frequency.csv."
    )
    parser.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES_FILE),
        help=f"Text file with one URL per line (default: {DEFAULT_SOURCES_FILE})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SUBTITLES_DIR),
        help=f"Directory for downloaded subtitles (default: {SUBTITLES_DIR})",
    )
    parser.add_argument(
        "--frequency",
        default=str(DEFAULT_FREQUENCY_CSV),
        help=f"Frequency CSV to update (default: {DEFAULT_FREQUENCY_CSV})",
    )
    parser.add_argument(
        "--lang",
        default="es",
        help="Subtitle language code (default: es)",
    )
    parser.add_argument(
        "--model",
        default="es_core_news_sm",
        help="spaCy Spanish model name (default: es_core_news_sm)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Only reprocess subtitles already in the output directory",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top lemmas to print (default: 20, use 0 to skip)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sources_path = Path(args.sources)
    output_dir = Path(args.output_dir)
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
            download_subtitles(urls, output_dir, lang=args.lang)
        except FileNotFoundError as exc:
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

    if args.top > 0:
        print(f"\nTop {args.top} lemmas:")
        for lemma, count in freq.most_common(args.top):
            print(f"{lemma}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())