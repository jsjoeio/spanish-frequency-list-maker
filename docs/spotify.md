# Spotify transcripts

## 1. Download

Use the [Spotify Transcript Downloader](https://chromewebstore.google.com/detail/spotify-transcript-downlo/ikikjdefijhcmoomcfkbjhimhmbnmnnf) extension in Spotify Web.

## 2. Move files

Put the `.txt` files in `subtitles/spotify/` (any filename is fine).

## 3. Build frequency list

```bash
python scripts/process_spotify.py
```

Updates `data/frequency.csv`.