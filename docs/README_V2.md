# 🧠 La mémoire qui trie — V2 : graphe daté, deux axes, provenance

*Évolution du prototype (cf. `README.md` pour la V1). Le V2 corrige les défauts mesurés en V1
— suicide de la mémoire au mois 3, fragilité du juge sur la récence, piège « ancien ≠ périmé » —
par un changement de **modèle de stockage**.*

---

## 1. Les quatre idées du V2

```
 R1 · SURPRISE        Une confirmation ne modifie jamais le contenu. Seule une contradiction
                      factuelle agit — et c'est une CLÔTURE, pas une destruction : l'ancien
                      reste vrai comme HISTOIRE (« était PDG jusqu'en mai 2026 »).

 R2 · DEUX AXES       L'ancien score unique se scinde en :
                        • FORCE     — vivacité / retrouvabilité (nourrie par l'ACCÈS)
                        • CERTITUDE — validité actuelle (nourrie par la CORROBORATION)
                      Orthogonaux : un fait peut être fort & incertain, ou faible & certain.

 R3 · GRAPHE          Entités + faits datés reliés. Entrée vectorielle (évocation floue), puis
                      MARCHE le long des liens (le PDG → la personne → son conjoint → son métier).

 R4 · PROVENANCE      La consultation nourrit la Force ; SEULE la corroboration par une source
                      INDÉPENDANTE nourrit la Certitude. Répéter n'est pas corroborer (anti-rumeur).
```

**Le déplacement-clé :** la détection de contradiction **quitte la lecture pour l'écriture**
(fait contre fait, dates contre dates, sans LLM dans la boucle). Le juge de lecture ne peut plus
qu'alimenter la Force ; il ne peut plus *éteindre* un fait. Le talon d'Achille du juge V1 (15 % de
fausses contradictions du récent) est ainsi **structurellement désarmé** : le défaut existe encore
dans le modèle, mais il n'a plus accès à l'arme.

---

## 2. Modèle de données

- **Entité** : `id`, `nom`, `alias[]`, `embedding`, `date_creation`.
- **Fait** (arête datée) : `(sujet, prédicat, objet)`, `embedding`, **Force**, **Certitude**,
  `provenance[]` (sources + dates), bornes temporelles (`valide_de`, `valide_jusqua`), compteur
  d'accès, flag `noyau`, et un **statut** :
  - `courant` · `clos` (remplacé, reste vrai comme histoire) · `disputé` (deux valeurs en
    concurrence) · `dormant` (Force basse — exclu de l'évocation, mais TOUJOURS navigable par le
    graphe). **On ne supprime jamais.**
- **Ontologie des prédicats** (`v2_ontologie.py`) : chaque prédicat est `fonctionnel` ou
  multi-valué, et porte une **volatilité** qui gouverne la décroissance de la Certitude :
  `immuable` (jamais — fondations, naissances : « ancien ≠ périmé » réglé DANS LES DONNÉES) ·
  `stable` (730 j) · `changeant` (180 j) · `volatil` (45 j).

**Règle du menteur** : un fait à **une seule source** a sa Certitude plafonnée à 0.60 tant
qu'aucune source indépendante ne le corrobore.

---

## 3. Les trois procédures

- **Écriture** (`v2_modele.ingerer`) : extraction LLM → triplet ; résolution d'entité ; puis
  comparaison aux faits existants → **corroboration** (Certitude ↑, si source nouvelle) /
  **répétition même source** (Force ↑, Certitude inchangée) / **conflit fonctionnel** → CLÔTURE
  (si le nouveau est plus récent *et* indépendant) ou DISPUTÉ (si la vérité en place est corroborée
  et le nouveau à source unique : la vérité résiste au menteur).
- **Lecture** (`v2_lecture.lire`) : entrée vectorielle pondérée par la Force (dormants exclus) →
  **marche de graphe** (atteint clos/dormant si un lien y mène, et **réveille** un dormant accédé) →
  **rendu épistémique VERBAL** (jamais de chiffre — leçon V1) :
  `courant sûr` → présent · `courant incertain` → « serait…, à revérifier » · `clos` → imparfait
  borné · `disputé` → les deux valeurs avec leurs sources.
- **Sommeil** (`v2_modele.sommeil`) : décroissances → **promotion noyau** (≥3 sources ET ≥5 accès
  → demi-vies doublées) → fusion d'entités doublonnes → **dormance bidimensionnelle** (un fait n'est
  endormi que s'il est faible ET peu attesté ; un fait ≥3 sources reste évocable malgré une Force
  basse — *ce que le monde atteste résiste à l'oubli*).

---

## 4. Comment lancer

```powershell
$env:PYTHONUTF8=1 ; $py = "C:\ProgramData\miniconda3\python.exe"
& $py etape_v2_1_ingestion.py     # micro-test ÉCRITURE (corroboration, clôture, menteur, immuable)
& $py etape_v2_2_lecture.py       # micro-test LECTURE (entrée + marche + grammaire épistémique)
& $py etape_v2_3_sommeil.py       # micro-test SOMMEIL (dormance bidim., réveil, fusion, noyau)
& $py etape_v2_duel_repondeurs.py # mini-duel llama vs qwen → choix du répondeur
& $py etape_v2_4_grand_run.py     # grand run comparatif (A/B/B′/C-v2)
& $py etape_v2_5_durci.py         # métrique stricte + fixes (retrieval, plancher) → chiffres finaux
```

Répondeur retenu (mini-duel, 10 questions) : **`qwen3:30b-a3b`** — 10/10 de fidélité épistémique,
**0 refus** (vs llama 2 refus). Décidé sur mesure, pas au flair.

---

