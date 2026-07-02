#!/usr/bin/env python3
"""Build a Spanish lemma frequency list from subtitle (.srt) or plain text (.txt) files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import spacy

TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
VTT_INLINE_TAG_RE = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>|<c>|</c>")
NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)
DIGIT_RE = re.compile(r"\d+")


def extract_subtitle_text(content: str) -> str:
    """Strip subtitle sequence numbers, timestamps, and markup; keep spoken text."""
    lines: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper() == "WEBVTT":
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if line.isdigit():
            continue
        if "-->" in line or TIMESTAMP_RE.match(line):
            continue
        line = HTML_TAG_RE.sub("", line)
        line = VTT_INLINE_TAG_RE.sub("", line)
        if line:
            lines.append(line)
    return " ".join(lines)


def read_input_text(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() in {".srt", ".vtt"}:
        return extract_subtitle_text(content)
    return content


def clean_text(text: str) -> str:
    text = DIGIT_RE.sub("", text)
    text = NON_WORD_RE.sub(" ", text)
    return text.lower().strip()


def process_file(file_path: Path, nlp: spacy.Language, freq_dict: Counter[str]) -> Counter[str]:
    text = clean_text(read_input_text(file_path))
    doc = nlp(text)

    for token in doc:
        if token.is_alpha and not token.is_stop and len(token.lemma_) > 2:
            freq_dict[token.lemma_.lower()] += 1

    return freq_dict


def load_existing_frequencies(csv_path: Path) -> Counter[str]:
    freq = Counter()
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = row.get("lemma", "").strip()
            count = row.get("frequency", row.get("frecuencia", "0")).strip()
            if lemma and count.isdigit():
                freq[lemma] = int(count)
    return freq


def save_frequency(freq_dict: Counter[str], output_path: Path, output_format: str) -> None:
    sorted_freq = sorted(freq_dict.items(), key=lambda item: item[1], reverse=True)

    if output_format == "json":
        payload = [{"lemma": lemma, "frequency": count} for lemma, count in sorted_freq]
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["lemma", "frequency"])
            writer.writerows(sorted_freq)

    print(f"Saved {len(sorted_freq)} lemmas to {output_path}")


def collect_input_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            files.extend(sorted(path.glob("*.srt")))
            files.extend(sorted(path.glob("*.vtt")))
            files.extend(sorted(path.glob("*.txt")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"Input path not found: {path}")
    return files


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Spanish lemma frequency list from .srt or .txt files."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input files or directories containing .srt/.txt files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="spanish_frequency.csv",
        help="Output file path (default: spanish_frequency.csv)",
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
        print("No .srt or .txt files found in the provided inputs.", file=sys.stderr)
        return 1

    try:
        nlp = spacy.load(args.model)
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