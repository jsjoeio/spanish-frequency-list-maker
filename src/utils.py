"""Shared helpers for subtitle download and frequency processing."""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from pathlib import Path

import spacy
from spacy.tokens import Token

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SUBTITLES_DIR = PROJECT_ROOT / "subtitles" / "raw"
DEFAULT_FREQUENCY_CSV = DATA_DIR / "frequency.csv"
DEFAULT_SOURCES_FILE = DATA_DIR / "sources.txt"
DEFAULT_LEMMA_GOAL = 15000

TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")
TIMESTAMP_RANGE_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{1,3})"
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
VTT_INLINE_TAG_RE = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>|<c>|</c>")
NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)
DIGIT_RE = re.compile(r"\d+")
CENSOR_PLACEHOLDER_RE = re.compile(r"\[&nbsp;__&nbsp;\]", re.IGNORECASE)
ENCLITIC_SUFFIX_RE = re.compile(
    r"(?:me|te|se|nos|os|lo|la|le|los|las|les)+$", re.IGNORECASE
)
SUBTITLE_SUFFIXES = {".srt", ".vtt", ".txt"}

# spaCy es_core_news_sm attaches clitic pronouns to verb lemmas ("decir él" from decirle)
CLITIC_PRONOUNS = frozenset({
    "él", "ella", "yo", "me", "te", "se", "le", "lo", "la",
    "los", "las", "nos", "os", "les",
})

# caption / markup junk that slips through tokenization
LEMMA_BLOCKLIST = frozenset({
    "nbsp", "ner", "__",
    # short non-words from ASR/caption noise
    "sti", "rós",
    # OCR/typing errors
    "vwer",
    # bogus verb stems that escape correction (not real infinitives)
    "tremeo", "tremear", "ahoritir", "paular",
})

# spaCy es_core_news_sm returns bad lemmas for conjugated rioplatense forms
LEMMA_CORRECTIONS: dict[str, str] = {
    "hablé": "hablar",
    "habler": "hablar",
    "charler": "charlar",
    "charlo": "charlar",
    "char": "charlar",
    "imaginé": "imaginar",
    "imaginer": "imaginar",
    "imagino": "imaginar",
    "imaginaba": "imaginar",
    "imaginabas": "imaginar",
    "imaginastar": "imaginar",
    "imaginaste": "imaginar",
    "imaginábar": "imaginar",
    "tenía": "tener",
    "tenías": "tener",
    "tenia": "tener",
    "escucho": "escuchar",
    "cholar": "chola",
    "veíar": "ver",
    "veiar": "ver",
    "veía": "ver",
    "veer": "ver",
    "vear": "ver",
    "sentíar": "sentir",
    "sentí": "sentir",
    "sentís": "sentir",
    "senter": "sentir",
    "servís": "servir",
    "necesitemos": "necesitar",
    "necesit": "necesitar",
    "saqué": "sacar",
    "saquar": "sacar",
    "saqu": "sacar",
    "saqer": "sacar",
    "saqar": "sacar",
    "arreglatir": "arreglar",
    "arreglé": "arreglar",
    "caístir": "caer",
    "usastar": "usar",
    "cesárear": "cesárea",
    "cesáreo": "cesárea",
    "cesáreir": "cesárea",
    "nacés": "nacer",
    "sebir": "servir",
    "vezar": "ver",
    "reduelar": "doler",
    "incluyo": "incluir",
    # ---- bottom-100 lemma improvements (issue #4) ----
    # bogus spaCy suffixes not caught by BOGUS_LEMMA_SUFFIXES patterns
    "soldastir": "soldar",
    "ayudser": "ayudar",
    "trasladir": "trasladar",
    # stem-change irregulars (c→qu, etc.) that _guess_from_stem can't recover
    "choqué": "chocar",
    "choquar": "chocar",
    # wrong infinitive form generated from conjugated base
    "discutar": "discutir",
    "pudar": "poder",
    "intuyo": "intuir",
    # reflexive/enclitic surface forms kept as-is by spaCy
    "tirarno": "tirar",
    "involucrarte": "involucrar",
    "prepararme": "preparar",
    # conjugated/subjunctive/imperative forms where spaCy keeps surface lemma
    "mire": "mirar",
    "agarra": "agarrar",
    "agarrir": "agarrar",
    "desespera": "desesperar",
    "desespero": "desesperar",
    "desesperir": "desesperar",
    "enseñas": "enseñar",
    "intente": "intentar",
    # past-participle adjective forms that should map to the verb infinitive
    "comparado": "comparar",
    "superado": "superar",
    "reflejado": "reflejar",
    "reconciliado": "reconciliar",
    # wrong accentuation / spelling produced by ASR
    "incómodar": "incomodar",
    "genuín": "genuino",
    "algun": "alguno",
    # wrong grammatical gender
    "zanahorio": "zanahoria",
    "tierro": "tierra",
}

