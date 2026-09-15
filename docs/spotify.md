# Spotify transcripts

## 1. Download

Use the [Spotify Transcript Downloader](https://chromewebstore.google.com/detail/spotify-transcript-downlo/ikikjdefijhcmoomcfkbjhimhmbnmnnf) extension in Spotify Web.

## 2. Move files

Put the `.txt` files in `subtitles/spotify/` (any filename is fine). Those transcripts are committed so the list can be rebuilt on another machine. Do not commit MP3s or `*:Zone.Identifier` files.

## 3. Build frequency list

```bash
python scripts/process_spotify.py
```

Updates `data/frequency.csv`.