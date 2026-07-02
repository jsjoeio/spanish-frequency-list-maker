# Spanish Frequency List Maker

Build a personal Spanish lemma frequency list from subtitle (`.srt`, `.vtt`) or plain text (`.txt`) files. Useful for language learning apps, vocabulary prioritization, or tracking which words appear most in content you actually consume.

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
├── subtitles/              # Downloaded subtitles (gitignored)
│   └── raw/
├── README.md
└── requirements.txt
```

Subtitles are not stored in the repo. Only the code and the generated frequency list are committed.

## Features

- Downloads Spanish subtitles from URLs in `data/sources.txt` via `yt-dlp`
- Processes `.srt`, `.vtt`, and `.txt` files
- Lemmatizes words with [spaCy](https://spacy.io/) (`es_core_news_sm`)
- Filters stop words and short tokens
- Merges with the existing frequency list to accumulate counts over time
- Exports to CSV or JSON

## Requirements

- Python 3.10+
- spaCy Spanish model: `es_core_news_sm`
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading subtitles

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
pip install yt-dlp
```

## Usage

### Full pipeline: download and update frequency list

Add URLs to `data/sources.txt` (one per line), then run:

```bash
python -m src.download_subs
```

This downloads subtitles into `subtitles/raw/` (gitignored), processes them, and updates `data/frequency.csv`. At the end it prints a summary with your unique lemma count, progress toward a 15,000-lemma goal, and a rough estimate of how much more content you need (hours/minutes and videos).

Reprocess existing downloads without re-downloading:

```bash
python -m src.download_subs --skip-download
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

1. `download_subs.py` reads URLs from `data/sources.txt` and saves subtitles to `subtitles/raw/`
2. Subtitle markup and timestamps are stripped
3. Text is normalized (lowercase, numbers and punctuation removed)
4. spaCy tokenizes and lemmatizes each file
5. Lemma counts from all files in `subtitles/raw/` are written to `data/frequency.csv`

## License

MIT