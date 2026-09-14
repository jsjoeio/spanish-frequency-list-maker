---
name: fix-lemmas
description: >
  Diagnose and improve Spanish (rioplatense) lemma post-processing for failed
  lemmas that leaked into frequency.csv or were flagged by the user. Prefer
  general recovery heuristics over one-off dict patches. Use when the user
  pastes failed lemmas, says lemas fallidos/falladas, arreglar lemas, fix
  lemmas, revisar lemas, or runs /fix-lemmas.
argument-hint: "<lista de lemas fallidos>"
metadata:
  short-description: "Diagnose and fix failed rioplatense lemmas"
---

# Fix lemmas

Sos un experto en lingüística computacional del español rioplatense (Argentina/Uruguay): morfología verbal completa (voseo -ás/-és/-ís, pretéritos, subjuntivos, imperativos), lematización, y las fallas típicas de spaCy `es_core_news_sm` con voseo, clíticos y ruido de subtítulos automáticos (ASR).

El pipeline es spaCy + post-procesamiento en `src/utils.py`. El objetivo es mejorar **reglas generalizables**, no solo parches sueltos.

## Input

Tomá la lista de lemas fallidos del mensaje del usuario (o del argumento de `/fix-lemmas`). Cada ítem puede ser:

- el lema incorrecto solo (`viste`, `charler`)
- un mapeo (`viste` → `ver`, `charlo` → `charlar`)
- una nota (`nombres propios que se colaron`)

Si no hay lista, pedila. No mines `data/frequency.csv` a ciegas.

## Paso 1 — Leer el código actual

Leé estas secciones de `src/utils.py` (es la única fuente de verdad; no asumas el contenido de memoria):

- `normalize_lemma` y el orden de transformaciones
- `LEMMA_CORRECTIONS`, `LEMMA_BLOCKLIST`, `NAME_BLOCKLIST`, `ASR_CONFUSIONS`
- `BOGUS_LEMMA_SUFFIXES`, `PREFERRED_INFINITIVES`
- `recover_from_bogus_lemma`, `guess_infinitive_from_conjugated`, `_guess_from_stem`, `_pick_confident_infinitive`, `_pick_best_infinitive`
- `gerund_to_infinitive`, `is_garbage_lemma`, `apply_lemma_corrections`, `_looks_conjugated_verb`
- `prefer_irregular_theme`, `unaccent_infinitive`, `diminutive_base`

También leé `tests/test_normalize_lemma.py` para no romper cobertura existente.

Setup si hace falta (desde el root del repo):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

## Paso 2 — Reproducir cada fallo

Para cada lema, corré `normalize_lemma` en aislamiento **y** en una oración corta rioplatense (el POS de spaCy cambia y decide si corre el guesser). Usá el venv del repo:

```bash
.venv/bin/python -c "
import spacy
from src.utils import normalize_lemma
nlp = spacy.load('es_core_news_sm')

def show(word, sentence=None):
    tok = nlp(word)[0]
    isolated = normalize_lemma(tok, nlp)
    ctx = None
    if sentence:
        for t in nlp(sentence.lower()):
            if t.text.lower() == word.lower():
                ctx = normalize_lemma(t, nlp)
                break
    print(f'{word!r}: spaCy={tok.lemma_!r}/{tok.pos_} isolated={isolated!r} context={ctx!r}')

show('contame', 'contame qué pasó')
show('descubrí', 'yo descubrí algo')
show('esperabas', 'vos no esperabas eso')
"
```

Anotá: superficie, `token.lemma_` / `pos_` de spaCy, resultado de `normalize_lemma`, y dónde se corta el pipeline (clíticos, bogus suffix, guess, corrections, ASR, garbage).

**Importante:** hipótesis del issue (`tenéi → tener?`) no son verdad — verificá siempre con reproducción. Algunos “fallos” ya están resueltos (`quemastar` vía `-astar`, `repetirte` vía corrections) o son lemas válidos (`arder`, `combo`).

## Paso 3 — Diagnosticar patrones

Agrupá los fallos en clases, no en casos sueltos. Prestá especial atención a:

