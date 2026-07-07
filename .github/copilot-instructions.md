# Copilot Instructions

## Repository overview

This repo builds a personal Spanish lemma frequency list from subtitle files.
Key files:

| File | Purpose |
|------|---------|
| `src/utils.py` | Lemma normalisation: `LEMMA_CORRECTIONS`, `LEMMA_BLOCKLIST`, `NAME_BLOCKLIST`, `BOGUS_LEMMA_SUFFIXES` |
| `tests/test_normalize_lemma.py` | Unit tests for `normalize_lemma()` |
| `data/frequency.csv` | Committed frequency list (lemma, count) |

Run tests with:

```bash
python -m pytest tests/
```

---

## Skill: `/fix-frequency-list`

**Trigger phrase** — include `/fix-frequency-list` anywhere in a GitHub issue to activate this skill.

### What it does

Audits the bottom ~100 rows of `data/frequency.csv` for bad lemmas produced by spaCy mis-lemmatization, ASR noise, or unconverted conjugated forms, then fixes them using a TDD workflow.

### Step-by-step workflow

1. **Audit** — read `data/frequency.csv` and collect every lemma in the bottom 100 rows that looks suspicious:
   - Non-Spanish character sequences or mixed scripts
   - Conjugated verb forms left unchanged by spaCy (e.g. ends in `-astir`, `-aser`, `-iser`)
   - Stem-change preterites spaCy cannot recover (e.g. `choqué → chocar`)
   - Past-participle adjectives that should map to their base verb
   - Enclitics still attached (e.g. `tirarno`, `involucrarte`)
   - Wrong accent or wrong gender (e.g. `incómodar`, `zanahorio`)
   - Entries that are names, abbreviations, or pure noise

2. **Categorise** — group findings into these buckets:
   - `BOGUS_LEMMA_SUFFIXES` fix (suffix-stripping rule)
   - `LEMMA_CORRECTIONS` fix (explicit mapping)
   - `LEMMA_BLOCKLIST` addition (noise/garbage)
   - `NAME_BLOCKLIST` addition (proper name)

3. **Write failing tests first** — add one `assert normalize_lemma("bad") == "good"` test per finding to `tests/test_normalize_lemma.py`. Run the suite and confirm every new test fails.

4. **Fix `src/utils.py`** — add/update entries in `BOGUS_LEMMA_SUFFIXES`, `LEMMA_CORRECTIONS`, `LEMMA_BLOCKLIST`, `NAME_BLOCKLIST` to make every new test pass without breaking existing tests.

5. **Verify** — run `python -m pytest tests/` and confirm all tests pass.

6. **Commit** — use a message in the form:
   ```
   fix: improve lemma normalization for bottom-100 frequency.csv entries
   ```

### Relevant patterns in `src/utils.py`

```python
# Suffix-stripping rules: (bogus_suffix, (replacement_suffixes,))
BOGUS_LEMMA_SUFFIXES = [
    ("astir", ("ar", "er", "ir")),
    ...
]

# Explicit overrides applied after suffix stripping
LEMMA_CORRECTIONS: dict[str, str] = {
    "choquar": "chocar",
    ...
}

# Lemmas that are always discarded
LEMMA_BLOCKLIST: set[str] = {"sti", "rós", ...}

# Proper names that are always discarded
NAME_BLOCKLIST: set[str] = {"paulo", ...}
```

### Acceptance criteria

- All pre-existing tests still pass.
- Every suspicious bottom-100 lemma identified in step 1 is either corrected or blocklisted.
- No non-Spanish or clearly erroneous lemmas remain in the bottom 100 after re-running the pipeline.
