# 🔥 La mémoire qui trie

*Prototype d'une mémoire externe à **péremption**, **surprise** et **sédiment**, pour un modèle de langage local.*

---

## 1. L'idée

Les LLM ont des poids figés : leur savoir n'a pas de date, ne se met pas à jour, et le RAG
classique n'est qu'un **entrepôt inerte** qui ressort l'ancien et le nouveau en vrac. Ce projet
teste une mémoire externe dotée de trois mécanismes, et la compare au modèle seul et au RAG
classique **sur des questions dont la réponse a changé au fil du temps**.

### Les trois mécanismes

```
   SURPRISE          un souvenir n'est réécrit que s'il est CONTREDIT par un fait plus récent.
   (le faux décline)   Une simple confirmation ne change pas le contenu — elle renforce.

   PÉREMPTION        chaque souvenir porte une date et une confiance qui DÉCROÎT avec le temps
   (l'oubli par défaut) s'il n'est ni consulté ni confirmé (décroissance exponentielle, demi-vie réglable).

   RENFORCEMENT      un souvenir consulté ET confirmé voit sa confiance remonter et sa date
   (la flamme entretenue) se rafraîchir. L'usage résiste à l'oubli ; l'oubli est le défaut.
```

**Hypothèse :** une mémoire dotée de ces trois mécanismes bat (a) le modèle seul et (b) un RAG
classique, sur les faits qui ont changé.

---

## 2. Comment ça marche (le cycle)

À chaque question : **recherche** (similarité cosinus → top-k souvenirs actifs) → **injection**
dans le prompt avec date et confiance → **réponse** du modèle → **juge** (2ᵉ appel, vérificateur
strict, verdict par souvenir : `CONFIRME` / `CONTREDIT` / `NON_UTILISE` / `INCERTAIN`) →
**mise à jour** (confiance + dates) → **érosion** temporelle → **consolidation** (« sommeil » :
fusion des doublons, archivage sous le seuil) toutes les N interactions.

Le temps de l'expérience est **simulé** (horloge virtuelle qu'on avance), pour compresser
12 mois en quelques minutes.

---

## 3. Installation

- **Python** : Miniconda (`C:\ProgramData\miniconda3`), avec `numpy`, `sentence-transformers`, `torch`.
- **Ollama** (déjà installé) servant deux modèles locaux :
  - Répondeur : `llama3.1:8b` (instruct 7-8 B)
  - Juge : `qwen3:30b-a3b` (plus fiable sur la récence — voir §6)
- **Embeddings** : `paraphrase-multilingual-MiniLM-L12-v2` (téléchargé au 1ᵉʳ lancement).

Tous les réglages sont dans **`config.py`** (un non-développeur peut les modifier).

---

## 4. Comment lancer chaque étape

```powershell
# (les scripts forcent l'UTF-8 et se placent dans leur dossier automatiquement)
$env:PYTHONUTF8=1
$py = "C:\ProgramData\miniconda3\python.exe"

& $py etape0_check.py            # vérifie l'environnement (modèle + embeddings répondent)
& $py etape1_micro.py            # micro-démo : 30 souvenirs, 10 questions, le cycle en clair
& $py etape1c_duel_decouple.py   # duel/ablation des juges (voir §6)
& $py etape1d_juge_scinde.py     # test du juge scindé (échec instructif, §6)
& $py etape2_experience.py       # expérience aux paramètres PAR DÉFAUT (échec expliqué, §5)
& $py etape3_sensibilite.py      # balayage de la demi-vie 60/120/240 + baseline B′ + dashboard
& $py etape3b_fix_verbal.py      # le fix « confiance verbale » (le tournant, §5)
```

