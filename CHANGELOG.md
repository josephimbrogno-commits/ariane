# Changelog — Ariane

> Journal des évolutions du projet. L'**article** raconte *pourquoi* ; ce changelog liste *quoi* et *quand*.
> Change log. The **article** tells *why*; this changelog lists *what* and *when*.
>
> Les dates de version sont celles des **commits réels** (via `git log`).
> Version dates are those of the **actual commits** (via `git log`).
> Ne lister ici que ce qui est **réellement poussé** dans le dépôt — jamais le travail en cours.
> List here only what is **actually pushed** to the repo — never work in progress.

Le format suit la convention [Keep a Changelog](https://keepachangelog.com). Versionnage indicatif (projet-laboratoire, pas de release formelle).
Format follows [Keep a Changelog](https://keepachangelog.com). Indicative versioning (a lab project, no formal releases).

---

## [Non publié] / [Unreleased]

> Travail terminé en local, pas encore poussé. / Work done locally, not yet pushed.

- *(rien pour l'instant — à remplir au prochain commit) / (nothing yet — fill at next commit)*

---

## [0.5.0] — Résolution d'entités / Entity resolution — 2026-06-16

**FR**
- Ajouté — **typage des nœuds** : le type compris par le greffier (personne, organisation, lieu fin pays/ville…) voyage désormais jusqu'au nœud au lieu d'être jeté après l'orientation.
- Ajouté — **fusion conditionnée au type** (anti-collision) : deux nœuds ne fusionnent que si leurs familles de type sont compatibles. « France » (lieu) et « Business France » (organisation) ne se confondent plus.
- Ajouté — **réunion des fragments** par structure de liens pondérée par la rareté (idf-like) : deux noms d'une même entité (ex. sigle / nom complet) se réunissent quand ils partagent un voisin *rare* ; un voisin banal (un hub partagé par beaucoup) ne déclenche rien. L'embedding s'est révélé non fiable ici (mesuré) et n'est pas utilisé comme déclencheur.
- Ajouté — **acronymes courts** : normalisation (ponctuation → égalité de texte, « U.S.A. » = « USA ») + malus de brièveté sur l'embedding (sigles différents « UE »/« ONU » séparés ; vrai doublon « États-Unis »/« USA » préservé).
- Mesuré — les trois formes de collision coupées + fragmentation réunie sans sur-réunion, aucune régression du cœur (48/48), 0 faux positif de polarité maintenu.

**EN**
- Added — **node typing**: the type understood by the extractor (person, organization, fine-grained place country/city…) now travels to the node instead of being discarded after relation orientation.
- Added — **type-conditioned merging** (anti-collision): two nodes merge only if their type families are compatible. "France" (place) and "Business France" (organization) no longer collide.
- Added — **fragment reunion** via link structure weighted by rarity (idf-like): two names of one entity (e.g. acronym / full name) reunite when they share a *rare* neighbor; a banal hub triggers nothing. Embedding proved unreliable here (measured) and is not used as a trigger.
- Added — **short acronyms**: normalization (punctuation → text equality, "U.S.A." = "USA") + brevity penalty on embedding (different acronyms "UE"/"ONU" separated; true duplicate "États-Unis"/"USA" preserved).
- Measured — all three collision forms cut + fragmentation reunited without over-merging, no core regression (48/48), 0 polarity false positives maintained.

---

## [0.4.0] — Baromètre v2 & mise à jour du dépôt / Benchmark v2 & repo update — 2026-06-15

**FR**
- Ajouté — **baromètre bout-en-bout** sur OpenClaw, 4 configurations (agent nu, RAG bien tenu, Ariane, RAG naïf), faits réels datés (CAC 40, chancelier d'Allemagne), vérité-terrain à la main.
- Résultat — Ariane 93 % / 0 *confidently-wrong*, à égalité avec un RAG bien tenu sur la justesse brute ; le RAG naïf s'effondre (40 %). Distinction : correction structurelle + tenue sur notes sales.
- Modifié — README et articles FR/EN mis à jour avec les chiffres frais (remplacement des anciens ~33/92/83) et la nuance honnête (contraste sur l'« obscur vérifiable »).

**EN**
- Added — **end-to-end benchmark** on OpenClaw, 4 configurations (bare agent, well-kept RAG, Ariane, naive RAG), real dated facts (CAC 40, German chancellor), hand-built ground truth.
- Result — Ariane 93% / 0 *confidently-wrong*, tied with a well-kept RAG on raw accuracy; naive RAG collapses (40%). Distinction: structural correction + holding on messy notes.
- Changed — README and FR/EN articles updated with fresh figures (replacing the old ~33/92/83) and the honest nuance (contrast on the "verifiable obscure").

---

## [0.3.0] — Dormance graduelle / Graduated dormancy — 2026-06-15

**FR**
- Modifié — la dormance n'est plus un interrupteur muet/présent mais une **pente** : l'entrée vectorielle inclut les faits dormants avec un malus de rang **modulé par la corroboration** (un fait rare bien attesté redevient audible en rang bas ; un fait fragile reste en bas).
- Corrige — l'« oubli binaire » révélé par un test de robustesse : un fait rare corroboré n'est plus muet après des mois sans consultation.
- Mesuré — rappel des faits anciens non-nommés amélioré, aucun bruit dormant remonté, non-régression du cœur.

**EN**
- Changed — dormancy is no longer a mute/present switch but a **slope**: vector retrieval now includes dormant facts with a rank penalty **modulated by corroboration** (a rare, well-attested fact becomes audible at low rank; a fragile fact stays at the bottom).
- Fixes — the "binary forgetting" revealed by a robustness test: a rare corroborated fact is no longer mute after months without consultation.
- Measured — recall of old un-named facts improved, no dormant noise resurfaced, core non-regression.

---

## [0.2.0] — Refonte de l'extraction / Extraction rebuild — 2026-06-15

**FR**
- Ajouté — **extraction dimensionnelle (V2)** : une phrase est résolue sur quatre axes indépendants — polarité, modalité, temporalité, rôle/direction — puis le fait, son statut et sa date sont *dérivés* (au lieu d'une décision unique). 0 faux positif de polarité sur banc à l'aveugle.
- Ajouté — **axe rôle/direction** : la direction d'une relation se dérive des types d'arguments (inversions 4 → 0).
- Ajouté — **ontologie induite des textes** (chaîne : un modèle propose, un autre retranche, l'humain valide) + **greffier généraliste** sur six domaines, couverture ~90 % (banc à l'aveugle).
- Contexte — l'extraction était le goulot du système (~40 % sur langage réel au départ) ; identifiée par diagnostic, refondue, mesurée à chaque étape.

**EN**
- Added — **dimensional extraction (V2)**: a sentence is resolved along four independent axes — polarity, modality, temporality, role/direction — then the fact, its status and date are *derived* (instead of a single decision). 0 polarity false positives on a blind benchmark.
- Added — **role/direction axis**: a relation's direction is derived from argument types (inversions 4 → 0).
- Added — **ontology induced from text** (chain: one model proposes, another prunes, the human validates) + **generalist extractor** over six domains, ~90% coverage (blind benchmark).
- Context — extraction was the system's bottleneck (~40% on real language at first); identified by diagnosis, rebuilt, measured at every step.

---

## [0.1.1] — Correction des chiffres / Figures correction — 2026-06-14

**FR**
- Corrigé — chiffres du test réel ajustés aux valeurs réellement mesurées avant publication (honnêteté avant flatterie) ; reformulation de la thèse : avantage *structurel*, pas de justesse brute.

**EN**
- Fixed — real-test figures adjusted to actually-measured values before publishing (honesty over flattery); thesis reframed: *structural* advantage, not raw accuracy.

---

## [0.1.0] — Publication initiale / Initial release — 2026-06-14

**FR**
- Première mise en ligne publique (licence MIT) : bibliothèque `memoire/` (cœur testé), connecteur OpenClaw, bancs synthétiques, articles FR/EN, README bilingue.
- Architecture — graphe daté ; trois axes indépendants (force, certitude, importance) ; grammaire épistémique (est / était / serait / je ne sais pas) ; contradiction résolue à l'écriture, sans modèle dans la boucle de décision ; provenance (anti-rumeur, plafond mono-source) ; quatre statuts, jamais de suppression.

**EN**
- First public release (MIT license): `memoire/` library (tested core), OpenClaw connector, synthetic benchmarks, FR/EN articles, bilingual README.
- Architecture — dated graph; three independent axes (strength, certainty, importance); epistemic grammar (is / was / would be / I don't know); contradiction resolved at write time, no model in the decision loop; provenance (anti-rumor, single-source cap); four statuses, never deletion.

---

*Projet-laboratoire — Joseph Imbrogno. Conçu par le raisonnement, implémenté avec l'aide d'un assistant.*
*A lab project — Joseph Imbrogno. Designed by reasoning, implemented with an assistant's help.*
