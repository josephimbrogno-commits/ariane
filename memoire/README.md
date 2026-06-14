# La mémoire qui trie — `memoire/`

Une **mémoire externe pour LLM** qui ne se contente pas de stocker : elle **date**, elle **trie**,
elle **clôt sans détruire**, et elle **parle au bon temps**. Là où une base de données rend ce
qu'on y a mis, cette mémoire distingue ce qui est *courant* de ce qui *l'était*, ce dont elle est
*sûre* de ce qui est *à revérifier*, et ce qui est *capital* de ce qui est *trivial*.

Cette bibliothèque est l'**unification** de cinq prototypes validés chacun sur son banc
(V2 → V3 → Ariane → Typologie). Elle n'invente aucune fonctionnalité : elle consolide et durcit.
Le juge de cette unification est la **non-régression** — les verdicts des cinq étapes se reproduisent
à l'identique depuis le code unifié (voir [`tests/bancs/README_BANCS.md`](tests/bancs/README_BANCS.md)).

```python
from memoire import Memoire
from memoire.adaptateurs.ollama_qwen import OllamaLLM, faire_embed

mem = Memoire(llm=OllamaLLM(), embed=faire_embed())   # on INJECTE le modèle ; la lib est agnostique
mem.ecrire("En janvier 2026, le PDG de Nexora est Mme Karel.", source_id="Gazette",  date=...)
mem.ecrire("Depuis mai 2026, le PDG de Nexora est M. Doss.",   source_id="Officiel", date=...)
mem.consolider()
print(mem.lire("Qui dirige Nexora ?")["reponse"])     # → « Il s'agirait de M. Doss, à revérifier. »
```

L'exemple complet — l'histoire d'un fait qu'un fait plus récent vient clore — est dans
[`exemples/vitrine.py`](exemples/vitrine.py). C'est la vitrine : en ~20 lignes, on y voit la mémoire
dater, clore sans effacer, et parler au bon temps.

---

## La règle d'or (non négociable)

> **On LIT la toile librement ; on ne TISSE jamais un fil sans dire d'où il vient.**

Parcourir la structure (voisinage, liens, degrés) est libre et n'engage aucune croyance. Mais
**créer ou clore un lien passe TOUJOURS par un fait sourcé**, via le pipeline normal — provenance,
plafond du menteur, conflit, statut. C'est une fonction de **sécurité** : toute croyance reste
auditable, et il n'existe aucune porte dérobée pour imposer une vérité non tracée. `lier` sans
source échoue ; un `lier` qui contredit un fait corroboré devient *disputé* et plafonné, sans
détrôner la vérité corroborée.

---

## Les 6 gestes de l'API

`Memoire(llm, embed)` — le LLM et l'embedding sont **injectés**. La bibliothèque ne fabrique pas son
modèle ; tout hôte fournit le sien via une petite interface (`llm.texte`, `llm.json`, `embed`).

### Registre CONTENU — nourrir la mémoire par le monde
| Geste | Rôle |
|---|---|
| `ecrire(enonce, source_id, date=None)` | Ingère un énoncé : extraction → résolution → conflit / corroboration / clôture. |
| `lire(question, date=None)` | Entrée vectorielle (+ reconnaissance par nœud nommé) + marche de graphe → réponse au rendu épistémique verbal. |
| `consolider(date=None)` | Le « sommeil » : érosions de Force/Certitude, clôtures, dormance, promotion du noyau (+ options branchées). |

