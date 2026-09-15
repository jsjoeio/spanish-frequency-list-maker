"""Flagged-lemma coverage for issues #17 and #18."""

import spacy

from src.utils import normalize_lemma, recover_from_bogus_lemma

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


# ============================================================
# Flagged lemmas (issues #17 / #18)
# ============================================================


# --- recoverable conjugated / voseo / clitic forms ---


def test_contame_to_contar():
    """voseo imperative + enclitic: contame → contar."""
    assert lemma_for("contame") == "contar"
    assert lemma_in_sentence("contame qué pasó", "contame") == "contar"


def test_decime_to_decir():
    assert lemma_for("decime") == "decir"
    assert lemma_in_sentence("decime la verdad", "decime") == "decir"


def test_mirame_to_mirar():
    assert lemma_for("mirame") == "mirar"
    assert lemma_in_sentence("mirame a los ojos", "mirame") == "mirar"


def test_descubrí_to_descubrir():
    """1sg preterite -í er/ir tie should resolve to descubrir."""
    assert lemma_for("descubrí") == "descubrir"
    assert lemma_in_sentence("yo descubrí algo", "descubrí") == "descubrir"


def test_traigo_to_traer():
    assert lemma_for("traigo") == "traer"
    assert lemma_in_sentence("yo traigo el libro", "traigo") == "traer"


def test_tenéi_to_tener():
    """ASR trailing -i on voseo imperative tené."""
    assert lemma_for("tenéi") == "tener"
    assert lemma_in_sentence("tenéi paciencia", "tenéi") == "tener"


def test_ido_to_ir():
    assert lemma_for("ido") == "ir"
    assert lemma_in_sentence("he ido a casa", "ido") == "ir"


def test_nacimos_to_nacer():
    assert lemma_for("nacimos") == "nacer"
    assert lemma_in_sentence("nosotros nacimos acá", "nacimos") == "nacer"


def test_esperabas_to_esperar():
    """-ar imperfect -abas was missing from the guesser."""
    assert lemma_for("esperabas") == "esperar"
    assert lemma_in_sentence("vos no esperabas eso", "esperabas") == "esperar"


def test_amamos_hablamos_to_infinitive():
    assert lemma_for("amamos") == "amar"
    assert lemma_for("hablamos") == "hablar"


# --- stem-change / bogus spaCy infinitives ---


def test_devuelvar_to_devolver():
    assert lemma_for("devuelvar") == "devolver"


def test_arrepientir_to_arrepentir():
    assert lemma_for("arrepientir") == "arrepentir"


def test_enogir_to_enojar():
    assert lemma_for("enogir") == "enojar"


def test_deciar_to_decir():
    assert lemma_for("deciar") == "decir"


def test_américar_to_américa():
    assert lemma_for("américar") == "américa"


def test_quemastar_to_quemar():
    """already covered by -astar bogus suffix; keep regression coverage."""
    assert recover_from_bogus_lemma("quemastar", nlp) == "quemar"
    assert lemma_for("quemastar") == "quemar"


def test_issue18_repetirte_in_context():
    assert lemma_for("repetirte") == "repetir"
    assert lemma_in_sentence("quiero repetirte esto", "repetirte") == "repetir"


# --- gender / form / truncated adjectives ---


def test_ansiós_to_ansioso():
    assert lemma_for("ansiós") == "ansioso"


def test_mamás_to_mamá():
    assert lemma_for("mamás") == "mamá"
    assert lemma_in_sentence("las mamás vienen", "mamás") == "mamá"


# --- names / brands / English junk rejected ---


def test_issue17_18_names_and_brands_rejected():
    assert lemma_for("fil") is None
    assert lemma_for("filma") is None
    assert lemma_for("picasso") is None
    assert lemma_for("twitter") is None
    assert lemma_for("xiaomi") is None
    assert lemma_for("siri") is None


def test_issue17_18_english_and_noise_rejected():
    assert lemma_for("mapping") is None
    assert lemma_for("sharenting") is None
    assert lemma_for("ong") is None
    assert lemma_for("cheno") is None
    assert lemma_for("pueri") is None
    assert lemma_for("fidico") is None


