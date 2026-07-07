"""Tests for lemma normalization."""

import spacy

from src.utils import (
    gerund_to_infinitive,
    guess_infinitive_from_conjugated,
    is_garbage_lemma,
    normalize_lemma,
    recover_from_bogus_lemma,
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


def test_charlo_and_charler_map_to_charlar():
    assert lemma_for("charlo") == "charlar"
    assert lemma_for("charler") == "charlar"
    assert lemma_in_sentence("yo charlo con mi hijo", "charlo") == "charlar"
    assert lemma_in_sentence("nada, es cuestión de charlarlo", "charlarlo") == "charlar"


def test_caption_junk_rejected():
    assert lemma_for("ner") is None
    assert lemma_for("sción") is None
    assert lemma_for("nbsp") is None
    assert lemma_for("pid") is None


# --- conjugated verbs → infinitive ---


def test_preterite_to_infinitive():
    assert lemma_for("hablé") == "hablar"
    assert lemma_in_sentence("yo hablé con mi hijo", "hablé") == "hablar"
    assert lemma_for("saqué") == "sacar"


def test_present_to_infinitive():
    assert lemma_for("escucho") == "escuchar"
    assert lemma_in_sentence("no escucho a nadie", "escucho") == "escuchar"


def test_imperfect_to_infinitive():
    assert lemma_for("tenía") == "tener"
    assert lemma_for("tenías") == "tener"
    assert lemma_in_sentence("como tenía buen peso", "tenía") == "tener"
    assert lemma_in_sentence("no veíamos nada", "veíamos") == "ver"
    assert lemma_in_sentence("la veía sola", "veía") == "ver"


def test_imaginar_conjugations():
    assert lemma_for("imaginé") == "imaginar"
    assert lemma_for("imagino") == "imaginar"
    assert lemma_in_sentence("me imaginé que", "imaginé") == "imaginar"


def test_subjunctive_to_infinitive():
    assert lemma_for("necesitemos") == "necesitar"
    assert lemma_in_sentence("incluyo necesitemos que", "necesitemos") == "necesitar"


def test_voseo_to_infinitive():
    assert lemma_for("nacés") == "nacer"
    assert lemma_in_sentence("sentís que nacés con el", "nacés") == "nacer"
    assert lemma_in_sentence("sentís que nacés con el", "sentís") == "sentir"


# --- gerund + clitic ---


def test_gerund_with_clitic_to_infinitive():
    assert gerund_to_infinitive("mirándolo") == "mirar"
    assert gerund_to_infinitive("mirándome") == "mirar"
    assert lemma_for("mirándolo") == "mirar"
    assert lemma_in_sentence("estoy mirándolo", "mirándolo") == "mirar"


# --- bogus spaCy lemma recovery ---


def test_bogus_suffix_recovery():
    assert recover_from_bogus_lemma("veíar", nlp) == "ver"
    assert recover_from_bogus_lemma("sentíar", nlp) == "sentir"
    assert recover_from_bogus_lemma("arreglatir", nlp) == "arreglar"
    assert recover_from_bogus_lemma("caístir", nlp) == "caer"
    assert recover_from_bogus_lemma("usastar", nlp) == "usar"
    assert recover_from_bogus_lemma("saquar", nlp) == "sacar"


def test_bogus_lemma_forms_in_context():
    assert lemma_for("sentíamos") == "sentir"
    assert lemma_for("caíste") == "caer"
    assert lemma_for("usaste") == "usar"
    assert lemma_for("arreglatir") == "arreglar"


# --- ASR confusion fixes ---


def test_asr_confusions():
    assert lemma_for("pacer") == "hacer"
    assert lemma_for("parí") == "para"
    assert lemma_in_sentence("disfruté pero parí haber disfrutado", "parí") == "para"
    assert lemma_for("tetra") == "teta"
    assert lemma_in_sentence("mi tetra y me dice", "tetra") == "teta"
    assert lemma_in_sentence("eso me reduela", "reduela") == "duele"


# --- proper names filtered ---


def test_proper_names_rejected():
    assert lemma_for("mari") is None
    assert lemma_for("aus") is None
    assert lemma_in_sentence("sí, mari me dijo", "mari") is None
    assert lemma_in_sentence("escuchame. aus, me gustaría", "aus") is None


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
    assert lemma_for("marido") == "marido"
    assert lemma_for("ver") == "ver"
    assert lemma_for("flipar") == "flipar"
    assert lemma_for("cesárea") == "cesárea"


# --- guess_infinitive helper ---


def test_guess_infinitive_from_conjugated():
    assert guess_infinitive_from_conjugated("hablé", nlp) == "hablar"
    assert guess_infinitive_from_conjugated("tenías", nlp) == "tener"
    assert guess_infinitive_from_conjugated("escucho", nlp) == "escuchar"
    assert guess_infinitive_from_conjugated("necesitemos", nlp) == "necesitar"
    assert guess_infinitive_from_conjugated("nacés", nlp) == "nacer"
    assert guess_infinitive_from_conjugated("veíamos", nlp) == "ver"


# ============================================================
# Bottom-100 lemma improvements (issue #4)
# ============================================================


# --- bogus suffix forms ---


def test_astir_bogus_suffix_recovery():
    """soldastir and similar -astir forms are recovered to their infinitive."""
    assert lemma_for("soldastir") == "soldar"


def test_ayudser_to_ayudar():
    assert lemma_for("ayudser") == "ayudar"


def test_trasladir_to_trasladar():
    assert lemma_for("trasladir") == "trasladar"


def test_discutar_to_discutir():
    assert lemma_for("discutar") == "discutir"


# --- reflexive / enclitic surface forms ---


def test_tirarno_to_tirar():
    assert lemma_for("tirarno") == "tirar"


def test_involucrarte_to_involucrar():
    assert lemma_for("involucrarte") == "involucrar"


def test_infinitive_plus_clitic():
    """normalize_lemma strips infinitive+clitic via LEMMA_CORRECTIONS safety net."""
    assert lemma_for("prepararme") == "preparar"


# --- irregular paradigm forms ---


def test_pudar_to_poder():
    assert lemma_for("pudar") == "poder"


def test_intuyo_to_intuir():
    assert lemma_for("intuyo") == "intuir"


def test_choqué_to_chocar():
    assert lemma_for("choqué") == "chocar"
    assert lemma_for("choquar") == "chocar"


# --- conjugated / subjunctive forms kept by spaCy ---


def test_mire_to_mirar():
    assert lemma_for("mire") == "mirar"


def test_agarra_to_agarrar():
    assert lemma_for("agarra") == "agarrar"
    assert lemma_for("agarrir") == "agarrar"
    assert lemma_in_sentence("ella agarra el libro", "agarra") == "agarrar"


def test_desespera_to_desesperar():
    assert lemma_for("desespera") == "desesperar"
    assert lemma_for("desespero") == "desesperar"
    assert lemma_for("desesperir") == "desesperar"
    assert lemma_in_sentence("me desespera todo", "desespera") == "desesperar"


def test_enseñas_to_enseñar():
    assert lemma_for("enseñas") == "enseñar"
    assert lemma_in_sentence("enseñas muy bien", "enseñas") == "enseñar"


def test_intente_to_intentar():
    assert lemma_for("intente") == "intentar"


# --- past-participle adjectives → verb infinitive ---


def test_past_participle_adjectives_to_infinitive():
    assert lemma_for("comparado") == "comparar"
    assert lemma_for("superado") == "superar"
    assert lemma_for("reflejado") == "reflejar"
    assert lemma_in_sentence("estaba reconciliado con su pasado", "reconciliado") == "reconciliar"
    assert lemma_in_sentence("comparado con antes era mejor", "comparado") == "comparar"


# --- wrong accentuation / spelling ---


def test_incómodar_to_incomodar():
    assert lemma_for("incómodar") == "incomodar"


def test_genuín_to_genuino():
    assert lemma_for("genuín") == "genuino"


def test_algun_to_alguno():
    assert lemma_for("algun") == "alguno"


# --- wrong grammatical gender ---


def test_zanahorio_to_zanahoria():
    assert lemma_for("zanahorio") == "zanahoria"


def test_tierro_to_tierra():
    assert lemma_for("tierro") == "tierra"


# --- garbage forms rejected ---


def test_bottom_100_garbage_rejected():
    assert lemma_for("sti") is None
    assert lemma_for("rós") is None
    assert lemma_for("vwer") is None
    assert lemma_for("tremeo") is None
    assert lemma_for("tremear") is None
    assert lemma_for("ahoritir") is None
    assert lemma_for("paular") is None


# --- proper names rejected ---


def test_paulo_rejected():
    assert lemma_for("paulo") is None