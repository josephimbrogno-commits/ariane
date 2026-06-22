# Ariane

**Une mémoire externe qui trie le périmé pour les agents IA.**
**An external memory that sorts stale facts for AI agents.**

> *Le souvenir est dans le fil, pas dans le nœud. / Memory lives in the thread, not the node.*

---

🇫🇷 **Français**

Les modèles de langage ont un savoir figé : ils servent un fait périmé avec la même assurance qu'un fait vrai. Le domaine appelle ça *« confidently wrong »*, et c'est l'un de ses problèmes ouverts les plus durs (≈ un tiers des faits stockés deviennent faux en 90 jours).

**Ariane** est un prototype de mémoire externe qui ne se contente pas de *retrouver* (comme un RAG) mais qui **trie** : elle date chaque fait, distingue ce qui *est* de ce qui *était*, résiste aux sources uniques (anti-rumeur), et rend la correction **structurelle** plutôt qu'espérée.

➡️ **L'histoire complète, les six échecs et le test sur le monde réel : [ARTICLE_FR.md](./ARTICLE_FR.md)**

🇬🇧 **English**

Language models have frozen knowledge: they serve a stale fact with the same confidence as a true one. The field calls this *"confidently wrong"* — one of its hardest open problems (≈ one third of stored facts become incorrect within 90 days).

**Ariane** is a prototype external memory that doesn't just *retrieve* (like a RAG) but **sorts**: it dates every fact, distinguishes what *is* from what *was*, resists single sources (anti-rumor), and makes correction **structural** rather than hoped-for.

➡️ **The full story, the six failures and the real-world test: [ARTICLE_EN.md](./ARTICLE_EN.md)**

---

## Positionnement / Positioning