# --- intentionally kept ---


def test_arder_kept():
    """arder is a real Spanish verb (to burn); do not block."""
    assert lemma_for("arder") == "arder"


def test_combo_kept():
    """combo is an established loanword in this corpus."""
    assert lemma_for("combo") == "combo"


# ============================================================
# Rebuild regressions: nouns/adjs must not become nonce verbs
# ============================================================


def test_tranquilo_family_stays_adjective():
    assert lemma_for("tranquilo") == "tranquilo"
    assert lemma_for("tranquila") == "tranquilo"
    assert lemma_in_sentence("estoy tranquilo ahora", "tranquilo") == "tranquilo"
    assert lemma_in_sentence("quedate tranquila", "tranquila") == "tranquilo"
    assert lemma_in_sentence("están tranquilos", "tranquilos") == "tranquilo"


def test_abuelo_abuela_stay_nouns():
    assert lemma_for("abuelo") == "abuelo"
    assert lemma_for("abuela") == "abuela"
    assert lemma_in_sentence("mi abuelo vive acá", "abuelo") == "abuelo"
    assert lemma_in_sentence("mi abuela cocina rico", "abuela") == "abuela"
    assert lemma_in_sentence("los abuelos vienen", "abuelos") == "abuelo"


def test_plural_nouns_not_stripped_as_enclitics():
    assert lemma_in_sentence("come fideos todos los días", "fideos") == "fideo"
    assert lemma_in_sentence("vi unos videos ayer", "videos") == "video"
    assert lemma_in_sentence("vi unos vídeos ayer", "vídeos") == "vídeo"
    assert lemma_in_sentence("hubo varios cambios", "cambios") == "cambio"
    assert lemma_in_sentence("dejó comentarios", "comentarios") == "comentario"
    assert lemma_in_sentence("mis hermanos son grandes", "hermanos") == "hermano"
    assert lemma_in_sentence("comió cereales", "cereales") == "cereal"
    assert lemma_in_sentence("el paquete llegó ayer", "paquete") == "paquete"
    assert lemma_in_sentence("un juguete nuevo", "juguete") == "juguete"
    assert lemma_in_sentence("te traje un regalo", "regalo") == "regalo"
    assert lemma_in_sentence("come chocolate todos los días", "chocolate") == "chocolate"


def test_adjective_plurals_not_verbed():
    assert lemma_in_sentence("las redes sociales", "sociales") == "social"
    assert lemma_in_sentence("temas laborales", "laborales") == "laboral"
    assert lemma_in_sentence("son profesionales", "profesionales") == "profesional"
    assert lemma_in_sentence("impactos medioambientales", "medioambientales") == "medioambiental"
    assert lemma_in_sentence("cosas fundamentales", "fundamentales") == "fundamental"


def test_estar_paradigm_not_ester():
    assert lemma_for("estás") == "estar"
    assert lemma_for("estés") == "estar"
    assert lemma_for("estabas") == "estar"
    assert lemma_for("estábamos") == "estar"
    assert lemma_in_sentence("estás bien vos", "estás") == "estar"
    assert lemma_in_sentence("estábamos en casa", "estábamos") == "estar"
    assert lemma_in_sentence("si estés tranquila", "estés") == "estar"


def test_íbamos_to_ir():
    assert lemma_for("íbamos") == "ir"
    assert lemma_in_sentence("íbamos a casa", "íbamos") == "ir"


def test_desayunábamos_to_desayunar():
    assert lemma_for("desayunábamos") == "desayunar"
    assert lemma_in_sentence("nosotros desayunábamos juntos", "desayunábamos") == "desayunar"


def test_voseo_enclitics_still_recover():
    """false-enclitic fix must not break contame/decime/mirame."""
    assert lemma_for("contame") == "contar"
    assert lemma_for("decime") == "decir"
    assert lemma_for("mirame") == "mirar"
    assert lemma_in_sentence("contame qué pasó", "contame") == "contar"