Résultats dans `resultats/`, journaux dans `logs/`. **Le tableau de bord** :
`resultats/etape3_dashboard.html` (ouvrable d'un double-clic).

---

## 5. Résultats

### Les 3 configurations comparées

- **A** — modèle seul (aucune mémoire).
- **B** — RAG classique inerte (mêmes souvenirs, sans mise à jour). *Daté* = le texte du souvenir
  contient la date (« Depuis mai 2026… ») ; *aveugle* (**B′**) = texte sans aucune date.
- **C** — la mémoire qui trie (système complet, nourri chronologiquement sur 12 mois).

### Étape 2 — aux paramètres par défaut : un échec **expliqué**

Avec la demi-vie par défaut (30 j) sur 12 mois, **la mémoire de C s'auto-efface** : un fait perd
la moitié de sa confiance chaque mois, passe sous le seuil d'archivage (0.15) dès le **mois 3**, et
devient invisible à la recherche. Résultat : C ≈ 3 % (mémoire vide), tandis que B atteint 70 % sur
les faits changés. *C'est le « suicide du mois 3 » — un résultat, pas un bug (voir §6).*

### Étape 3 — balayage de la demi-vie (le seul curseur modifié)

| Demi-vie | C (changés) | C (stables) | Souvenirs actifs | Faux oublis | Conf. VRAIS vs PÉRIMÉS |
|---|---|---|---|---|---|
| 60 j  | 27 % | 0 %  | 18 / 95  | 77 / 95 | 0.14 vs 0.11 *(indistinct)* |
| 120 j | 53 % | 3 %  | 40 / 95  | 55 / 95 | 0.18 vs 0.10 |
| 240 j | 63 % | 37 % | 119 / 95 | 5 / 95  | **0.32 vs 0.17** *(nette séparation)* |

```
 C sur faits changés, selon la demi-vie :

 63% |                                   ● 240j     ── B (daté)  57%
 53% |                  ● 120j           ┄┄┄┄┄┄┄┄┄┄ ── B′ (aveugle) 43%
 43% |┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
 27% |   ● 60j
     +------------------------------------------
        60j        120j               240j
```

**Croisements (faits changés) :** C dépasse **B′ (baseline équitable) dès 120 j**, et dépasse
**B (daté) dès 240 j**. La mémoire distingue alors clairement le vrai du périmé (0.32 vs 0.17).

### Étape 3b — le tournant : la confiance **verbale**

À demi-vie 240 j, C perdait sur les faits *stables* (37 %) en **refusant de répondre** (« je n'ai
pas d'information ») alors que le fait était en mémoire : voir un **« 0.20 » en chiffre** rendait le
modèle timide. En remplaçant le nombre par une mention verbale (rien si la confiance est correcte,
*« à confirmer »* si elle est basse), tout change :

| Config (demi-vie 240 j) | Faits changés | Faits stables | Global | Refus |
|---|---|---|---|---|
| A — modèle seul | 0 % | 0 % | 0 % | — |
| B — RAG inerte **daté** | 57 % | 83 % | 70 % | — |
| B′ — RAG inerte **aveugle** | 43 % | 87 % | 65 % | — |
| C — confiance **numérique** | 60 % | 37 % | 48 % | 31 |
| **C — confiance VERBALE** ✅ | **87 %** | **70 %** | **78 %** | **6** |

### Verdict sur l'hypothèse

✅ **Confirmée sur la métrique décisive.** La mémoire qui trie (rendu verbal) atteint **87 % sur les
faits changés** — contre 57 % pour le RAG daté et 43 % pour le RAG aveugle — et **gagne globalement
(78 % vs 70 %)**. Dater, contredir l'ancien et entretenir le récent bat l'entrepôt qui ressort tout
en vrac.

⚠️ **Un sous-critère reste juste en deçà :** sur les faits *purement stables*, C (70 %) reste un peu
sous B (83 %) — un écart de ~4 questions, dont 6 refus résiduels. Honnêtement documenté, pas masqué.

---

## 6. Les trois échecs compris (les échecs font partie du résultat)

1. **Le prompt de juge « durci » (V2) a empiré le juge.** En voulant blinder le juge contre toutes
   les erreurs, le prompt long et défensif a *embrouillé* qwen (1 → 4 verdicts catastrophiques) et a
   même fait contredire un fait ancien-mais-vrai qu'il devait protéger. Leçon : **un prompt court +
   de bonnes données (les dates) battent un prompt long et défensif.** → on a gardé le prompt simple (V1).

2. **Le juge scindé a échoué.** Séparer le juge en deux détecteurs étanches (conflits ⟂ usage, règle
   *« le conflit bat l'usage »*) semblait plus propre, mais **6 verdicts catastrophiques contre 1** :
   privé de la question et de la réponse, le détecteur de conflits devient incohérent sur la
   comparaison de dates pures. Leçon : **le goulot n'est pas l'architecture du juge, c'est la
   fiabilité brute du modèle sur la récence ; plus de contexte l'aide, l'isoler le dessert.**

3. **Le « suicide du mois 3 ».** Aux paramètres par défaut (demi-vie 30 j) sur un horizon de 12 mois,
   la mémoire de C s'auto-efface : tout passe sous le seuil d'archivage dès le 3ᵉ mois. Ce n'est pas
   un bug mais une **incompatibilité de calibrage** entre la vitesse d'oubli et la durée de
   l'expérience — révélée par un test à sec (sans LLM) avant le run coûteux, puis corrigée au balayage.

---

## 7. Note méthodologique — la contamination de B par les dates

Le RAG inerte **B** s'est révélé étonnamment fort, parce que les énoncés de mise à jour contiennent
la date **dans le texte** (« *Depuis mai 2026*, le PDG est… »). Même sans métadonnées, le modèle lit
donc la récence. **B n'est donc pas un baseline réellement aveugle.** On a ajouté **B′**, identique
mais au texte débarrassé de toute date : c'est le vrai « entrepôt inerte ». **L'écart C − B′ mesure
le véritable apport des métadonnées datées.** Une condition future **B″** pourrait aussi retirer la
date des énoncés de C pour un test encore plus strict.

---

## 8. Limites connues

- **Le juge est faillible (~15 %).** Ses erreurs sont presque toutes des **fausses contradictions de
  faits actuels** (il contredit parfois le récent). Volontairement **non retouché** pendant le
  balayage, pour ne pas confondre l'effet de la demi-vie avec un changement de juge.
- **Monde synthétique.** 40 entités, 95 faits fictifs, déterministes (graine fixe). Les résultats
  valent pour ce micro-monde contrôlé, pas (encore) pour des données réelles.
- **Une seule demi-vie balayée à la fois**, et le fix verbal testé à 240 j seulement. Le réglage
  optimal (demi-vie × seuils × intensité de consultation) n'a pas été exploré exhaustivement.
- **Sous-critère stable non pleinement atteint** (C 70 % vs B 83 %) — voir §5.

---

## 9. Structure du projet

```
config.py              tous les réglages (modèles, gain/perte, demi-vie, seuils…)
modele.py              passerelle Ollama (répondre / juger, robuste aux réponses vides)
embeddings.py          vecteurs (sentence-transformers, CPU)
horloge.py             horloge virtuelle (temps simulé)
memoire_store.py       LA MÉMOIRE : Souvenir + Memoire (recherche, verdicts, érosion, sommeil)
cycle.py               prompts A/B/C + juges (V1, scindé, champion) + répondeur verbal
monde.py               génération du monde synthétique + vérité-terrain
util.py                journal (affiche + enregistre)
etape0_check.py        vérification environnement
etape1_micro.py        micro-démo du cycle
etape1c / 1d           ablation et juge scindé
etape2_experience.py   l'expérience (3 configs, métriques, rapport)
etape3_sensibilite.py  balayage demi-vie + B′ + dashboard HTML
etape3b_fix_verbal.py  le fix « confiance verbale »
logs/ , resultats/     journaux et sorties (rapports, CSV, dashboard, JSON)
```

---

---

## 10. Suite — la V2 (graphe daté, deux axes, provenance)

Une refonte du **modèle de stockage** corrige les défauts mesurés ici (suicide au mois 3, juge
fragile sur la récence, piège « ancien ≠ périmé ») : mémoire en **graphe daté**, score scindé en
**Force** (vivacité) et **Certitude** (validité), **provenance** anti-rumeur, quatre statuts
(courant / clos / disputé / dormant), et la **contradiction déplacée vers l'écriture** (ce qui
désarme le juge). Sous une métrique stricte, **C-v2 atteint 70 % sur les faits changés contre 15 %
pour le RAG inerte**. Tout est documenté dans **`README_V2.md`**.

---

*Construit pas à pas, petit d'abord. Trois échecs compris valent mieux qu'un succès non expliqué.*
