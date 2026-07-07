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


# ============================================================
# Bottom-500 lemma improvements (issue #6)
# ============================================================


# --- bogus spaCy verb stems (-ir/-er/-ar endings on non-infinitives) ---


def test_acomodir_to_acomodar():
    assert lemma_for("acomodir") == "acomodar"


def test_acompañer_to_acompañar():
    assert lemma_for("acompañer") == "acompañar"


def test_animir_to_animar():
    assert lemma_for("animir") == "animar"


def test_auténticar_to_autenticar():
    assert lemma_for("auténticar") == "autenticar"


def test_busquar_busquer_to_buscar():
    assert lemma_for("busquar") == "buscar"
    assert lemma_for("busquer") == "buscar"


def test_banquar_to_bancar():
    assert lemma_for("banquar") == "bancar"


def test_cociner_to_cocinar():
    assert lemma_for("cociner") == "cocinar"


def test_contamir_to_contaminar():
    assert lemma_for("contamir") == "contaminar"


def test_escucher_to_escuchar():
    assert lemma_for("escucher") == "escuchar"


def test_esperser_to_esperar():
    assert lemma_for("esperser") == "esperar"


def test_estarer_to_estar():
    assert lemma_for("estarer") == "estar"


def test_festegir_to_festejar():
    assert lemma_for("festegir") == "festejar"


def test_fíjatar_to_fijar():
    assert lemma_for("fíjatar") == "fijar"


def test_guardir_to_guardar():
    assert lemma_for("guardir") == "guardar"


def test_hacar_hagar_to_hacer():
    assert lemma_for("hacar") == "hacer"
    assert lemma_for("hagar") == "hacer"


def test_irer_to_ir():
    assert lemma_for("irer") == "ir"


def test_jodar_to_joder():
    assert lemma_for("jodar") == "joder"


def test_juzguir_to_juzgar():
    assert lemma_for("juzguir") == "juzgar"


def test_querrir_to_querer():
    assert lemma_for("querrir") == "querer"


def test_sigar_to_seguir():
    assert lemma_for("sigar") == "seguir"


def test_uner_to_unir():
    assert lemma_for("uner") == "unir"


# --- enclitic / reflexive surface forms ---


def test_corregidme_to_corregir():
    assert lemma_for("corregidme") == "corregir"


def test_definirte_to_definir():
    assert lemma_for("definirte") == "definir"


def test_despidiéndotar_to_despedir():
    assert lemma_for("despidiéndotar") == "despedir"


def test_decilar_to_decir():
    assert lemma_for("decilar") == "decir"


def test_dormirmir_to_dormir():
    assert lemma_for("dormirmir") == "dormir"


def test_hagámoslo_to_hacer():
    assert lemma_for("hagámoslo") == "hacer"


def test_mirate_to_mirar():
    assert lemma_for("mirate") == "mirar"


def test_preguntándotar_to_preguntar():
    assert lemma_for("preguntándotar") == "preguntar"


def test_pruébalar_to_probar():
    assert lemma_for("pruébalar") == "probar"


def test_sacárselo_to_sacar():
    assert lemma_for("sacárselo") == "sacar"


def test_tirame_to_tirar():
    assert lemma_for("tirame") == "tirar"


def test_vincularno_to_vincular():
    assert lemma_for("vincularno") == "vincular"


# --- irregular conjugated forms ---


def test_eche_to_echar():
    """eche (subjunctive/imperative of echar) → echar."""
    assert lemma_for("eche") == "echar"


def test_elegí_to_elegir():
    assert lemma_for("elegí") == "elegir"


def test_levantabar_to_levantar():
    assert lemma_for("levantabar") == "levantar"


def test_logre_to_lograr():
    assert lemma_for("logre") == "lograr"


def test_naciero_to_nacer():
    assert lemma_for("naciero") == "nacer"


def test_ofrezcar_to_ofrecer():
    assert lemma_for("ofrezcar") == "ofrecer"


def test_tuvierar_to_tener():
    assert lemma_for("tuvierar") == "tener"


# --- wrong gender ---


def test_lactancio_to_lactancia():
    assert lemma_for("lactancio") == "lactancia"


def test_neofobio_to_neofobia():
    assert lemma_for("neofobio") == "neofobia"


# --- garbage / noise forms rejected ---


def test_bottom_500_garbage_rejected():
    assert lemma_for("achir") is None       # spaCy bogus lemma from ache (noise)
    assert lemma_for("arbolitar") is None   # not a real verb
    assert lemma_for("blancir") is None     # unclear/not standard
    assert lemma_for("callera") is None     # not a word
    assert lemma_for("dábir") is None       # unclear bogus form
    assert lemma_for("dej") is None         # fragment
    assert lemma_for("dido") is None        # not a Spanish word
    assert lemma_for("diciéndar") is None   # unclear bogus form
    assert lemma_for("díado") is None       # bogus form
    assert lemma_for("direr") is None       # unclear
    assert lemma_for("ehh") is None         # noise
    assert lemma_for("helicópterar") is None  # not a real verb
    assert lemma_for("macame") is None      # unclear
    assert lemma_for("maner") is None       # unclear
    assert lemma_for("matetar") is None     # not a real verb
    assert lemma_for("moody") is None       # English
    assert lemma_for("neurólogar") is None  # not a real verb
    assert lemma_for("purro") is None       # unclear/not standard
    assert lemma_for("redificiil") is None  # ASR noise (garbled "difícil")
    assert lemma_for("stickers") is None    # English plural
    assert lemma_for("sunami") is None      # misspelling
    assert lemma_for("tattoar") is None     # spaCy bogus lemma from tattoo
    assert lemma_for("tattoo") is None      # English
    assert lemma_for("terapiar") is None    # not a real verb
    assert lemma_for("terapéuticar") is None  # not a real verb
    assert lemma_for("vivar") is None       # not standard
    assert lemma_for("wonder") is None      # English
    assert lemma_for("anónimar") is None    # not a real verb
    assert lemma_for("contact") is None     # English


