# Future plans

## Whisper transcription (implemented)

The default pipeline now downloads audio with `yt-dlp` and transcribes with [Whisper](https://github.com/openai/whisper) (`medium` by default). Use `--method captions` to fall back to YouTube subtitles.

Possible follow-ups:

- Try `large-v3` or a fine-tuned Spanish model for higher accuracy
- Fine-tune on rioplatense parenting content
- Trim caption-specific heuristics once Whisper transcripts prove stable

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