# Spotify transcripts

Use Spotify exports as the primary transcript source when the podcast is also on YouTube. They are cleaner than YouTube auto-captions (no rollup duplication) and much faster than Whisper on CPU.

## Download

1. Install the Chrome extension: [Spotify Transcript Downloader](https://chromewebstore.google.com/detail/spotify-transcript-downlo/ikikjdefijhcmoomcfkbjhimhmbnmnnf)
2. Open the episode in **Spotify Web**
3. Use the extension to download the transcript

## Where to put files

Save exports under `subtitles/spotify/` (gitignored).

**Naming:** use the YouTube video ID so each file pairs with its caption in `subtitles/raw/`:

```text
subtitles/spotify/gPpk1L-wzFM.txt
subtitles/spotify/Wqn7OlSW4yY.txt
```

Supported formats: `.txt`, `.srt`, `.vtt`

Find the ID in `data/sources.txt` (e.g. `watch?v=gPpk1L-wzFM` → `gPpk1L-wzFM`).

## Compare before building frequency.csv

After adding a file, compare it against the matching YouTube caption:

```bash
python scripts/compare_transcript.py subtitles/spotify/gPpk1L-wzFM.txt --id gPpk1L-wzFM
```

Or pass the YouTube path explicitly:

```bash
python scripts/compare_transcript.py \
  subtitles/spotify/gPpk1L-wzFM.txt \
  subtitles/raw/gPpk1L-wzFM.es.vtt
```

The script prints word counts, previews, top lemmas, and the biggest count differences between sources.

### What we saw on `gPpk1L-wzFM`

| | Spotify | YouTube caption |
|--|---------|-----------------|
| Words | ~11.5k | ~34k (~3× inflated) |
| Lemma occurrences | ~3k | ~9k |
| Top lemmas | Same order (`ver`, `decir`, `momento`, …) | Same order, inflated counts |

Spotify text is readable dialogue; YouTube repeats phrases from caption rollup. Prefer Spotify when available.

## Build frequency.csv (once all episodes are downloaded)

When every episode is in `subtitles/spotify/`, process the folder and write a new list:

```bash
python -m src.process_files subtitles/spotify/ -o data/frequency.csv
```

Optional: show a summary and top lemmas:

```bash
python -m src.process_files subtitles/spotify/ -o data/frequency.csv --top 30
```

Then copy `data/frequency.csv` to [spanish-vocab](https://github.com/jsjoeio/spanish-vocab) and run `bun run convert-frequency` there.

## Workflow checklist

- [ ] Download all episodes with the Chrome extension
- [ ] Move files to `subtitles/spotify/<VIDEO_ID>.txt`
- [ ] Spot-check with `scripts/compare_transcript.py` (optional)
- [ ] Run `python -m src.process_files subtitles/spotify/ -o data/frequency.csv`
- [ ] Sync to `spanish-vocab`

## Notes

- Timestamp lines like `[0:00]` in Spotify `.txt` files are harmless for lemmatization; strip them later if you want cleaner plain text.
- YouTube captions remain in `subtitles/raw/` as a fallback (`python -m src.download_subs --method captions`).
- Whisper (`feat/whisper-transcription` branch) is optional and slow on CPU; Spotify + compare is the preferred path for this corpus.