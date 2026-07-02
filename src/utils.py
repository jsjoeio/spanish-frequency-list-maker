"""Shared helpers for subtitle download and frequency processing."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import spacy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SUBTITLES_DIR = PROJECT_ROOT / "subtitles" / "raw"
DEFAULT_FREQUENCY_CSV = DATA_DIR / "frequency.csv"
DEFAULT_SOURCES_CSV = DATA_DIR / "sources.csv"

TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
VTT_INLINE_TAG_RE = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>|<c>|</c>")
NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)
DIGIT_RE = re.compile(r"\d+")

SUBTITLE_SUFFIXES = {".srt", ".vtt", ".txt"}


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


def save_frequency(freq_dict: Counter[str], output_path: Path, output_format: str = "csv") -> None:
    sorted_freq = sorted(freq_dict.items(), key=lambda item: item[1], reverse=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        payload = [{"lemma": lemma, "frequency": count} for lemma, count in sorted_freq]
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["lemma", "frequency"])
            writer.writerows(sorted_freq)

    print(f"Saved {len(sorted_freq)} lemmas to {output_path}")


def collect_input_files(paths: list[Path | str]) -> list[Path]:
    files: list[Path] = []
    for path_value in paths:
        path = Path(path_value)
        if path.is_dir():
            for suffix in SUBTITLE_SUFFIXES:
                files.extend(sorted(path.glob(f"*{suffix}")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"Input path not found: {path}")
    return files


def load_spacy_model(model_name: str) -> spacy.Language:
    return spacy.load(model_name)


def read_source_urls(sources_path: Path) -> list[str]:
    urls: list[str] = []
    with sources_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            url = row.get("url", "").strip()
            if url and not url.startswith("#"):
                urls.append(url)
    return urls