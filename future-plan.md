# Future plans

## Whisper transcription

YouTube auto-generated subtitles are often low quality — they produce broken words (`ner`, `sción`), mistranscriptions (`parí` for `para`), and inconsistent verb forms.

A better long-term pipeline:

1. Download audio from source videos
2. Transcribe with [Whisper](https://github.com/openai/whisper) (large-v3 or fine-tuned Spanish model)
3. Optionally fine-tune on rioplatense parenting content for better accuracy
4. Feed clean transcripts into the existing lemma frequency pipeline

This would reduce reliance on caption-specific heuristics and improve lemma quality across the board.

## Other ideas (not scoped yet)

- Multi-source frequency lists (podcasts, Wikipedia, etc.) with dropdown selector in the vocab test
- Domain-specific ASR correction dictionaries per source
- Larger spaCy model (`es_core_news_lg`) for better lemmatization accuracy