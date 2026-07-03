# Spanish Frequency List Maker

Build a personal Spanish lemma frequency list from subtitle (`.srt`, `.vtt`) or plain text (`.txt`) files. Useful for language learning apps, vocabulary prioritization, or tracking which words appear most in content you actually consume.

## Quickstart

**One-time setup:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
# ffmpeg is required for audio extraction and Whisper (e.g. sudo apt install ffmpeg)
```

**Every time you have new videos:**

1. Paste YouTube URLs into `data/sources.txt` (one per line)
2. Run:

```bash
python -m src.download_subs
```

3. Check `data/frequency.csv` for your updated list

The script downloads audio from each URL, transcribes it with Whisper, processes the transcripts, and prints a summary at the end (unique lemma count, progress toward 15k, and a rough time estimate).

## Project Structure

```
spanish-frequency-list-maker/
├── src/
│   ├── process_files.py    # Lemmatize subtitle/text files into a frequency list
│   ├── download_subs.py    # Download subtitles from URLs and update frequency.csv
│   └── utils.py            # Shared processing helpers
├── data/
│   ├── frequency.csv       # Main frequency list (committed)
│   └── sources.txt         # YouTube/podcast URLs to download (one per line)
├── subtitles/              # Downloaded transcripts and audio (gitignored)
│   ├── raw/                # Whisper VTT transcripts (or caption files)
│   └── audio/              # Extracted MP3 files
├── README.md
└── requirements.txt
```

Transcripts and audio are not stored in the repo. Only the code and the generated frequency list are committed.

## Features

- Transcribes Spanish speech from URLs in `data/sources.txt` via `yt-dlp` + Whisper (default)
- Falls back to YouTube captions with `--method captions`
- Processes `.srt`, `.vtt`, and `.txt` files
- Lemmatizes words with [spaCy](https://spacy.io/) (`es_core_news_sm`)
- Filters stop words and short tokens
- Rebuilds the frequency list from all downloaded subtitles each run
- Exports to CSV or JSON

## Requirements

- Python 3.10+
- spaCy Spanish model: `es_core_news_sm`
- [ffmpeg](https://ffmpeg.org/) for audio extraction and Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading audio
- [Whisper](https://github.com/openai/whisper) (`openai-whisper`) for transcription

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

## Usage

### Full pipeline: transcribe and update frequency list

Add URLs to `data/sources.txt` (one per line), then run:

```bash
python -m src.download_subs
```

This downloads audio into `subtitles/audio/`, saves Whisper transcripts as VTT files in `subtitles/raw/` (both gitignored), processes them, and updates `data/frequency.csv`. At the end it prints a summary with your unique lemma count, progress toward a 15,000-lemma goal, and a rough estimate of how much more content you need (hours/minutes and videos).

Use a different Whisper model:

```bash
python -m src.download_subs --whisper-model large-v3
```

Fall back to YouTube captions instead of Whisper:

```bash
python -m src.download_subs --method captions
```

Reprocess existing transcripts without re-downloading:

```bash
python -m src.download_subs --skip-download
```

Force re-transcription of URLs that already have a transcript:

```bash
python -m src.download_subs --force
```

### Process local files manually

```bash
python -m src.process_files subtitles/raw/
python -m src.process_files episode.srt notes.txt
```

Merge with the existing list:

```bash
python -m src.process_files subtitles/raw/ --merge data/frequency.csv -o data/frequency.csv
```

Export as JSON:

```bash
python -m src.process_files subtitles/raw/ -o data/frequency.json --format json
```

Show more top lemmas after processing:

```bash
python -m src.process_files subtitles/raw/ --top 100
```

## Sources File

`data/sources.txt` — paste one URL per line:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://www.youtube.com/watch?v=ANOTHER_ID
```

Lines starting with `#` are treated as comments.

## Output

`data/frequency.csv`:

```csv
lemma,frequency
decir,142
cosa,98
...
```

## How It Works

1. `download_subs.py` reads URLs from `data/sources.txt`, extracts audio with `yt-dlp`, transcribes with Whisper, and saves VTT transcripts to `subtitles/raw/`
2. Subtitle markup and timestamps are stripped
3. Text is normalized (lowercase, numbers and punctuation removed)
4. spaCy tokenizes and lemmatizes each file
5. Lemma counts from all files in `subtitles/raw/` are written to `data/frequency.csv`

## License

MIT