#!/usr/bin/env python3
"""Build frequency.csv from Spotify transcripts in subtitles/spotify/."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPOTIFY_DIR = PROJECT_ROOT / "subtitles" / "spotify"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.process_files import main as process_main


def run() -> int:
    if not SPOTIFY_DIR.is_dir():
        print(f"Directory not found: {SPOTIFY_DIR}", file=sys.stderr)
        return 1
    return process_main([str(SPOTIFY_DIR)])


if __name__ == "__main__":
    raise SystemExit(run())