# common ASR mistakes in auto-generated youtube captions
ASR_CONFUSIONS: dict[str, str] = {
    "pacer": "hacer",  # valid word, but almost always "hacer" in this corpus
    "parí": "para",
    "tetra": "teta",
    "reduela": "duele",
    "reduele": "duele",
}

# proper names that appear in this corpus and should not be lemmas
NAME_BLOCKLIST = frozenset({"mari", "aus", "redue", "paulo"})

# short but valid Spanish infinitives that must not be filtered as fragments
KNOWN_SHORT_INFINITIVES = frozenset({"ver", "ser", "ir", "dar"})

# prefer these when spaCy validates multiple bogus-stem candidates (e.g. veer vs ver)
PREFERRED_INFINITIVES = frozenset({
    "ver", "ser", "ir", "dar", "hacer", "tener", "venir", "poder", "decir",
    "saber", "querer", "poner", "salir", "venir", "caer", "valer", "doler",
    "sentir", "sacar", "charlar", "necesitar", "nacer", "servir", "usar",
})

INFINITIVE_RE = re.compile(r"^.+(ar|er|ir)$")
CONSONANT_CLUSTER_RE = re.compile(r"[^aeiouáéíóúüñ]{3,}")
GERUND_ENDINGS = (
    ("ándo", "ar"),
    ("ando", "ar"),
    ("iendo", "er"),
    ("íendo", "ir"),
)

# spaCy invents these suffixes from conjugated / voseo forms
BOGUS_LEMMA_SUFFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("astir", ("ar", "er", "ir")),
    ("elir", ("ar", "er", "ir")),
    ("eir", ("ar", "er", "ir")),
    ("astar", ("ar", "er", "ir")),
    ("ístir", ("ir", "er", "ar")),
    ("istir", ("ir", "er", "ar")),
    ("atir", ("ar", "er", "ir")),
    ("íar", ("er", "ir", "ar")),
    ("lear", ("ar",)),
    ("uelar", ("ar", "er", "ir")),
    ("uar", ("ar", "er", "ir")),
)


def extract_subtitle_text(content: str) -> str:
    """Strip subtitle sequence numbers, timestamps, and markup; keep spoken text."""
    content = html.unescape(content)
    content = CENSOR_PLACEHOLDER_RE.sub(" ", content)

    lines: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper() == "WEBVTT":
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if line.isdigit():
            continue
        if "-->" in line or TIMESTAMP_RE.match(line):
            continue
        line = HTML_TAG_RE.sub("", line)
        line = VTT_INLINE_TAG_RE.sub("", line)
        if line:
            lines.append(line)
    return " ".join(lines)