## 5. Résultats du grand run (métrique STRICTE)

> **Métrique stricte (anti-hedging)** : juste = la bonne valeur citée **ET**, pour un fait changé,
> l'ancienne non réassertée comme courante (l'imparfait borné « était… jusqu'en… » reste correct).

| Config | **Faits changés** (décisif) | Faits stables | Global |
|---|---|---|---|
| A — modèle seul | 0 % | 0 % | 0 % |
| B — RAG inerte daté | 15 % | 95 % | 55 % |
| B′ — RAG inerte aveugle | 15 % | 95 % | 55 % |
| **C-v2 — graphe daté** | **70 %** | 45 % | **58 %** |
| *C-v1-verbale (réf. monde V1)* | *87 %* | *70 %* | *78 %* |

**C-v2 domine la métrique décisive : 70 % sur les faits changés, contre 15 % pour les deux RAG
inertes (~4,7×)**, et passe devant en global. Sur un monde où la réponse change, dater, clôturer
l'ancien et hiérarchiser bat l'entrepôt qui ressort tout en vrac.

### Leçon méthodologique — l'artefact de hedging
Avec une notation par sous-chaîne, B′ (aveugle) affichait **90 %** : il « gagnait » en **déversant
l'ancienne ET la nouvelle valeur** (le matcher trouvait la bonne parmi le lot). La **métrique
stricte**, qui exige de *trancher*, fait tomber B′ de **75 % → 15 %** sur les changés. **Récompenser
le hedging est un piège de mesure classique : il faut exiger l'engagement, pas la présence.**

### Décomposition des erreurs — greffier vs architecte
La santé de l'**ingestion** (le *greffier* : extraction + résolution) et celle de la **mémoire**
(l'*architecte* : tri + rendu + retrouvé) se lisent séparément :

| Famille | Erreurs | Verdict |
|---|---|---|
| 🖊️ Greffier | **1 / 17** | **Sain.** Extraction 100 % (244/244), 0 énoncé perdu. |
| 🏛️ Architecte | **16 / 17** | Le résidu — surtout les **faits stables** (45 % vs 95 % pour l'inerte). |

**Pourquoi C-v2 perd sur les faits stables :** ce n'est pas un défaut de stockage, mais **le prix de
l'oubli**. Un fait stable rarement consulté pendant 12 mois voit sa Force décroître et **sort de
l'entrée vectorielle** (dormance) ; l'entrepôt inerte, lui, n'oublie jamais, donc le retrouve
toujours. Le fait reste navigable par le graphe, mais la question directe ne l'évoque plus. Arbitrage
de conception assumé — et **proprement imputé à l'architecte, pas au greffier**.

### Les trois tests propres au V2
- ✅ **Menteur** : **5/5** vérités corroborées résistent à une source unique (après ajout d'un
  **plancher de Certitude** à 0.55 pour les faits ≥2 sources — assez haut pour battre un mensonge
  récent qui décline, assez bas pour rester « à revérifier » s'il n'est jamais reconfirmé).
- ✅ **Rumeur** : une même source répétant 5× un faux plafonne à C=0.21 (≤ 0.60). Répéter ≠ prouver.
- ✅ **Dupont** : 3/3 faits stables jamais reconfirmés rendus **avec réserve**, ni tus ni affirmés
  au présent.

---

## 6. Limites connues

- **Faits stables rarement consultés** : la dormance les exclut de l'évocation directe (architecte).
  Pistes : inclure les dormants dans l'entrée vectorielle avec pénalité, ou abaisser leur seuil de
  dormance selon la Certitude.
- **Double rôle de qwen** : extracteur + juge d'usage + répondeur. Un même biais pourrait se corréler
  entre les rôles. Garde-fou actuel : la contradiction reste **règle/données** (jamais un verdict de
  lecture), et l'extraction est mesurée à part (greffier sain). À diversifier dans une version future.
- **Mesure** : automatique par correspondance (avec la métrique stricte). Un contrôle manuel et un
  juge-correcteur indépendant resteraient souhaitables.
- **Monde synthétique** : 40 entités, faits fictifs, déterministes. Indicatif, pas encore du réel.

---

## 7. Fichiers V2

```
v2_ontologie.py   prédicats + volatilité + gabarits de phrase (présent/imparfait/groupe)
v2_extraction.py  extraction LLM de triplets (qwen, JSON strict) — la surface d'erreur « greffier »
v2_modele.py      Entite, Fait (deux axes), GrapheMemoire : résolution, écriture, sommeil
v2_lecture.py     entrée vectorielle (+ variante boostée), marche de graphe, rendu épistémique
v2_monde.py       monde enrichi (sources nommées, volatilité, injections menteur/rumeur/Dupont)
etape_v2_1..5     micro-tests (écriture, lecture, sommeil), duel, grand run, durcissement
resultats/        rapports markdown + JSON ; logs/ journaux
```

---

## Suite — la V3 (l'axe Importance)

Un **troisième axe** — l'**Importance** (structurelle, ne décroît pas) — a été ajouté pour protéger
les faits *qui comptent* de la dormance. L'ablation a livré un verdict honnête : **la « porte »
d'entrée par nœud (reconnaissance/rappel) est le vrai correctif** (faits muets 16 → 6, stables
45 % → 85 %), tandis que **l'axe importance, lui, ne s'impose pas sur ce banc** — qui ne pose jamais
de question de *rappel libre*. Tout est documenté, y compris l'angle mort du protocole, dans
**`README_V3.md`**.

---

*Construit pas à pas, petit d'abord. La contradiction appartient à l'écriture ; la lecture nourrit
la flamme. Le greffier classe, l'architecte trie — et on sait désormais lire leur santé séparément.*