### Registre STRUCTURE — parcourir la toile, tisser des liens
| Geste | Rôle |
|---|---|
| `parcourir(entite, profondeur=1)` | **Lecture libre** du voisinage (liens, sens, degrés, statuts). N'écrit rien. |
| `lier(entite_a, relation, entite_b, source_id, date=None)` | Tisse un lien — **jamais sans source**. Sous le capot, un fait sourcé soumis au pipeline (plafond menteur, conflit). |
| `retoucher(fait_id, action, source_id, date=None)` | `clore` (exige source **et** date → « était… jusqu'à »), `contester`, `corroborer`. Toute retouche est sourcée. |

Plus `inspecter(fait_id | entite)` pour la transparence (état d'un fait, ou tous les faits d'une entité).

---

## Ce qui distingue cette mémoire d'une base de données

- **Deux axes orthogonaux** — la **Force** (vivacité : monte à la consultation, s'érode avec le
  temps) et la **Certitude** (validité : monte à la corroboration *indépendante*, s'érode selon la
  volatilité du prédicat). Un fait peut être vif mais douteux, ou sûr mais oublié.
- **Quatre statuts, jamais de suppression** — *courant* / *clos* (« était… jusqu'à ») / *disputé* /
  *dormant*. On n'efface pas : on clôt, on dispute, on endort.
- **Provenance & règle du menteur** — une source unique plafonne la Certitude à 0.60 ; corroborer,
  c'est une source *indépendante* (répéter la même source ne compte pas — anti-rumeur).
- **Contradiction à l'écriture** — fait contre fait, date contre date ; pas de juge de lecture qui
  arbitre le vrai.
- **Grammaire épistémique verbale** — présent pour le sûr, « il s'agirait de…, à revérifier » pour
  l'incertain, imparfait borné pour le clos, les deux valeurs pour le disputé, et le droit de dire
  « je ne sais pas ». Aucun chiffre de confiance dans la réponse.

---

## Les défauts sûrs (à l'installation)

| Interrupteur | Défaut | Effet |
|---|---|---|
| `OPT_RECONNAISSANCE` | **ON** | Entrée par nœud nommé : lit les faits dormants. Le vrai remède aux « faits muets ». |
| `OPT_TYPOLOGIE` | **ON** | Typologie DURABLE / ÉPHÉMÈRE d'un lien (lecture seule, n'altère aucune croyance). |
| `OPT_IMPORTANCE` | OFF | 3ᵉ axe (PageRank) calculé au sommeil. Inerte tant qu'OFF. |
| `OPT_IMPORTANCE_RETRIEVAL` | OFF | Terme d'importance dans le score de lecture. |
| `OPT_DORMANCE_MODULEE` | OFF | Seuil de dormance abaissé pour les faits importants. |

Défaut global : **V2 nu + reconnaissance/rappel + typologie en lecture**. Importance et dormance
modulée sont **OFF** et strictement **inertes** tant qu'on ne bascule pas l'interrupteur (prouvé
par `tests/unitaires/test_inertie.py`).

---

## L'historique : cinq verdicts chaînés

Chaque étape a été gelée sur son banc (graine loguée) AVANT observation, et son verdict lu sur les
cas-pièges — jamais sur des moyennes. Les READMEs d'étape (`README_V2/V3/ARIANE/TYPOLOGIE.md`)
gardent le détail.

1. **V2 — le tri à deux axes.** Force + Certitude, quatre statuts, règle du menteur. *Verdict :* la
   vérité corroborée résiste au menteur (5/5), l'anti-rumeur tient, un fait stable non reconfirmé
   passe « à revérifier ». → `tests/unitaires/test_coeur.py` (13/13).
2. **V3 — l'axe importance.** PageRank structurel, orthogonal au temps. *Verdict :* l'importance
   gagne sa place **en rappel libre**, mais l'importance *en dormance seule* introduisait du bruit —
   d'où son OFF par défaut, ON optionnel.
3. **Ariane — le rappel libre.** Banc mécanique (sans LLM) contre vérité-terrain. *Verdict :* la
   **reconnaissance** fait passer les faits capitaux dormants de **8/38 à 38/38** lisibles, et
   l'importance porte la complétude **12 % → 58 %** (+46 pts) sans effondrer la pureté.
   → `tests/bancs/banc_ariane.py` (6/6).
4. **Typologie — durable vs éphémère.** Structure seule (degrés, réciprocité, forme temporelle).
   *Verdict :* la structure suffit pour **91 %** des liens ; les 13 % aveugles sont exclusivement des
   durables asymétriques non datés, comblés sans bruit par une déclaration ciblée (→ 100 %).
   → `tests/bancs/banc_typologie.py` (5/5).
5. **Unification — la bibliothèque.** *Verdict :* les cinq verdicts se reproduisent à l'identique
   depuis `memoire/` — **48 vérifications déterministes vertes** (cœur 13 + règle d'or 17 +
   inertie 7 + typologie 5 + importance 6). La non-régression est le juge.

---

## Deux décisions assumées

1. **Un seul scoreur de retrieval (additif).** Le prototype avait deux fonctions de score
   (multiplicatif pour la baseline V2, additif pour V3). La bibliothèque n'en garde qu'**une**,
   l'additive ; le multiplicatif est *superseded* et n'est pas réintroduit. Une fonction au lieu de
   deux, et le seul verdict que ça empêche de rejouer exactement est aussi le seul à passer par un
   LLM bruité (voir ci-dessous) : rien de déterministe n'est perdu.
2. **« Faits muets 16 → 6 » = observation historique, pas test de non-régression.** Ce chiffre est
   mesuré à travers **deux** LLM (le greffier qui construit le graphe, le répondeur qui répond) ;
   relancer même le prototype plat ne le redonnerait pas au fait près. Il est conservé comme
   illustration LLM, **non rejouée au chiffre près**. Son **mécanisme** — la reconnaissance qui
   dé-mutise les dormants — est, lui, prouvé déterministe et exact par Ariane (8/38 → 38/38).

---

## Structure du dépôt

```
memoire/                  LA bibliothèque (agnostique du modèle)
  config.py               interrupteurs + paramètres, défauts sûrs
  coeur/                  ontologie · graphe (écriture, sommeil) · extraction · lecture
  options/                importance · typologie_liens · hook_consolidation
  adaptateurs/            ollama_qwen.py — exemple découplé (Ollama + sentence-transformers)
  api.py                  les 6 gestes + inspecter
exemples/vitrine.py       la mémoire en ~20 lignes
tests/
  unitaires/              test_coeur · test_regle_or · test_inertie  (stub embed, sans LLM)
  bancs/                  banc_typologie · banc_ariane  (non-régression des verdicts)
    + fixtures de banc    config · embeddings · structure_monde · ariane_monde
    archive_prototypes/   les 5 prototypes historiques (etape_*, v2_*, v3_*…) — non maintenus
```

### Lancer les tests déterministes
```bash
python tests/unitaires/test_coeur.py        # cœur V2          → 13/13
python tests/unitaires/test_regle_or.py     # règle d'or        → 17/17
python tests/unitaires/test_inertie.py      # options OFF inertes → 7/7
python tests/bancs/banc_typologie.py        # typologie 91 %    → 5/5
python tests/bancs/banc_ariane.py           # importance/rappel → 6/6  (charge le modèle d'embed)
```
