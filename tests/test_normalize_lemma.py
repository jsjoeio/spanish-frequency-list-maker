"""Tests for lemma normalization."""

import spacy

from src.utils import normalize_lemma

nlp = spacy.load("es_core_news_sm")


def lemma_for(word: str) -> str | None:
    token = nlp(word)[0]
    return normalize_lemma(token, nlp)


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