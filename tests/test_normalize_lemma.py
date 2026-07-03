"""Tests for lemma normalization."""

import spacy

from src.utils import (
    gerund_to_infinitive,
    guess_infinitive_from_conjugated,
    is_garbage_lemma,
    normalize_lemma,
)

nlp = spacy.load("es_core_news_sm")


def lemma_for(word: str) -> str | None:
    token = nlp(word)[0]
    return normalize_lemma(token, nlp)


def lemma_in_sentence(sentence: str, target: str) -> str | None:
    doc = nlp(sentence.lower())
    for token in doc:
        if token.text.lower() == target:
            return normalize_lemma(token, nlp)
    return None


# --- clitic pronouns (previous fixes) ---


def test_clitic_pronoun_stripped():
    assert lemma_for("decirle") == "decir"
    assert lemma_for("vincularlo") == "vincular"
    assert lemma_for("hacerlo") == "hacer"


def test_charla_not_truncated_to_char():
    assert lemma_for("charla") == "charla"


def test_caption_junk_rejected():
    assert lemma_for("ner") is None
    assert lemma_for("sción") is None
    assert lemma_for("nbsp") is None


# --- conjugated verbs → infinitive ---


def test_preterite_to_infinitive():
    assert lemma_for("hablé") == "hablar"
    assert lemma_in_sentence("yo hablé con mi hijo", "hablé") == "hablar"


def test_present_to_infinitive():
    assert lemma_for("escucho") == "escuchar"
    assert lemma_in_sentence("no escucho a nadie", "escucho") == "escuchar"


def test_imperfect_to_infinitive():
    assert lemma_for("tenía") == "tener"
    assert lemma_for("tenías") == "tener"
    assert lemma_in_sentence("como tenía buen peso", "tenía") == "tener"


def test_imaginar_conjugations():
    assert lemma_for("imaginé") == "imaginar"
    assert lemma_for("imagino") == "imaginar"
    assert lemma_in_sentence("me imaginé que", "imaginé") == "imaginar"


# --- gerund + clitic ---


def test_gerund_with_clitic_to_infinitive():
    assert gerund_to_infinitive("mirándolo") == "mirar"
    assert gerund_to_infinitive("mirándome") == "mirar"
    assert lemma_for("mirándolo") == "mirar"
    assert lemma_in_sentence("estoy mirándolo", "mirándolo") == "mirar"


# --- ASR confusion fixes ---


def test_asr_confusions():
    assert lemma_for("pacer") == "hacer"
    assert lemma_for("parí") == "para"
    assert lemma_in_sentence("disfruté pero parí haber disfrutado", "parí") == "para"


# --- garbage / loanword rejection ---


def test_garbage_lemmas_rejected():
    assert lemma_for("cambtico") is None
    assert lemma_for("youtubar") is None
    assert is_garbage_lemma("cambtico")
    assert is_garbage_lemma("youtubar")


# --- valid words we should keep ---


def test_valid_words_kept():
    assert lemma_for("celo") == "celo"
    assert lemma_for("chola") == "chola"
    assert lemma_for("hablar") == "hablar"
    assert lemma_for("tener") == "tener"


# --- guess_infinitive helper ---


def test_guess_infinitive_from_conjugated():
    assert guess_infinitive_from_conjugated("hablé", nlp) == "hablar"
    assert guess_infinitive_from_conjugated("tenías", nlp) == "tener"
    assert guess_infinitive_from_conjugated("escucho", nlp) == "escuchar"