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

## [0.12.0] — Noyau : inférence & promotion (mécanismes, inactifs par défaut) / Core: inference & promotion (off by default) — 2026-06-29

**FR**
- Ajouté — **index par entité** : accès direct aux faits d'une entité (au lieu d'un parcours complet). Accélère fortement les opérations centrées entité. Sous interrupteur, inerte par défaut.
- Ajouté — **inférence typée** (première brique du « raisonnement ») : la mémoire peut composer des faits reliés pour en déduire un nouveau, MAIS uniquement selon une grammaire de compositions légitimes par type, et le fait déduit est TOUJOURS marqué « inféré » (jamais affirmé comme observé). Sur banc de composition : aucune inférence fausse, rappel complet.
- Ajouté — **promotion rétroactive** : un fait dormant (non encore jugé pertinent) peut être promu vers la mémoire active quand un fait nouveau lui donne du sens ; il rentre marqué « promu » et passe les mêmes garde-fous qu'un fait neuf.
- Inactif par défaut — mécanismes en place et sûrs ; la garantie épistémique (servir l'actuel, signaler le conflit, ne rien affirmer d'inféré comme observé) est préservée. Activation au cas par cas.
- Mesuré — non-régression complète ; garantie de tri inchangée, interrupteurs ON ou OFF.

**EN**
- Added — **per-entity index**: direct access to an entity's facts (instead of a full scan). Greatly speeds up entity-centered operations. Switch-gated, inert by default.
- Added — **typed inference** (first "reasoning" brick): memory can compose linked facts to derive a new one, BUT only along a grammar of type-legitimate compositions, and the derived fact is ALWAYS marked "inferred" (never asserted as observed). On a composition benchmark: zero false inference, full recall.
- Added — **retroactive promotion**: a dormant fact (not yet deemed relevant) can be promoted to active memory when a new fact gives it meaning; it enters marked "promoted" and passes the same guardrails as a fresh fact.
- Off by default — mechanisms in place and safe; the epistemic guarantee (serve the current, flag conflicts, never assert inferred as observed) is preserved. Case-by-case activation.
- Measured — full non-regression; sorting guarantee unchanged whether switches are on or off.

---

## [0.11.0] — Documentation : positionnement, portée du 0-CW, guide testeurs / Documentation: positioning, 0-CW scope, testers' guide — 2026-06-22

**FR**
- Clarifié — **positionnement honnête** : Ariane est un **complément** d'un RAG, pas un concurrent. Sa valeur propre est le **tri / garde-fou épistémique** (slot `contextEngine`, poussé d'office) ; le RAG reste la **récupération large** (slot `memory`), et les deux coexistent. Elle ne rivalise pas sur le **rappel brut** et ne le cherche pas. Tri **démontré en conditions réelles** dans un agent OpenClaw (sert l'actuel, signale le conflit là où le RAG natif ressert le périmé et tranche à plat).
- Précisé — **portée du « 0 confidently-wrong »** : garantie sur le **périmètre acquis** (les faits captés et structurés), **pas** une immunité globale ; un fait manqué par l'extraction échappe au garde-fou. Étendre la couverture (l'extraction) reste le **chantier ouvert n°1**. Nuance ajoutée au README et aux articles FR/EN.
- Ajouté — **guide testeurs** (`GETTING_STARTED.md`) : prérequis (matériel réaliste annoncé), exemple minimal qui **montre le tri** sur la bibliothèque seule (péremption + conflit), raccordement OpenClaw, **quoi observer**, sécurité du raccord (loopback, aucun secret en clair, store local).
- Annoncé — **banc public reproductible** (faits Wikidata publics, juge mécanique) comme prochain livrable, pour des chiffres **vérifiables par un tiers**. Aucun chiffre de banc privé publié en attendant.
- Documentation seule — **aucun changement de code**.

