# Bancs de non-régression — les verdicts des 5 prototypes, rejoués depuis la bibliothèque

Ces bancs rejouent les verdicts historiques des prototypes **en utilisant le code de la
bibliothèque `memoire/`** (et non plus les modules plats). Le juge de l'unification, c'est la
non-régression : un verdict qui ne retombe pas au chiffre près signale une régression cachée.

Les **fixtures de banc** (mondes gelés, vérités-terrain) restent à la racine — `structure_monde.py`,
`ariane_monde.py`, `v2_monde.py`, `embeddings.py`, `config.py` (params de banc : `MONDE_DEBUT`,
graine 42…). La bibliothèque ne dépend jamais d'elles ; ce sont les bancs qui les importent.

## Verdicts reproduits AU CHIFFRE PRÈS (déterministes, sans LLM)

| Banc | Verdict cible | Statut |
|---|---|---|
| `banc_typologie.py` | S1 = 52 % · S2 = 73 % · **S1+S2 = 91 %** · +décl = 100 % · frange 6/46 (asym.) | ✅ 5/5 |
| `banc_ariane.py` | P1 non-dormants 8/38 → 38/38 · complétude P1@T3 **porte 12 % → axe 58 %** (+46 pts) · pureté 8/0 | ✅ 6/6 |
| `../unitaires/test_coeur.py` | cœur V2 : menteur, anti-rumeur, clôture, immuable, plancher, Dupont, grammaire | ✅ 13/13 |
| `../unitaires/test_regle_or.py` | registre STRUCTURE : règle d'or (lire libre / tisser sourcé) | ✅ 17/17 |
| `../unitaires/test_inertie.py` | options OFF (importance, dormance modulée) inertes | ✅ 7/7 |

Garantie de reproductibilité : graine 42, mêmes générateurs, mêmes 31 paramètres `IMP_*`/`V2_*`
(vérifiés identiques au bit près entre `config.py` plat et `memoire/config.py`), même ordre
d'opérations (`décroître → importance → dormance`).

## Le seul verdict NON rejoué au chiffre près — et pourquoi ce n'est pas une perte

**« Faits muets : 16 → 6 avec la reconnaissance »** (prototype `etape_v3_3_grand_run.py`).

Ce chiffre est **mesuré à travers un LLM**, et même *deux* : le graphe est construit par le greffier
qwen (extraction), puis le compte de muets compare la réponse du répondeur qwen au fait. À
température 0 qwen est *largement* déterministe, mais pas garanti au fait près. **Relancer le
prototype plat lui-même ne redonnerait pas « 16 » à coup sûr.** Le « 16 → 6 » est donc conservé
comme **observation historique explicitement étiquetée « mesurée via LLM, non déterministe, non
rejouée au chiffre près »** — pas comme un test de non-régression.

Ce que l'on ne perd pas : le **mécanisme** sous-jacent (la reconnaissance/rappel qui rend lisibles
les faits dormants — « dé-mutiser ») est prouvé **déterministe et au chiffre exact** par
`banc_ariane.py` : `P1 non-dormants 8/38 → 38/38`. C'est le même phénomène que « 16 → 6 », mesuré
mécaniquement contre la vérité-terrain au lieu de passer par qwen. **Le proxy Ariane est la preuve
canonique ; le 16→6 n'en est que l'illustration LLM.**

## Décision d'architecture : un seul scoreur de retrieval (additif)

Le prototype avait **deux** fonctions de score :
- `entree_vectorielle_v2` — *multiplicatif* : `sim × (0.5 + 0.5·force)` (colonne baseline C-v2) ;
- `entree_vectorielle_v3` — *additif* : `W_SIM·sim + W_FORCE·force` (+ importance) (colonnes porte/axe).

La bibliothèque **consolide en un seul scoreur, l'additif** (`memoire/coeur/lecture.py:entree_vectorielle`),
le terme d'importance étant gated par `OPT_IMPORTANCE_RETRIEVAL`. Le multiplicatif (V2) est considéré
*superseded* et n'est **pas** réintroduit. Conséquence assumée : il n'existe plus de baseline
« C-v2 multiplicatif » exacte dans la bibliothèque.

Pourquoi c'est sans danger : le **seul** verdict que cette consolidation empêche de rejouer
exactement (la colonne C-v2) est **aussi le seul** qui passe par un LLM bruité. Rien de
déterministe n'est perdu — la simplification (une fonction au lieu de deux) ne coûte qu'un chiffre
qui n'était de toute façon pas reproductible au bit près.
