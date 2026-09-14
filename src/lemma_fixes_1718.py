"""Issue #17/#18 lemma fixes applied onto src.utils at import time.

Keeps the large heuristic/table updates in a focused module so they can be
reviewed and shipped without rewriting all of utils.py in one MCP payload.
"""

from __future__ import annotations

import re
from typing import Any

import spacy


def apply_to_module(ns: dict[str, Any]) -> None:
    """Mutate utils module globals: extend tables and replace heuristics."""
    ENCLITIC_SUFFIX_RE = ns["ENCLITIC_SUFFIX_RE"]
    INFINITIVE_RE = ns["INFINITIVE_RE"]
    PREFERRED_INFINITIVES = ns["PREFERRED_INFINITIVES"]
    LEMMA_CORRECTIONS = ns["LEMMA_CORRECTIONS"]
    _validate_infinitive = ns["_validate_infinitive"]
    _pick_best_infinitive = ns["_pick_best_infinitive"]
    gerund_to_infinitive = ns["gerund_to_infinitive"]
    _stem_variants = ns["_stem_variants"]

    # --- tables ---
    ns["LEMMA_BLOCKLIST"] = ns["LEMMA_BLOCKLIST"] | frozenset({
        "mapping",
        "sharenting",
        "ong",
        "cheno",
        "pueri",
        "fidico",
    })
    ns["NAME_BLOCKLIST"] = ns["NAME_BLOCKLIST"] | frozenset({
        "fil",
        "filma",
        "picasso",
        "twitter",
        "xiaomi",
        "siri",
    })
    ns["PREFERRED_INFINITIVES"] = PREFERRED_INFINITIVES | frozenset({
        "descubrir", "escribir", "abrir", "cubrir", "sufrir", "traer", "devolver",
        "arrepentir", "enojar", "contar", "esperar", "perder", "volver", "mostrar",
        "mirar", "dejar", "llamar", "amar", "hablar", "escuchar",
    })
    PREFERRED_INFINITIVES = ns["PREFERRED_INFINITIVES"]

    LEMMA_CORRECTIONS.update({
        "repetirtir": "repetir",
        "repetirte": "repetir",
        "traigo": "traer",
        "devuelvar": "devolver",
        "arrepientir": "arrepentir",
        "enogir": "enojar",
        "deciar": "decir",
        "américar": "américa",
        "esperabar": "esperar",
        "ido": "ir",
        "ansiós": "ansioso",
        "mamás": "mamá",
        "tenéi": "tener",
        "miramir": "mirar",
    })

    def _pick_confident_infinitive(candidates: list[str]) -> str | None:
        """like _pick_best_infinitive, but refuse a tie between non-preferred inventions.

        For a pure -er/-ir tie from 1sg preterite (-í), prefer -ir when the stem looks
        like a typical -ir verb (descubrir/escribir/abrir); otherwise keep refusing
        unless PREFERRED_INFINITIVES already resolved it.
        """
        if not candidates:
            return None
        corrected = [LEMMA_CORRECTIONS.get(c, c) for c in candidates]
        preferred = [c for c in corrected if c in PREFERRED_INFINITIVES]
        if preferred:
            return min(preferred, key=len)
        unique = list(dict.fromkeys(corrected))
        if len(unique) == 1:
            return unique[0]
        if len(unique) == 2:
            er = next((c for c in unique if c.endswith("er")), None)
            ir = next((c for c in unique if c.endswith("ir")), None)
            if er and ir and er[:-2] == ir[:-2]:
                stem = er[:-2]
                if re.search(r"(br|cr|dr|fr|gr|pr|tr|vr|scr)$", stem) or stem.endswith(
                    ("r", "b")
                ):
                    return ir
        return None

    def _guess_from_stem(stem: str, nlp: spacy.Language) -> str | None:
        gerund = gerund_to_infinitive(stem, nlp)
        if gerund and _validate_infinitive(gerund, nlp):
            return gerund

        # ASR trailing vowel on voseo imperative: tenéi → tené → tener
        if stem.endswith("éi") and len(stem) > 4:
            stripped = stem[:-1]
            picked = _guess_from_stem(stripped, nlp)
            if picked:
                return picked

        # preterite / voseo imperative: hablé → hablar, tené → tener
        if re.search(r"[éó]$", stem) and len(stem) > 3:
            root = stem[:-1]
            matches = [
                root + ending
                for ending in ("ar", "er", "ir")
                if _validate_infinitive(root + ending, nlp)
            ]
            picked = _pick_best_infinitive(matches)
            if picked:
                return picked

        # voseo -ar imperative (contá→contar). exclude mamá/papá/sofá.
        if (
            stem.endswith("á")
            and len(stem) >= 4
            and stem not in {"mamá", "papá", "sofá"}
        ):
            candidate = stem[:-1] + "ar"
            if _validate_infinitive(candidate, nlp) and (
                len(stem) > 4 or candidate in PREFERRED_INFINITIVES
            ):
                return LEMMA_CORRECTIONS.get(candidate, candidate)

        for suffix in ("aste", "iste"):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
                root = stem[: -len(suffix)]
                for ending in ("ar", "er", "ir"):
                    candidate = root + ending
                    if _validate_infinitive(candidate, nlp):
                        return candidate

        for suffix in (
            "íamos", "íais", "ías", "ía", "ábamos", "abais", "aban", "abas", "aba"
        ):
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

        for suffix in ("imos", "amos"):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
                root = stem[: -len(suffix)]
                if suffix == "amos":
                    matches = [
                        root + ending
                        for ending in ("ar", "er", "ir")
                        if _validate_infinitive(root + ending, nlp)
                    ]
                    ar_matches = [c for c in matches if c.endswith("ar")]
                    picked = _pick_best_infinitive(ar_matches) or _pick_confident_infinitive(
                        matches
                    )
                else:
                    matches = [
                        root + ending
                        for ending in ("er", "ir")
                        if _validate_infinitive(root + ending, nlp)
                    ]
                    picked = _pick_confident_infinitive(matches)
                if picked:
                    return picked

        for suffix in ("emos", "áis", "an"):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
                root = stem[: -len(suffix)]
                for ending in ("ar", "er", "ir"):
                    candidate = root + ending
                    if _validate_infinitive(candidate, nlp):
                        return candidate

        for suffix in ("és", "ás", "ís"):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
                root = stem[: -len(suffix)]
                for ending in ("er", "ir", "ar"):
                    candidate = root + ending
                    if _validate_infinitive(candidate, nlp):
                        return candidate

        if stem.endswith("í") and len(stem) > 3:
            root = stem[:-1]
            matches = [
                root + ending
                for ending in ("er", "ir")
                if _validate_infinitive(root + ending, nlp)
            ]
            picked = _pick_confident_infinitive(matches)
            if picked:
                return picked

        if stem.endswith("o") and len(stem) > 3:
            root = stem[:-1]
            for ending in ("ar", "er", "ir"):
                candidate = root + ending
                if _validate_infinitive(candidate, nlp):
                    return candidate

        return None

    def guess_infinitive_from_conjugated(text: str, nlp: spacy.Language) -> str | None:
        stripped = ENCLITIC_SUFFIX_RE.sub("", text)
        if (
            stripped
            and stripped != text
            and len(stripped) >= 5
            and INFINITIVE_RE.match(stripped)
            and _validate_infinitive(stripped, nlp)
        ):
            return LEMMA_CORRECTIONS.get(stripped, stripped)

        stems = [text]
        if stripped and stripped != text:
            stems.append(stripped)
            if stripped[-1] in "aei" and len(stripped) >= 4:
                accented = stripped[:-1] + {"a": "á", "e": "é", "i": "í"}[stripped[-1]]
                stems.append(accented)
        for stem in stems:
            if not stem:
                continue
            guessed = _guess_from_stem(stem, nlp)
            if guessed:
                return guessed

        if stripped and stripped != text and stripped.endswith("a") and len(stripped) >= 4:
            root = stripped[:-1]
            candidate = root + "ar"
            if _validate_infinitive(candidate, nlp) and (
                len(root) >= 4 or candidate in PREFERRED_INFINITIVES
            ):
                return LEMMA_CORRECTIONS.get(candidate, candidate)
        return None

    def _looks_conjugated_verb(text: str) -> bool:
        if re.search(r"[éó]", text):
            return True
        if re.search(
            r"(íamos|íais|ías|emos|áis|ís|ás|és|aste|iste|ábamos|abais|aban|abas|aba|imos|amos|éi|í)$",
            text,
        ):
            return True
        stem = ENCLITIC_SUFFIX_RE.sub("", text)
        if stem != text and len(stem) >= 4 and stem[-1] in "aeiáéí":
            return True
        return False

    ns["_pick_confident_infinitive"] = _pick_confident_infinitive
    ns["_guess_from_stem"] = _guess_from_stem
    ns["guess_infinitive_from_conjugated"] = guess_infinitive_from_conjugated
    ns["_looks_conjugated_verb"] = _looks_conjugated_verb