**EN**
- Clarified — **honest positioning**: Ariane is a **complement** to a RAG, not a competitor. Its own value is **sorting / epistemic guardrail** (`contextEngine` slot, pushed by default); the RAG remains **broad retrieval** (`memory` slot), and the two coexist. It doesn't compete on **raw recall** and doesn't try to. Sorting **demonstrated in real conditions** inside an OpenClaw agent (serves the current fact, flags the conflict where the native RAG re-serves the stale and picks one flatly).
- Specified — **scope of "0 confidently-wrong"**: a guarantee on the **acquired perimeter** (facts captured and structured), **not** a blanket immunity; a fact missed by extraction escapes the guardrail. Extending coverage (extraction) remains **open worksite #1**. Nuance added to the README and the FR/EN articles.
- Added — **testers' guide** (`GETTING_STARTED.md`): prerequisites (realistic hardware stated), a minimal example that **shows the sorting** on the library alone (perishability + conflict), OpenClaw wiring, **what to watch for**, wiring safety (loopback, no secrets in clear, local store).
- Announced — **reproducible public benchmark** (public Wikidata facts, mechanical judge) as the next deliverable, for **third-party verifiable** figures. No private benchmark figure published in the meantime.
- Documentation only — **no code change**.

---

## [0.10.0] — Subconscient : volatilité apprise (mécanisme, inactif par défaut) / Learned volatility (mechanism, off by default) — 2026-06-22

**FR**
- Ajouté — **volatilité apprise** (premier étage d'une couche « subconsciente ») : la mémoire peut estimer la vitesse de péremption d'un type de fait à partir de ses propres clôtures datées observées, au lieu d'une étiquette fixée à la main. L'estimation PART du réglage à la main et le corrige à mesure que les observations s'accumulent, en restant sur le réglage à la main tant que les observations sont trop rares (« supposition » vs « appris »). N'ajuste qu'un paramètre dérivé (la vitesse de décroissance de certitude) — **aucun fait n'est modifié**. Inspectable.
- **Inactif par défaut** — raison assumée : la mesure actuelle (part des faits clos) confond une « longue histoire » avec une « forte volatilité » et n'est pas normalisée par le temps ; sur des historiques profonds elle sur-estime la volatilité. Le mécanisme est en place et sûr (la péremption — servir l'actuel, jamais le périmé — est strictement inchangée), mais l'activation attend une mesure en **changements par unité de temps**.
- Mesuré — péremption strictement préservée (mécanisme actif ou non) ; non-régression complète.

**EN**
- Added — **learned volatility** (first stage of a "subconscious" layer): memory can estimate how fast a fact type goes stale from its own observed dated closures, instead of a hand-set label. The estimate STARTS from the hand setting and corrects it as observations accumulate, staying on the hand setting while observations are too sparse ("assumption" vs "learned"). Adjusts only a derived parameter (certainty decay speed) — **no fact is modified**. Inspectable.
- **Off by default** — acknowledged reason: the current measure (share of closed facts) conflates "long history" with "high volatility" and is not time-normalized; on deep histories it overestimates volatility. The mechanism is in place and safe (perishability — serve the current, never the stale — is strictly unchanged), but activation awaits a measure in **changes per unit of time**.
- Measured — perishability strictly preserved (mechanism on or off); full non-regression.

---

## [0.9.0] — Rappel : lecture & extraction / Recall: reading & extraction — 2026-06-21

