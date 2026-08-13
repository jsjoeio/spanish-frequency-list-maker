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
- `BOGUS_LEMMA_SUFFIXES`
- `recover_from_bogus_lemma`, `guess_infinitive_from_conjugated`, `_guess_from_stem`, `gerund_to_infinitive`, `is_garbage_lemma`, `apply_lemma_corrections`, `_looks_conjugated_verb`

También leé `tests/test_normalize_lemma.py` para no romper cobertura existente.

## Paso 2 — Reproducir cada fallo

Para cada lema, corré `normalize_lemma` en aislamiento y en una oración corta rioplatense. Usá el venv del repo:

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

show('VISTE', 'viste lo que pasó')
"
```

Anotá: superficie, `token.lemma_` / `pos_` de spaCy, resultado de `normalize_lemma`, y dónde se corta el pipeline (clíticos, bogus suffix, guess, corrections, ASR, garbage).

## Paso 3 — Diagnosticar patrones

Agrupá los fallos en clases, no en casos sueltos. Prestá especial atención a:

- voseo (`-ás`, `-és`, `-ís`, imperativos)
- clíticos y lemas con espacio (`decir él`)
- inventos de spaCy con sufijos raros (`-íar`, `-astir`, `-istir`, `-elir`)
- ASR de YouTube (`pacer`/`hacer`, recortes, confusiones)
- género/número colapsado al masculino
- nombres propios y basura de captions
- formas finitas que spaCy tagea como `NOUN`/`ADJ` y el guesser no corre

## Paso 4 — Proponer (este orden)

Preferí la solución más general que sea segura:

1. Heurísticas / funciones de recovery (`_guess_from_stem`, `_looks_conjugated_verb`, orden en `normalize_lemma`)
2. Nuevos patrones en `BOGUS_LEMMA_SUFFIXES` (o regla equivalente)
3. Entradas en `LEMMA_CORRECTIONS`
4. Entradas en `LEMMA_BLOCKLIST` / `NAME_BLOCKLIST` / `ASR_CONFUSIONS`
5. Rediseño del orden de `normalize_lemma` solo si el orden actual causa fallos sistemáticos

Un parche de dict está bien cuando el caso es irregular de verdad (p. ej. `pacer` → `hacer` en este corpus) o el falso positivo de una heurística sería peor.

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

## Respuesta

Estructurá así:

1. **Diagnóstico** — patrones, con evidencia de la reproducción
2. **Propuestas priorizadas** — tabla o lista con los 4 campos de arriba
3. **Qué hice / qué falta** — si implementaste, decí qué tests corrieron; si no, qué aplicarías primero