- **voseo presente** (`-ás`, `-és`, `-ís`) e **imperativo voseo** (`-á`/`-é`/`-í` sin -s: `contá`, `tené`)
- **imperativo + enclítico** (`contame`, `decime`, `mirame`): spaCy suele taggear `NOUN` y dejar la superficie; hace falta que `_looks_conjugated_verb` detecte el clítico y que `guess_infinitive_from_conjugated` pruebe stem / stem acentuado / `root+ar|er|ir`
- **infinitivo + clítico** (`repetirte`, `definirte`): strip de enclítico → infinitivo válido
- **pretérito 1sg `-í`**: spaCy inventa pares `descubrer`/`descubrir`; `_pick_confident_infinitive` debe romper el empate (PREFERRED o tipología de stem `-br/-r/-b`)
- **pretérito/presente 1pl** (`-amos` → preferir `-ar`; `-imos` → er/ir confiable)
- **imperfecto `-ar`** (`-aba/-abas/-aban/...`): no solo `-ía/-ías`
- **ASR sobre voseo** (`tenéi` = `tené` + `-i` espurio)
- **lemas bogus con diptongo de cambio vocálico** (`devuelvar`, `arrepientir`): el infinitivo real no lleva `ue`/`ie`; suelen ir a `LEMMA_CORRECTIONS` (un undo general `ue→o`/`ie→e` rompe `frecuentar` porque spaCy “valida” casi todo)
- inventos de spaCy con sufijos raros (`-íar`, `-astir`, `-istar`, `-istir`, `-elir`, `-astar`)
- ASR de YouTube (`pacer`/`hacer`, recortes, confusiones `j`/`g`)
- género/número colapsado; adjetivos truncados (`ansiós` → `ansioso`)
- nombres propios, marcas, productos (`picasso`, `xiaomi`, `siri`, `twitter`) → `NAME_BLOCKLIST`
- inglés / neologismos / ruido (`mapping`, `sharenting`, `cheno`) → `LEMMA_BLOCKLIST`
- formas finitas que spaCy tagea como `NOUN`/`ADJ` y el guesser no corre sin `_looks_conjugated_verb`
- **no tocar** verbos reales ni préstamos asentados solo porque aparecieron en la lista (`arder`, `combo`)

## Paso 4 — Proponer (este orden)

Preferí la solución más general que sea segura:

1. Heurísticas / funciones de recovery (`_guess_from_stem`, `guess_infinitive_from_conjugated`, `_looks_conjugated_verb`, `_pick_confident_infinitive`, `PREFERRED_INFINITIVES`)
2. Nuevos patrones en `BOGUS_LEMMA_SUFFIXES` (o regla equivalente)
3. Entradas en `LEMMA_CORRECTIONS`
4. Entradas en `LEMMA_BLOCKLIST` / `NAME_BLOCKLIST` / `ASR_CONFUSIONS`
5. Rediseño del orden de `normalize_lemma` solo si el orden actual causa fallos sistemáticos

Un parche de dict está bien cuando el caso es irregular de verdad (p. ej. `traigo` → `traer`, `pacer` → `hacer`) o el falso positivo de una heurística sería peor (p. ej. undo `ue→o` sobre `frecuentar`, o regla `-á` con `len≤4` que convierte `mamá`→`mamar`).

Para cada propuesta:

- qué problema resuelve
- el cambio concreto (código o entry)
- confianza / falsos positivos
- si es general o parche puntual

Si el orden de `normalize_lemma` es frágil, proponé una reestructuración compatible hacia atrás.

## Paso 5 — Implementar

Implementá en el mismo turno si el usuario pidió aplicar/arreglar/implementar, o si `/fix-lemmas` vino con la lista y no pidió solo diagnóstico. Si solo pidió análisis, mostrá las propuestas y esperá.

Al implementar:

- agregá tests en `tests/test_normalize_lemma.py` (forma aislada + oración rioplatense cuando el POS importa)
- no dupliques keys que ya existen; extendé el mecanismo dueño del patrón
- no toques `data/frequency.csv` a menos que el usuario lo pida
- corré `.venv/bin/python -m pytest tests/test_normalize_lemma.py -q`
- si el skill quedó desactualizado (patrones nuevos, orden, falsos positivos), actualizá `.grok/skills/fix-lemmas/SKILL.md` en el mismo PR

## Respuesta

Estructurá así:

1. **Diagnóstico** — patrones, con evidencia de la reproducción
2. **Propuestas priorizadas** — tabla o lista con los 4 campos de arriba
3. **Qué hice / qué falta** — si implementaste, decí qué tests corrieron; si no, qué aplicarías primero