**FR**
- Ajouté — **reconnaissance souple** : une entité nommée est retrouvée même quand son libellé stocké porte des éléments supplémentaires (prénoms composés, parenthèses, scripts non-latins), en exigeant le premier et le dernier élément du nom (anti-homonyme). Améliore le rappel à la lecture, sans toucher au tri ni introduire d'affirmation erronée.
- Ajouté — **complétude d'extraction sur phrase dense** : revue systématique des informations d'une phrase riche pour ne pas en perdre (« né le X à Y » conserve la date ET le lieu). N'ajoute que des faits fidèles.
- Ajouté — **reroutage de date** : une date attribuée par erreur à un prédicat d'action (fonder, publier, créer) est réorientée vers le prédicat de date adéquat. Correction structurelle, sûre en précision.
- Mesuré — rappel amélioré sur banc indépendant ; **0 confidently-wrong préservé sur les contradictions** (l'atout épistémique du système) ; non-régression factuelle. Restent ouverts : dates d'œuvres parfois non extraites, nationalité (gentilé vs pays).

**EN**
- Added — **lenient entity recognition**: a named entity is matched even when its stored label carries extra tokens (compound first names, parentheses, non-Latin scripts), by requiring the first and last name token (anti-homonym). Improves reading recall, without touching sorting or introducing wrong assertions.
- Added — **dense-sentence extraction completeness**: systematic review of a rich sentence so no fact is dropped ("born on X in Y" keeps both date AND place). Only faithful facts added.
- Added — **date rerouting**: a date wrongly attached to an action predicate (found, publish, create) is rerouted to the proper date predicate. Structural, precision-safe fix.
- Measured — improved recall on an independent benchmark; **0 confidently-wrong preserved on contradictions** (the system's epistemic edge); no factual regression. Still open: work release dates sometimes unextracted, nationality (demonym vs country).

---

## [0.8.0] — Abstention de prédicat & ingestion parallèle / Predicate abstention & parallel ingestion — 2026-06-20

**FR**
- Ajouté — **abstention de prédicat** : un verbe sans équivalent dans l'ontologie est conservé tel quel (verbe brut) plutôt que forcé dans une case inadéquate. Évite les relations absurdes (forcer une mauvaise « case » produisait des faits incohérents) ; le fait entre **faible, mono-source**, et c'est le **tri en aval** qui en décide — pas un filtre amont. Tous les garde-fous amont sont conservés (pas de pronom orphelin, coréférence, polarité). Sous interrupteur (défaut inactif au commit ; activé juste après, voir version suivante).
- Ajouté — **ingestion parallèle en lot** (`ecrire_lot`) pour les flux denses : l'extraction (le coût dominant) est parallélisée entre phrases, les écritures restent séquencées dans l'ordre. **Résultat identique** au séquentiel (prouvé par rejeu), seul le temps change. Sous interrupteur (défaut inactif).
- Mesuré — **rappel préservé** sur un banc indépendant, **0 confidently-wrong**, extraction factuelle non régressée. Le résidu nommé (le modèle choisit parfois une mauvaise relation avec aplomb) reste une borne du modèle.

**EN**
- Added — **predicate abstention**: a verb with no equivalent in the ontology is kept as-is (raw verb) instead of being forced into an unsuitable slot. Avoids absurd relations (forcing a wrong "slot" produced incoherent facts); the fact enters **weak, single-source**, and **downstream sorting** decides — not an upstream filter. All upstream guardrails preserved (no orphan pronoun, coreference, polarity). Behind a switch (inactive at this commit; enabled right after, see next version).
- Added — **batch parallel ingestion** (`ecrire_lot`) for dense streams: extraction (the dominant cost) is parallelized across sentences, writes stay ordered. **Identical result** to sequential (proven by replay), only timing changes. Behind a switch (inactive by default).
- Measured — **recall preserved** on an independent benchmark, **0 confidently-wrong**, factual extraction not regressed. The named residue (the model sometimes confidently picks a wrong relation) remains a model limit.

---

## [0.7.0] — Canonisation des prédicats, multi-triplets & ontologie événementielle / Predicate canonicalization, multi-triplets & event ontology — 2026-06-19

**FR**
- Ajouté — **canonisation de prédicats** : des formes de surface synonymes d'une **même** relation → un prédicat canonique (table curée, jamais d'embedding ; la direction est rétablie ensuite par l'axe rôle), pour que la corroboration s'accumule et que les conflits s'enregistrent. Précision d'abord : les relations de **nature différente** restent distinctes (dans le doute → distinct).
- Ajouté — **multi-triplets** : plusieurs faits extraits d'un énoncé dense (« né en 1973 à Toulouse, joueur de rugby » → date + lieu + profession), chacun passant par la **même** finalisation que le single (mêmes planchers 0 faux positif, anti-pronom, coréférence). Interrupteur de rollback (`OPT_MULTI_TRIPLETS`).
- Ajouté — **nationalité** : un adjectif de nationalité attaché à une personne devient un fait **séparé** (`a_nationalite`) au lieu d'être fondu dans la profession.
- Ajouté — **désambiguïsation d'homonymes** : marqueur générationnel (III ≠ Jr ≠ Sr), conservation de l'initiale médiane (« William M. Calder » ≠ « William Calder »), rejet des faits auto-référentiels (X relation X). Limite nommée : la parenté grand-père/petit-fils homonyme n'est pas résoluble par le nom seul.
- Ajouté — **ontologie événementielle** : 86 → 107 prédicats (droit/justice, administration, lieux/quantités, conflit, politique, média). L'extraction passe de l'« état » à l'« événement » (condamne, accorde, autorise, attaque, occupe, signe un accord…).
- Mesuré — confirmé sur un **banc caché indépendant** (loop-blind) : rappel élargi et nouveaux registres couverts, 0 *confidently-wrong*, 0 sur-fusion, extraction factuelle non régressée (0 faux positif de polarité), déterministe inchangé. Fronts ouverts nommés : **précision de sélection** du prédicat (mis-picks) et **temps de traitement au volume**.

**EN**
- Added — **predicate canonicalization**: synonymous surface forms of the **same** relation → one canonical predicate (curated table, never embeddings; direction is then restored by the role axis), so corroboration accumulates and conflicts register. Precision first: relations of a **different nature** stay distinct (when in doubt → distinct).
- Added — **multi-triplet** extraction from a dense statement ("born in 1973 in Toulouse, a rugby player" → date + place + profession), each fact passing through the **same** finalization as the single path (same 0-false-positive floors, anti-pronoun, coreference). Rollback switch (`OPT_MULTI_TRIPLETS`).
- Added — **nationality**: a nationality adjective attached to a person becomes a **separate** fact (`a_nationalite`) instead of being fused into the profession.
- Added — **homonym disambiguation**: generational marker (III ≠ Jr ≠ Sr), middle-initial preservation ("William M. Calder" ≠ "William Calder"), rejection of self-referential facts (X relation X). Named limit: homonymous grandfather/grandson kinship is not resolvable by name alone.
- Added — **event ontology**: 86 → 107 predicates (law/justice, administration, places/quantities, conflict, politics, media). Extraction moves from "state" to "event" (convicts, grants, authorizes, attacks, occupies, signs an agreement…).
- Measured — confirmed on an **independent held-out benchmark** (loop-blind): broader recall and new registers covered, 0 *confidently-wrong*, 0 over-merge, factual extraction not regressed (0 polarity false positives), deterministic tests unchanged. Open fronts named: predicate **selection precision** (mis-picks) and **processing time at volume**.

---

## [0.6.0] — Greffier en cascade & réunion par type d'identité / Cascade reader & identity-type reunion — 2026-06-17

**FR**
- Ajouté — **greffier en cascade** : l'extraction ne lit plus phrase par phrase mais par IDÉE — une fenêtre de contexte qui s'élargit jusqu'à ce que l'idée soit complète (sujet nommé, référence résolue).
- Ajouté — **coréférence locale** : un pronom (« il ») est rattaché à son antécédent nommé proche avant l'écriture.
- Ajouté — **résolution distante par la mémoire** : une référence non résolue localement (« M. Vasseur » → Pierre) est rattachée à une entité connue en interrogeant la toile. Garde-fou : la mémoire répond *qui*, jamais *quoi* (le contenu vient toujours du texte ; droit de douter de la toile).
- Ajouté — **propreté à la source** : un pronom non résolu ne devient jamais un nœud (abstention plutôt que nœud-poubelle).
- Modifié — **réunion d'entités modulée par le type d'identité** : barre de confirmation haute pour les personnes (≥2 voisins rares ; un seul voisin commun = coïncidence, pas identité), inchangée pour les organisations (identité relationnelle). Corrige les sur-fusions de personnes.
- Mesuré — 0 mauvaise attribution, 0 boucle d'auto-renforcement, extraction factuelle non régressée (0 faux positif de polarité). Résidus nommés : nœuds-descriptions, résolution relationnelle (« papa » → père).

**EN**
- Added — **cascade reader**: extraction no longer reads sentence by sentence but by IDEA — a context window that expands until the idea is complete (subject named, reference resolved).
- Added — **local coreference**: a pronoun ("he") is attached to its nearby named antecedent before writing.
- Added — **distant resolution via memory**: a reference unresolved locally ("Mr. Vasseur" → Pierre) is attached to a known entity by querying the web. Guardrail: memory answers *who*, never *what* (content always comes from the text; right to doubt the web).
- Added — **cleanliness at the source**: an unresolved pronoun never becomes a node (abstention rather than a junk node).
- Changed — **entity reunion modulated by identity type**: high confirmation bar for persons (≥2 rare shared neighbors; a single shared neighbor = coincidence, not identity), unchanged for organizations (relational identity). Fixes person over-merges.
- Measured — 0 mis-attribution, 0 self-reinforcing loop, factual extraction not regressed (0 polarity false positives). Named residues: description-nodes, relational resolution ("dad" → father).

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
