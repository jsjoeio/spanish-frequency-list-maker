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
        "mirar", "dejar", "llamar", "amar", "hablar", "escuchar", "estar",
        "ayudar", "preguntar", "sacar", "quedar", "fijar", "olvidar", "pasar",
        "acordar",
    })
    PREFERRED_INFINITIVES = ns["PREFERRED_INFINITIVES"]

    # spaCy invents -ábar from -ar imperfect (desayunábamos → desayunábar)
    ns["BOGUS_LEMMA_SUFFIXES"] = (("ábar", ("ar",)),) + ns["BOGUS_LEMMA_SUFFIXES"]

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

    _1PL_PERSON_RE = re.compile(r"(ábamos|íbamos|íamos|amos|emos|imos)$")
    _VOSEO_CLITIC_RE = re.compile(r"(me|te|se|nos)$")
    _EXPLICIT_FINITE_RE = re.compile(
        r"[éó]|(?:íamos|íais|ías|emos|áis|ís|ás|és|aste|iste|"
        r"ábamos|abais|aban|abas|aba|imos|amos|éi|íbamos|í)$"
    )

    def _ir_imperfect(stem: str) -> bool:
        return bool(re.fullmatch(r"í?ba(?:s|mos|is|n)?", stem))

    def _voseo_enclitic_host(text: str) -> str | None:
        """conta+me / deci+me, not noun endings (paquete, abuelo, fideos, sociales)."""
        m = _VOSEO_CLITIC_RE.search(text)
        if not m:
            return None
        host = text[: m.start()]
        if len(host) < 4:
            return None
        # hermanos/humanos: -no + s plural, not voseo + nos
        if m.group(1) == "nos" and text.endswith("nos") and text[:-1].endswith("no"):
            return None
        if host[-1] in "aá":
            return host
        if host[-1] in "ei":
            mapped = host[:-1] + {"e": "er", "i": "ir"}[host[-1]]
            if mapped in PREFERRED_INFINITIVES or (host + "r") in PREFERRED_INFINITIVES:
                return host
        if host[-1] in "éí":
            mapped = host[:-1] + {"é": "er", "í": "ir"}[host[-1]]
            if mapped in PREFERRED_INFINITIVES:
                return host
        return None

    def _infinitive_from_voseo_host(host: str) -> str | None:
        if host[-1] in "aá":
            return host[:-1] + "ar"
        if host[-1] in "eé":
            return host[:-1] + "er"
        if host[-1] in "ií":
            return host[:-1] + "ir"
        return None

    def _guess_from_stem(stem: str, nlp: spacy.Language) -> str | None:
        gerund = gerund_to_infinitive(stem, nlp)
        if gerund and _validate_infinitive(gerund, nlp):
            return gerund

        if _ir_imperfect(stem):
            return "ir"

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

        # -ar imperfect is -aba; -er/-ir imperfect is -ía. Never try ester from estaba.
        for suffix in ("ábamos", "abais", "aban", "abas", "aba"):
            if stem.endswith(suffix) and len(stem) > len(suffix):
                matches = [
                    variant + "ar"
                    for variant in _stem_variants(stem[: -len(suffix)])
                    if _validate_infinitive(variant + "ar", nlp)
                ]
                picked = _pick_best_infinitive(matches)
                if picked:
                    return picked

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
                matches = [
                    root + ending
                    for ending in ("ar", "er", "ir")
                    if _validate_infinitive(root + ending, nlp)
                ]
                picked = _pick_best_infinitive(matches)
                if picked:
                    return picked

        # voseo present: -ás → -ar, -ís → -ir. -és is -er (tenés) or -ar subjunctive (estés).
        for suffix, endings in (("ás", ("ar",)), ("és", ("er", "ar")), ("ís", ("ir",))):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 1:
                root = stem[: -len(suffix)]
                matches = [
                    root + ending
                    for ending in endings
                    if _validate_infinitive(root + ending, nlp)
                ]
                picked = _pick_best_infinitive(matches)
                if picked:
                    return picked

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
        if not _1PL_PERSON_RE.search(text):
            host = _voseo_enclitic_host(text)
            if host:
                stems.append(host)
                if host[-1] in "aei":
                    stems.append(host[:-1] + {"a": "á", "e": "é", "i": "í"}[host[-1]])
            elif (
                stripped
                and stripped != text
                and INFINITIVE_RE.match(stripped)
            ):
                stems.append(stripped)
        for stem in stems:
            if not stem:
                continue
            guessed = _guess_from_stem(stem, nlp)
            if guessed:
                return guessed
        return None

    def _looks_conjugated_verb(text: str, token: Any | None = None) -> bool:
        if _EXPLICIT_FINITE_RE.search(text):
            return True
        host = _voseo_enclitic_host(text)
        if host is None:
            return False
        # chocolate/tomate: NOUN ending in -te, host ends in -a, but not a real voseo verb
        if token is not None and token.pos_ in {"NOUN", "ADJ"}:
            inf = _infinitive_from_voseo_host(host)
            if inf not in PREFERRED_INFINITIVES:
                return False
        return True

    ns["_pick_confident_infinitive"] = _pick_confident_infinitive
    ns["_guess_from_stem"] = _guess_from_stem
    ns["guess_infinitive_from_conjugated"] = guess_infinitive_from_conjugated
    ns["_looks_conjugated_verb"] = _looks_conjugated_verb
