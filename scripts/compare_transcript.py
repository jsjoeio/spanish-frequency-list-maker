#!/usr/bin/env python3
"""Compare a Spotify (or other) transcript against a YouTube caption file."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from src.utils import load_spacy_model, process_file, read_input_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPOTIFY_DIR = PROJECT_ROOT / "subtitles" / "spotify"
DEFAULT_YOUTUBE_DIR = PROJECT_ROOT / "subtitles" / "raw"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare transcript quality between a local file (e.g. Spotify export) "
            "and a YouTube caption file before updating frequency.csv."
        )
    )
    parser.add_argument(
        "spotify",
        type=Path,
        help="Local transcript file (.txt, .srt, .vtt)",
    )
    parser.add_argument(
        "youtube",
        type=Path,
        nargs="?",
        help="YouTube caption to compare against (default: subtitles/raw/<id>.es.vtt)",
    )
    parser.add_argument(
        "--id",
        help="Video id used to auto-pick subtitles/raw/<id>.es.vtt when youtube path omitted",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="How many top lemmas to print per source (default: 20)",
    )
    return parser.parse_args(argv)


def text_stats(label: str, path: Path) -> None:
    text = read_input_text(path)
    words = text.split()
    print(f"\n=== {label}: {path.name} ===")
    print(f"chars: {len(text):,}  words: {len(words):,}")
    print(f"preview: {text[:240].replace(chr(10), ' ')}...")


def lemma_stats(label: str, path: Path, nlp) -> Counter[str]:
    freq = process_file(path, nlp, Counter())
    print(f"\n--- {label} lemmas ---")
    print(f"unique: {len(freq):,}  total occurrences: {sum(freq.values()):,}")
    return freq


def print_top_diff(a: Counter[str], b: Counter[str], top: int) -> None:
    all_lemmas = set(a) | set(b)
    deltas = [(lemma, a[lemma], b[lemma], b[lemma] - a[lemma]) for lemma in all_lemmas]
    deltas.sort(key=lambda item: abs(item[3]), reverse=True)

    print(f"\n=== Biggest lemma count differences (B - A) ===")
    for lemma, a_count, b_count, delta in deltas[:top]:
        if delta == 0:
            continue
        sign = "+" if delta > 0 else ""
        print(f"  {lemma}: {a_count} -> {b_count} ({sign}{delta})")

    only_a = sorted(lemma for lemma in all_lemmas if a[lemma] and not b[lemma])[:10]
    only_b = sorted(lemma for lemma in all_lemmas if b[lemma] and not a[lemma])[:10]
    if only_a:
        print(f"\nOnly in A ({len(only_a)} shown): {', '.join(only_a)}")
    if only_b:
        print(f"\nOnly in B ({len(only_b)} shown): {', '.join(only_b)}")


def resolve_youtube_path(args: argparse.Namespace) -> Path:
    if args.youtube:
        return args.youtube
    if not args.id:
        raise SystemExit("Provide a youtube path or --id VIDEO_ID")
    candidate = DEFAULT_YOUTUBE_DIR / f"{args.id}.es.vtt"
    if not candidate.exists():
        fallback = DEFAULT_YOUTUBE_DIR / f"{args.id}.vtt"
        if fallback.exists():
            return fallback
        raise SystemExit(f"YouTube caption not found: {candidate}")
    return candidate


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spotify_path = args.spotify
    youtube_path = resolve_youtube_path(args)

    if not spotify_path.exists():
        print(f"Spotify/local transcript not found: {spotify_path}", file=sys.stderr)
        return 1
    if not youtube_path.exists():
        print(f"YouTube caption not found: {youtube_path}", file=sys.stderr)
        return 1

    print("Comparing:")
    print(f"  A (local):  {spotify_path}")
    print(f"  B (YouTube): {youtube_path}")

    text_stats("A local", spotify_path)
    text_stats("B YouTube", youtube_path)

    try:
        nlp = load_spacy_model("es_core_news_sm")
    except OSError:
        print("spaCy model es_core_news_sm is not installed.", file=sys.stderr)
        return 1

    freq_a = lemma_stats("A local", spotify_path, nlp)
    freq_b = lemma_stats("B YouTube", youtube_path, nlp)

    print(f"\n=== Top {args.top} lemmas: A local ===")
    for lemma, count in freq_a.most_common(args.top):
        print(f"  {lemma}: {count}")
    print(f"\n=== Top {args.top} lemmas: B YouTube ===")
    for lemma, count in freq_b.most_common(args.top):
        print(f"  {lemma}: {count}")

    print_top_diff(freq_a, freq_b, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())