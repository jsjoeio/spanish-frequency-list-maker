# Future plans

## Whisper transcription

YouTube auto-generated subtitles are often low quality — they produce broken words (`ner`, `sción`), mistranscriptions (`parí` for `para`), and inconsistent verb forms.

A better long-term pipeline:

1. Download audio from source videos
2. Transcribe with [Whisper](https://github.com/openai/whisper) (large-v3 or fine-tuned Spanish model)
3. Optionally fine-tune on rioplatense parenting content for better accuracy
4. Feed clean transcripts into the existing lemma frequency pipeline

This would reduce reliance on caption-specific heuristics and improve lemma quality across the board.

## Lemmatizer alternatives (evaluated, not switched)

`es_core_news_sm` struggles with rioplatense voseo, clitic pronouns, and conjugated forms in noisy captions. We stay on spaCy + rule-based post-processing for now, but these are worth revisiting if caption quality improves (e.g. via Whisper):

| Library | Pros | Cons |
|---------|------|------|
| [simplemma](https://github.com/adbar/simplemma) | Lightweight, rule-based, multilingual | Less context-aware than spaCy |
| [spacy-spanish-lemmatizer](https://github.com/pablodms/spacy-spanish-lemmatizer) | Drop-in edit-tree lemmatizer for Spanish | Still depends on spaCy tokenization |
| [Stanza](https://stanfordnlp.github.io/stanza/) | Higher accuracy on standard Spanish | Heavier; may still miss voseo without rules |
| `es_core_news_lg` | Better than `sm` within spaCy | Larger download; same clitic/voseo blind spots |

Whisper-clean transcripts would help more than swapping lemmatizers alone.

## Other ideas (not scoped yet)

- Multi-source frequency lists (podcasts, Wikipedia, etc.) with dropdown selector in the vocab test
- Domain-specific ASR correction dictionaries per source