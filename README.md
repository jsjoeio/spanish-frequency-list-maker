# Spanish Frequency List Maker

Build a personal Spanish lemma frequency list from subtitle (`.srt`) or plain text (`.txt`) files. Useful for language learning apps, vocabulary prioritization, or tracking which words appear most in content you actually consume.

## Features

- Processes `.srt` and `.vtt` subtitle files (timestamps and sequence numbers are stripped automatically)
- Processes plain `.txt` files
- Lemmatizes words with [spaCy](https://spacy.io/) (`es_core_news_sm`)
- Filters stop words and short tokens
- Merges with an existing frequency CSV to accumulate counts over time
- Exports to CSV or JSON

## Requirements

- Python 3.10+
- spaCy Spanish model: `es_core_news_sm`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

## Usage

Process one or more files:

```bash
python frequency_maker.py podcast.srt interview.txt
```

Process every `.srt` and `.txt` file in a directory:

```bash
python frequency_maker.py ./subtitles/
```

Custom output path and format:

```bash
python frequency_maker.py ./subtitles/ -o my_list.csv
python frequency_maker.py ./subtitles/ -o my_list.json --format json
```

Merge with an existing frequency list:

```bash
python frequency_maker.py new_episode.srt --merge spanish_frequency.csv -o spanish_frequency.csv
```

Show a different number of top lemmas (default: 50, use `0` to skip):

```bash
python frequency_maker.py episode.srt --top 100
```

## Output

CSV (default):

```csv
lemma,frequency
decir,142
cosa,98
...
```

JSON (`--format json`):

```json
[
  {"lemma": "decir", "frequency": 142},
  {"lemma": "cosa", "frequency": 98}
]
```

## Test Data

A sample Spanish subtitle file (`test_data/sample.es.vtt`) is included for quick testing:

```bash
python frequency_maker.py test_data/sample.es.vtt --top 20
```

To download subtitles from a YouTube video for your own testing:

```bash
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp && chmod +x yt-dlp
./yt-dlp --write-auto-sub --write-sub --sub-lang es --skip-download -o "test_data/%(title)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

The script accepts `.vtt` files directly, so no conversion step is required.

## How It Works

1. Read input text (SRT markup is removed for subtitle files)
2. Normalize text (lowercase, remove numbers and punctuation)
3. Tokenize and lemmatize with spaCy
4. Count lemmas, skipping stop words and tokens with 2 or fewer characters
5. Sort by frequency and write the output file

## License

MIT