# --- proper names rejected ---


def test_bottom_500_names_rejected():
    assert lemma_for("catalina") is None
    assert lemma_for("chacón") is None
    assert lemma_for("fikri") is None
    assert lemma_for("freud") is None
    assert lemma_for("lorenzo") is None
    assert lemma_for("machado") is None
    assert lemma_for("urquiza") is None


# ============================================================
# Bottom-500 additional fixes (issue #8)
# ============================================================


# --- bogus spaCy verb derivations from genuine nouns/adjectives ---


def test_karma_preserved():
    assert lemma_for("karma") == "karma"


def test_kilómetro_preserved():
    assert lemma_for("kilómetro") == "kilómetro"


def test_parámetro_preserved():
    assert lemma_for("parámetro") == "parámetro"


def test_ira_preserved():
    assert lemma_for("ira") == "ira"


def test_ingesta_preserved():
    assert lemma_for("ingesta") == "ingesta"


def test_verdulería_preserved():
    assert lemma_for("verdulería") == "verdulería"


def test_durazno_preserved():
    assert lemma_for("durazno") == "durazno"


def test_bocina_preserved():
    assert lemma_for("bocina") == "bocina"


def test_psicólogo_preserved():
    assert lemma_for("psicólogo") == "psicólogo"


def test_psicológico_preserved():
    assert lemma_for("psicológico") == "psicológico"


def test_pedagógico_preserved():
    assert lemma_for("pedagógico") == "pedagógico"


def test_terapista_preserved():
    assert lemma_for("terapista") == "terapista"


def test_quieto_preserved():
    assert lemma_for("quieto") == "quieto"


def test_ahorita_preserved():
    assert lemma_for("ahorita") == "ahorita"


def test_atmósfera_preserved():
    assert lemma_for("atmósfera") == "atmósfera"


def test_lupa_preserved():
    assert lemma_for("lupa") == "lupa"


def test_defecto_preserved():
    assert lemma_for("defecto") == "defecto"


def test_tóxico_preserved():
    assert lemma_for("tóxico") == "tóxico"


def test_toga_preserved():
    assert lemma_for("toga") == "toga"


def test_videollamada_preserved():
    assert lemma_for("videollamada") == "videollamada"


def test_melancolía_preserved():
    assert lemma_for("melancolía") == "melancolía"


def test_dicotomía_preserved():
    assert lemma_for("dicotomía") == "dicotomía"


def test_criaturita_to_criatura():
    assert lemma_for("criaturita") == "criatura"


# --- gender / word-form corrections ---


def test_triada_preserved():
    assert lemma_for("triada") == "triada"


def test_nana_preserved():
    assert lemma_for("nana") == "nana"


def test_peluche_from_peluches():
    assert lemma_for("peluches") == "peluche"


def test_bronca_preserved():
    """bronca (Rioplatense for anger) is distinct from adj bronco."""
    assert lemma_for("bronca") == "bronca"


def test_herida_preserved():
    """herida (wound, noun) is distinct from adj herido (injured)."""
    assert lemma_for("herida") == "herida"


def test_mordida_preserved():
    """mordida (bite/bribe, Rioplatense noun) is distinct from adj mordido."""
    assert lemma_for("mordida") == "mordida"


# --- verb form corrections ---


def test_represente_to_representar():
    assert lemma_for("represente") == "representar"


def test_minimiza_to_minimizar():
    assert lemma_for("minimiza") == "minimizar"


def test_acomoda_to_acomodar():
    assert lemma_for("acomoda") == "acomodar"


def test_crianzo_to_crianza():
    assert lemma_for("crianzo") == "crianza"


def test_repetirte_to_repetir():
    assert lemma_for("repetirte") == "repetir"


def test_abracer_to_abrazar():
    assert lemma_for("abracer") == "abrazar"


def test_jodiar_to_joder():
    assert lemma_for("jodiar") == "joder"


def test_estabir_to_estar():
    assert lemma_for("estabir") == "estar"


def test_estuvistar_to_estar():
    assert lemma_for("estuvistar") == "estar"


def test_podiar_to_poder():
    assert lemma_for("podiar") == "poder"


def test_respondar_to_responder():
    assert lemma_for("respondar") == "responder"


# --- garbage / noise forms rejected ---


def test_issue8_garbage_rejected():
    assert lemma_for("chipiado") is None       # unclear/non-standard
    assert lemma_for("encir") is None          # bogus verb form
    assert lemma_for("evertido") is None       # not a real Spanish word
    assert lemma_for("figonar") is None        # unclear/noise
    assert lemma_for("odar") is None           # unclear form
    assert lemma_for("organicémar") is None    # ASR/noise garbage
    assert lemma_for("rarir") is None          # bogus lemma
    assert lemma_for("sirito") is None         # unclear/noise
    assert lemma_for("sticker") is None        # English (plural stickers already blocked)
    assert lemma_for("superpoderós") is None   # noise/neologism
    assert lemma_for("tailandio") is None      # wrong form (tailandés is correct)
    assert lemma_for("tapamo") is None         # noise/fragment
    assert lemma_for("tientar") is None        # non-standard form


# --- proper name rejected ---


def test_pérez_rejected():
    assert lemma_for("pérez") is None