def read_input_text(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() in {".srt", ".vtt"}:
        return extract_subtitle_text(content)
    return content


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = CENSOR_PLACEHOLDER_RE.sub(" ", text)
    text = DIGIT_RE.sub("", text)
    text = NON_WORD_RE.sub(" ", text)
    return text.lower().strip()


def gerund_to_infinitive(text: str) -> str | None:
    """mirándolo → mirar; strip clitics first, then undo gerund ending."""
    stem = ENCLITIC_SUFFIX_RE.sub("", text)
    for gerund, ending in GERUND_ENDINGS:
        if stem.endswith(gerund):
            return stem[: -len(gerund)] + ending
    return None


def _validate_infinitive(candidate: str, nlp: spacy.Language) -> bool:
    parsed = nlp(candidate)
    if not parsed:
        return False
    token = parsed[0]
    return token.lemma_.lower() == candidate and token.pos_ in {"VERB", "AUX"}


def _stem_variants(stem: str) -> list[str]:
    """stem variants with trailing accent stripped first (veí → ve, veí)."""
    if stem and stem[-1] in "áéíóú":
        return [stem[:-1], stem]
    return [stem]


def _pick_best_infinitive(candidates: list[str]) -> str | None:
    if not candidates:
        return None
    corrected = [LEMMA_CORRECTIONS.get(c, c) for c in candidates]
    preferred = [c for c in corrected if c in PREFERRED_INFINITIVES]
    if preferred:
        return min(preferred, key=len)
    return min(corrected, key=len)


def recover_from_bogus_lemma(lemma: str, nlp: spacy.Language) -> str | None:
    """strip known spaCy bogus suffixes and validate a recovered infinitive."""
    for suffix, endings in BOGUS_LEMMA_SUFFIXES:
        if lemma.endswith(suffix) and len(lemma) > len(suffix) + 1:
            root = lemma[: -len(suffix)]
            matches: list[str] = []
            for variant in _stem_variants(root):
                for ending in endings:
                    candidate = variant + ending
                    if _validate_infinitive(candidate, nlp):
                        matches.append(candidate)
            picked = _pick_best_infinitive(matches)
            if picked:
                return LEMMA_CORRECTIONS.get(picked, picked)
    return None


def _guess_from_stem(stem: str, nlp: spacy.Language) -> str | None:
    gerund = gerund_to_infinitive(stem)
    if gerund and _validate_infinitive(gerund, nlp):
        return gerund

    # preterite: hablé → hablar, charló → charlar
    if re.search(r"[éó]$", stem) and len(stem) > 3:
        root = stem[:-1]
        for ending in ("ar", "er", "ir"):
            candidate = root + ending
            if _validate_infinitive(candidate, nlp):
                return candidate

    # preterite tú: usaste → usar, caíste → caer
    for suffix in ("aste", "iste"):
        if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
            root = stem[: -len(suffix)]
            for ending in ("ar", "er", "ir"):
                candidate = root + ending
                if _validate_infinitive(candidate, nlp):
                    return candidate

    # imperfect: tenía / tenías / veíamos → tener / ver
    for suffix in ("íamos", "íais", "ías", "ía"):
        if stem.endswith(suffix) and len(stem) > len(suffix):
            root = stem[: -len(suffix)]
            matches: list[str] = []
            for variant in _stem_variants(root):
                for ending in ("er", "ir", "ar"):
                    candidate = variant + ending
                    if _validate_infinitive(candidate, nlp):
                        matches.append(candidate)
            picked = _pick_best_infinitive(matches)
            if picked:
                return picked

    # subjunctive present: necesitemos → necesitar
    for suffix in ("emos", "áis", "an"):
        if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
            root = stem[: -len(suffix)]
            for ending in ("ar", "er", "ir"):
                candidate = root + ending
                if _validate_infinitive(candidate, nlp):
                    return candidate

    # voseo present: nacés → nacer, sentís → sentir, mirás → mirar
    for suffix in ("és", "ás", "ís"):
        if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
            root = stem[: -len(suffix)]
            for ending in ("er", "ir", "ar"):
                candidate = root + ending
                if _validate_infinitive(candidate, nlp):
                    return candidate

    # present: escucho → escuchar
    if stem.endswith("o") and len(stem) > 3:
        root = stem[:-1]
        for ending in ("ar", "er", "ir"):
            candidate = root + ending
            if _validate_infinitive(candidate, nlp):
                return candidate

    return None


def guess_infinitive_from_conjugated(text: str, nlp: spacy.Language) -> str | None:
    """recover infinitive when spaCy keeps the conjugated surface form as lemma."""
    # try the full form first so verb endings (-emos, -aste) are not eaten as clitics
    for stem in (text, ENCLITIC_SUFFIX_RE.sub("", text)):
        if not stem:
            continue
        guessed = _guess_from_stem(stem, nlp)
        if guessed:
            return guessed
    return None


def is_garbage_lemma(lemma: str) -> bool:
    """reject obvious caption/ASR junk that should not appear in a frequency list."""
    if lemma in LEMMA_BLOCKLIST or lemma in NAME_BLOCKLIST:
        return True
    if not re.search(r"[aeiouáéíóúü]", lemma):
        return True
    if CONSONANT_CLUSTER_RE.search(lemma):
        return True
    if lemma.endswith("ubar"):  # youtubar, etc.
        return True
    # short -ción fragments from broken captions (e.g. "sción" from "ascensión")
    if lemma.endswith("ción") and len(lemma) < 6:
        return True
    # caption fragments from truncated verbs (e.g. "pid" from "pide/piden")
    if (
        len(lemma) <= 3
        and lemma not in KNOWN_SHORT_INFINITIVES
        and lemma.endswith(("id", "ir", "ar", "er"))
    ):
        return True
    if len(lemma) <= 2:
        return True
    return False


def apply_lemma_corrections(lemma: str, text: str) -> str:
    return LEMMA_CORRECTIONS.get(lemma) or LEMMA_CORRECTIONS.get(text) or lemma


def _looks_conjugated_verb(text: str) -> bool:
    """detect finite verb surface forms spaCy often mis-tags as ADJ/NOUN."""
    return bool(
        re.search(r"[éó]", text)
        or re.search(r"(íamos|íais|ías|emos|áis|ís|ás|és|aste|iste|aba|aban)$", text)
    )


def normalize_lemma(token: Token, nlp: spacy.Language) -> str | None:
    """return a clean single-word lemma, or None to skip this token."""
    lemma = token.lemma_.lower().strip()
    text = token.text.lower().strip()

    if not lemma or not text:
        return None

    if text in NAME_BLOCKLIST:
        return None

    # short proper names from subtitles (Mari, Aus, etc.)
    if (
        token.pos_ == "PROPN"
        and len(text) <= 5
        and not _looks_conjugated_verb(text)
    ):
        return None

    # spaCy attaches clitic pronouns to verb lemmas: "decir él" from decirle
    if " " in lemma:
        parts = lemma.split()
        if len(parts) == 2 and parts[1] in CLITIC_PRONOUNS:
            base = parts[0]
            # "char él" from charla/charlo — spaCy mis-parses short stems as verb+clitic
            if text == f"{base}la" and len(base) < 5:
                lemma = text
            elif text == f"{base}lo" and len(base) < 6:
                if _validate_infinitive(base, nlp):
                    lemma = base
                else:
                    # charlo → char él: stem is charl, not char
                    stem = text[:-2]
                    for ending in ("ar", "er", "ir"):
                        candidate = stem + ending
                        if _validate_infinitive(candidate, nlp):
                            lemma = candidate
                            break
                    else:
                        lemma = base
            else:
                lemma = base
        else:
            return None

    # recover from -elir artifacts (dáselir, ponelir) by re-lemmatizing the stem
    if lemma.endswith("elir") and lemma != text:
        stem = ENCLITIC_SUFFIX_RE.sub("", text)
        if stem and stem != text:
            stem_lemma = nlp(stem)[0].lemma_.lower()
            if (
                stem_lemma
                and " " not in stem_lemma
                and not stem_lemma.endswith("elir")
                and len(stem_lemma) >= 3
            ):
                lemma = stem_lemma
            else:
                return None
        else:
            return None

    lemma = apply_lemma_corrections(lemma, text)

    # gerund + clitic: mirándolo → mirar
    if lemma == text or not INFINITIVE_RE.match(lemma):
        gerund = gerund_to_infinitive(text)
        if gerund:
            lemma = gerund

    # recover bogus spaCy lemmas (veíar, sentíar, caístir, charler, etc.)
    if not INFINITIVE_RE.match(lemma) or lemma == text:
        recovered = recover_from_bogus_lemma(lemma, nlp)
        if recovered:
            lemma = recovered

    # finite verb forms spaCy fails on: hablé, tenías, nacés, saqué, etc.
    needs_guess = not INFINITIVE_RE.match(lemma) or lemma == text
    can_guess = token.pos_ in {"VERB", "AUX"} or (
        token.pos_ in {"ADJ", "NOUN", "PROPN"} and _looks_conjugated_verb(text)
    )
    if needs_guess and can_guess:
        guessed = guess_infinitive_from_conjugated(text, nlp)
        if guessed:
            lemma = guessed
        else:
            lemma = apply_lemma_corrections(lemma, text)

    # ASR confusion pairs from auto-captions
    lemma = ASR_CONFUSIONS.get(lemma, lemma)
    lemma = ASR_CONFUSIONS.get(text, lemma)
    lemma = apply_lemma_corrections(lemma, text)

    if is_garbage_lemma(lemma):
        return None

    return lemma


def process_file(file_path: Path, nlp: spacy.Language, freq_dict: Counter[str]) -> Counter[str]:
    text = clean_text(read_input_text(file_path))
    doc = nlp(text)

    for token in doc:
        if not token.is_alpha or token.is_stop:
            continue
        lemma = normalize_lemma(token, nlp)
        if lemma:
            freq_dict[lemma] += 1

    return freq_dict


def load_existing_frequencies(csv_path: Path) -> Counter[str]:
    freq = Counter()
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = row.get("lemma", "").strip()
            count = row.get("frequency", row.get("frecuencia", "0")).strip()
            if lemma and count.isdigit():
                freq[lemma] = int(count)
    return freq


def save_frequency(freq_dict: Counter[str], output_path: Path, output_format: str = "csv") -> None:
    sorted_freq = sorted(freq_dict.items(), key=lambda item: item[1], reverse=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        payload = [{"lemma": lemma, "frequency": count} for lemma, count in sorted_freq]
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["lemma", "frequency"])
            writer.writerows(sorted_freq)

    print(f"Saved {len(sorted_freq)} lemmas to {output_path}")


def collect_input_files(paths: list[Path | str]) -> list[Path]:
    files: list[Path] = []
    for path_value in paths:
        path = Path(path_value)
        if path.is_dir():
            for suffix in SUBTITLE_SUFFIXES:
                files.extend(sorted(path.glob(f"*{suffix}")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"Input path not found: {path}")
    return files


def load_spacy_model(model_name: str) -> spacy.Language:
    return spacy.load(model_name)


def read_source_urls(sources_path: Path) -> list[str]:
    urls: list[str] = []
    for line in sources_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def _timestamp_part_to_seconds(hours: str, minutes: str, seconds: str, fraction: str) -> float:
    milliseconds = int(fraction.ljust(3, "0")[:3])
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + milliseconds / 1000


def get_subtitle_duration_seconds(file_path: Path) -> float:
    if file_path.suffix.lower() not in {".srt", ".vtt"}:
        return 0.0

    max_end = 0.0
    for match in TIMESTAMP_RANGE_RE.finditer(file_path.read_text(encoding="utf-8")):
        *_, end_h, end_m, end_s, end_frac = match.groups()
        max_end = max(max_end, _timestamp_part_to_seconds(end_h, end_m, end_s, end_frac))
    return max_end


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0m"

    total_minutes = int(round(seconds / 60))
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def print_frequency_summary(
    freq: Counter[str],
    input_files: list[Path],
    *,
    goal: int = DEFAULT_LEMMA_GOAL,
) -> None:
    unique_lemmas = len(freq)
    total_occurrences = sum(freq.values())

    timed_files = [
        (path, duration)
        for path in input_files
        if path.suffix.lower() in {".srt", ".vtt"}
        for duration in [get_subtitle_duration_seconds(path)]
        if duration > 0
    ]
    total_seconds = sum(duration for _, duration in timed_files)
    video_count = len(timed_files)

    print("\n--- Summary ---")
    progress = min(unique_lemmas / goal, 1.0) if goal > 0 else 0.0
    print(f"Unique lemmas: {unique_lemmas:,} (goal: {goal:,} — {progress:.1%})")
    print(f"Total word occurrences: {total_occurrences:,}")

    if video_count:
        label = "video" if video_count == 1 else "videos"
        print(f"Content processed: {format_duration(total_seconds)} across {video_count} {label}")

    if goal > 0 and unique_lemmas >= goal:
        print(f"Goal of {goal:,} unique lemmas reached.")
        return

    if total_seconds > 0 and unique_lemmas > 0 and goal > unique_lemmas:
        lemmas_per_hour = unique_lemmas / (total_seconds / 3600)
        seconds_needed = (goal - unique_lemmas) / lemmas_per_hour * 3600
        print(f"Estimate to reach {goal:,} lemmas: ~{format_duration(seconds_needed)} more content")
        if video_count > 0:
            avg_seconds = total_seconds / video_count
            videos_needed = max(1, int(round(seconds_needed / avg_seconds)))
            print(
                f"  (~{videos_needed} videos at ~{format_duration(avg_seconds)} each, "
                f"{lemmas_per_hour:.0f} lemmas/hour)"
            )
    elif unique_lemmas > 0:
        print("Add subtitle files with timestamps to get a time estimate toward your goal.")