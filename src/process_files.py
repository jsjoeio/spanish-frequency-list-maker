#!/usr/bin/env python3
"""Build a Spanish lemma frequency list from subtitle or plain text files."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from src.utils import (
    DEFAULT_FREQUENCY_CSV,
    collect_input_files,
    load_existing_frequencies,
    load_spacy_model,
    process_file,
    save_frequency,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Spanish lemma frequency list from .srt, .vtt, or .txt files."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input files or directories containing subtitle/text files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_FREQUENCY_CSV),
        help=f"Output file path (default: {DEFAULT_FREQUENCY_CSV})",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--merge",
        metavar="CSV",
        help="Merge counts with an existing frequency CSV before saving",
    )
    parser.add_argument(
        "--model",
        default="es_core_news_sm",
        help="spaCy Spanish model name (default: es_core_news_sm)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Number of top lemmas to print (default: 50, use 0 to skip)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        input_files = collect_input_files(args.inputs)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not input_files:
        print("No subtitle or text files found in the provided inputs.", file=sys.stderr)
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
    if args.merge:
        merge_path = Path(args.merge)
        if merge_path.exists():
            freq = load_existing_frequencies(merge_path)
            print(f"Loaded {len(freq)} lemmas from {merge_path}")

    for file_path in input_files:
        print(f"Processing {file_path}...")
        freq = process_file(file_path, nlp, freq)

    output_path = Path(args.output)
    save_frequency(freq, output_path, args.format)

    if args.top > 0:
        print(f"\nTop {args.top} lemmas:")
        for lemma, count in freq.most_common(args.top):
            print(f"{lemma}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())