🇫🇷
- **Ce qu'elle fait, seule.** Une mémoire pour agents qui **trie** : sur un monde qui change, elle sert le fait **actuel** et jamais le périmé, et **signale un conflit** au lieu de trancher à plat. Démontré en conditions réelles dans un agent (slot `contextEngine` d'OpenClaw), face au RAG natif qui, lui, ressert le périmé et tranche.
- **Ce qu'elle ne fait pas.** Elle ne rivalise pas avec un RAG sur le **rappel brut** (retrouver le plus de faits possible) — et ne le cherche pas. Un bon RAG retrouve plus ; Ariane *juge mieux* ce qu'elle a.
- **Donc : un complément, pas un concurrent.** Ariane = la couche de **tri / garde-fou épistémique** (slot `contextEngine`, poussée d'office à chaque tour). Le RAG = la **récupération large** (slot `memory`). Les deux **coexistent** dans OpenClaw.

🇬🇧
- **What it does, on its own.** A memory for agents that **sorts**: in a changing world it serves the **current** fact and never the stale one, and **flags a conflict** instead of resolving it flatly. Demonstrated in real conditions inside an agent (OpenClaw's `contextEngine` slot), against the native RAG that re-serves the stale fact and picks one.
- **What it doesn't do.** It doesn't compete with a RAG on **raw recall** (retrieving as many facts as possible) — and doesn't try to. A good RAG retrieves more; Ariane *judges better* what it holds.
- **So: a complement, not a competitor.** Ariane = the **sorting / epistemic-guardrail** layer (`contextEngine` slot, pushed on every turn). The RAG = the **broad retrieval** (`memory` slot). The two **coexist** in OpenClaw.

## Ce qui distingue Ariane / What sets Ariane apart

- **Grammaire épistémique / Epistemic grammar** — présent / imparfait (« était… jusqu'à ») / conditionnel (« serait… à revérifier ») / « je ne sais pas ». Present / past / conditional / "I don't know."
- **Trois axes indépendants / Three independent axes** — force (vivacité), certitude (validité), importance (structure). Strength, certainty, importance.
- **Contradiction à l'écriture / Contradiction at write time** — fait contre fait, dates contre dates, sans LLM dans la boucle de décision. Fact vs fact, no model in the decision loop.
- **Règle d'or / Golden rule** — on lit la toile librement, on ne tisse jamais un fil sans dire d'où il vient. Read freely, never weave a thread without a source.
- **L'œuvre est en aval / The work is downstream** — la valeur propre est le **tri** (les axes, la grammaire épistémique, la corroboration, l'abstention) ; l'extraction est un **composant** qu'on branche, améliore ou remplace, pas l'état de l'art qu'on réinvente. The value is the **sorting** (axes, epistemic grammar, corroboration, abstention); extraction is a **component** to plug in, improve or swap — not the state of the art to reinvent.

## Résultat clé / Key result

Sur des faits réels datés et vérifiables (composition du CAC 40, chancelier d'Allemagne), branché sur un agent OpenClaw local :

| Config | Correct | Confidently wrong |
|---|---|---|
| Agent nu / Bare agent | ~57% | 2-3 (faits périmés) |
| RAG (notes propres / clean notes) | 93% | 0 |
| Ariane | 93% | 0 |
| RAG (notes naïves / naive notes) | 40% | 3/3 (périssables) |

**Sur la justesse brute, un bon RAG fait jeu égal avec Ariane (93 % chacun). Ariane ne gagne pas là : elle ne se trompe jamais avec aplomb (0 sur 14, comme le RAG propre) et tient quand les notes sont sales (le RAG naïf s'effondre à 40 % et sert le périmé avec assurance). Le contraste éclate surtout sur l'obscur vérifiable — les sorties du CAC 2025 qu'aucun modèle ne connaît — pas sur les faits récents notoires.**
**On raw accuracy a good RAG ties Ariane (93% each). Ariane doesn't win there: it is never confidently wrong (0 of 14, like clean RAG) and holds when notes are messy (naive RAG collapses to 40% and serves stale facts with confidence). The contrast is sharpest on the verifiable obscure — the 2025 CAC exits no model knows — not on well-known recent facts.**

> **🇫🇷 Portée exacte du « 0 confidently-wrong ».** La garantie vaut sur les faits qu'Ariane a **captés et structurés** : sur ce périmètre, elle ne sert jamais un fait périmé ni ne tranche un conflit à plat — c'est **garanti par construction** (le tri se fait à l'écriture, pas à la lecture). Un fait qu'elle a **manqué** échappe en revanche à ce garde-fou : l'agent retombe alors sur ses propres biais ou le web. Le 0-CW est donc une garantie sur le **périmètre acquis**, pas une immunité globale — et **étendre ce périmètre (l'extraction) est le chantier ouvert n°1**.
>
> **🇬🇧 Exact scope of "0 confidently-wrong."** The guarantee holds on the facts Ariane **captured and structured**: on that perimeter it never serves a stale fact nor resolves a conflict flatly — **guaranteed by construction** (sorting happens at write time, not read time). A fact it **missed** escapes the guardrail: the agent then falls back on its own biases or the web. So 0-CW is a guarantee on the **acquired perimeter**, not a blanket immunity — and **extending that perimeter (extraction) is open worksite #1**.

> **🇫🇷 Banc public à venir.** Les chiffres ci-dessus viennent de bancs internes. Un **banc reproductible** (faits Wikidata publics, juge mécanique) est le prochain livrable, pour que ces résultats soient **vérifiables par un tiers**.
> **🇬🇧 Public benchmark coming.** The figures above come from internal benchmarks. A **reproducible benchmark** (public Wikidata facts, mechanical judge) is the next deliverable, so these results become **third-party verifiable**.

## Structure du dépôt / Repository layout

```
memoire/        la bibliothèque (cœur testé) / the library (tested core)
connecteur/     le connecteur OpenClaw (service + pont) / the OpenClaw connector
tests/          bancs synthétiques + tests unitaires / synthetic benchmarks + unit tests
ARTICLE_FR.md   l'article complet (français)
ARTICLE_EN.md   the full article (English)
CHANGELOG.md    journal des évolutions / changelog
```

## Essayer Ariane / Try it

🇫🇷 Un chemin guidé pour **installer**, **voir le tri** sur la bibliothèque seule (deux faits datés contradictoires → Ariane sert l'actuel ; un conflit → « disputé »), puis la **brancher sur un agent OpenClaw** et **savoir quoi observer** : **[GETTING_STARTED.md](./GETTING_STARTED.md)**. Détails du raccordement OpenClaw : [connecteur/README_CONNECTEUR.md](./connecteur/README_CONNECTEUR.md).

🇬🇧 A guided path to **install**, **see the sorting** on the library alone (two contradictory dated facts → Ariane serves the current one; a conflict → "disputed"), then **wire it into an OpenClaw agent** and **know what to watch for**: **[GETTING_STARTED.md](./GETTING_STARTED.md)**. OpenClaw wiring details: [connecteur/README_CONNECTEUR.md](./connecteur/README_CONNECTEUR.md).

## Journal des évolutions / Changelog

Voir [CHANGELOG.md](./CHANGELOG.md) pour la liste des évolutions, du plus récent au plus ancien.
See [CHANGELOG.md](./CHANGELOG.md) for the list of changes, newest first.

## Limites assumées / Acknowledged limits

Extraction sur langage réel : greffier refondu en quatre axes (polarité, modalité, temporalité, rôle) puis approfondi en lecture « en cascade » (lecture par idée à fenêtre variable, coréférence locale et distante, aucun pronom orphelin), avec une ontologie passée de l'« état » à l'« événement » (~107 prédicats : direction, mais aussi droit, administration, conflit, politique) — 0 faux positif de polarité, ~90 % de couverture sur six domaines (banc à l'aveugle) · résolution d'entités traitée (collision par type, fragmentation par structure pondérée modulée par le type d'identité, acronymes courts, homonymes par marqueur générationnel) · rappel renforcé (reconnaissance souple à la lecture, complétude d'extraction sur phrase dense, reroutage de date vers le bon prédicat) · fronts ouverts assumés : la précision de sélection du prédicat (un fait parfois mal rattaché), le temps de traitement au volume, et — encore ouverts — les dates d'œuvres parfois non extraites et la nationalité (gentilé vs pays) · l'extraction de prose littéraire dense et les faits purement implicites restent des bornes du modèle · le cours continu hors périmètre · prototype-laboratoire, pas un produit.
/ Real-language extraction: extractor rebuilt along four axes (polarity, modality, temporality, role) then deepened into a "cascade" reader (reading by idea with a variable window, local and distant coreference, no orphan pronoun), with an ontology moved from "state" to "event" (~107 predicates: direction, but also law, administration, conflict, politics) — 0 polarity false positives, ~90% coverage across six domains (blind benchmark) · entity resolution handled (collision by type, fragmentation by weighted structure modulated by identity type, short acronyms, homonyms via generational marker) · recall strengthened (lenient entity recognition at read time, dense-sentence extraction completeness, date rerouting to the proper predicate) · acknowledged open fronts: predicate-selection precision (a fact sometimes mis-attached), processing time at volume, and — still open — work release dates sometimes unextracted and nationality (demonym vs country) · dense literary-prose extraction and purely implicit facts remain model limits · continuous prices out of scope · a lab prototype, not a product.

## Licence / License

MIT.

---

*Projet-laboratoire. Conçu par le raisonnement, implémenté avec l'aide d'un assistant. / A lab project. Designed by reasoning, implemented with an assistant's help. — voir le post-scriptum de l'article / see the article's postscript.*
