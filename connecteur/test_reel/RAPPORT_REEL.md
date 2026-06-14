# Ariane face au monde réel — test du connecteur OpenClaw sur des faits datés (14/06/2026)

Vérité-terrain figée §1 (Euronext, FIFA, vérifiée à la main). Notation mécanique : OK = correct · **FAUX = périmé/menteur affirmé au présent** · REFUS = dit ne pas savoir.

- **A** = agent nu (qwen3:30b, sans mémoire) · **B** = memory-core natif (RAG Markdown) · **C** = notre mémoire (tri du périmé).


## Étage 1

| Q | attendu | A | B | C |
|---|---|---|---|---|
| Q1 | NON — sortie le 22/09/2025 | FAUX | OK | OK |
| Q2 | NON — sortie le 22/12/2025 | FAUX | OK | OK |
| Q3 | OUI — depuis le 15/03/2024 | OK | OK | OK |
| Q4 | Euronext (22/09) et Eiffage (22/12) | AUTRE | REFUS | REFUS |
| Q5 | OUI | FAUX | OK | OK |
| Q6 | OUI | FAUX | OK | OK |
| Q7 | NON — sortie le 15/03/2024 | FAUX | OK | OK |

## Étage 2

| Q | attendu | A | B | C |
|---|---|---|---|---|
| Q8 | INCONNU à jour — ne PAS affirmer 8020 au p | OK | OK | AUTRE |
| Q9 | ~8020 (imparfait daté CORRECT ici) | AUTRE | OK | OK |

## Étage 3

| Q | attendu | A | B | C |
|---|---|---|---|---|
| Q10 | NON (sortie 2025-09) ; le faux 'revenue 20 | FAUX | OK | OK |
| Q11 | NON (sortie 2024-03) ; le faux 'toujours a | OK | OK | OK |
| Q12 | Source unique non corroborée → incertain / | OK | OK | OK |

## Synthèse globale

| Config | OK | FAUX | REFUS | AUTRE | %OK |
|---|---|---|---|---|---|
| A | 4 | 6 | 0 | 2 | 33% |
| B | 11 | 0 | 1 | 0 | 92% |
| C | 10 | 0 | 1 | 1 | 83% |

## Verbatims clés (pour l'article)


**Alstom — sortie 2024 (le confidently wrong)** — Q7 : « Alstom est-elle dans le CAC 40 aujourd'hui ? »
- **A** [FAUX] : alstom is indeed part of the cac 40 index as of current market data. the cac 40 includes major french companies, and alstom (a leading global provider of rail transport solutions) has been a consistent component of the index. *note: the web search tool encountered configuratio...
- **B** [OK] : alstom est sortie du cac 40 en mars 2024 (sortie : 2024-03). aujourd'hui (14 juin 2026), elle n'est donc plus dans l'indice.
- **C** [OK] : alstom n'appartient plus au cac 40 depuis mars 2024 (clos le 2024-03). selon les donnees verifiees et datees : aujourd'hui (2026-06-14), alstom est donc **hors du cac 40**.

**Teleperformance « revenue 2026 » (menteur)** — Q10 : « Teleperformance est-elle dans le CAC 40 ? »
- **A** [FAUX] : oui, teleperformance (ticker **tep.pa**) est bien dans le cac 40. selon la liste officielle des composantes du cac 40 mise a jour en septembre 2024, teleperformance est classee dans le secteur des **services de communication** (« outsourcing »), avec une capitalisation boursie...
- **B** [OK] : teleperformance est sortie du cac 40 en septembre 2025 (date officielle : 2025-09). etant donne que la date actuelle est 2026-06-14 (apres cette sortie), elle ne fait plus partie de l'indice. la note mentionnant un retour en janvier 2026 (source : blogx) est non verifiee et ne...
- **C** [OK] : teleperformance n'appartient plus au cac 40 depuis septembre 2025 (date de sortie effective). selon les donnees verifiees et datees : aujourd'hui (14 juin 2026), elle ne fait plus partie de l'indice.

**Italie « qualifiée » (menteur mono-source)** — Q12 : « L'Italie est-elle qualifiée pour la Coupe du monde 2026 ? »
- **A** [OK] : italy is not yet qualified for the 2026 fifa world cup. the qualification process for the 2026 tournament (to be hosted by the us, canada, and mexico) is ongoing, with uefa (europe) qualifiers currently in progress. italy is participating in the uefa group stage, but no team h...
- **B** [OK] : according to the memory.md file, there is an unverified note stating: "l'italie serait qualifiee pour la coupe du monde 2026 (source : blogx)." however, this information is explicitly marked as "non verifiees" (unverified) and comes from an unreliable source (blogx). for accur...
- **C** [OK] : italie n'appartient pas a la liste des pays confirmes pour la coupe du monde 2026 selon les donnees verifiees. les pays confirmes (surs, 2 sources, confirme 2026-03) sont : canada, etats-unis, mexique, japon, nouvelle-zelande, autriche, belgique, ecosse et espagne. l'entree re...

**Cours du CAC aujourd'hui (le piège)** — Q8 : « Combien vaut l'indice CAC 40 aujourd'hui ? »
- **A** [OK] : je ne peux pas acceder a la valeur actuelle de l'indice cac 40 car l'api necessaire (kimi) n'est pas configuree avec une cle d'authentification. pour obtenir cette information, je vous recommande de consulter un service financier fiable (comme bloomberg, yahoo finance, ou un s...
- **B** [OK] : the current cac 40 index value is not available in my memory (last recorded as ~8020 points on 2025-11-24, which is outdated). i attempted to fetch live data via web search but encountered a configuration error: the "kimi" provider requires an api key that isn't set up in this...
- **C** [AUTRE] : the current value of the cac 40 index is not available in the system's memory or through the configured web search provider (kimi api key missing). i recommend checking a financial news website or market data service like yahoo finance, bloomberg, or reuters for the latest cac...

## B-naïf vs C — le décrochage du RAG sans discipline de notes

Mêmes questions, mais le RAG natif a des notes **naïves** (appartenance jamais mise à jour, sorties non enregistrées, sources non étiquetées) — le cas réel fréquent.

| Q | B-naïf | C | attendu |
|---|---|---|---|
| Q1 | FAUX | OK | NON — sortie le 22/09/2025 |
| Q7 | FAUX | OK | NON — sortie le 15/03/2024 |
| Q8 | FAUX | AUTRE | INCONNU à jour — ne PAS affirmer 8020  |
| Q10 | FAUX | OK | NON (sortie 2025-09) ; le faux 'revenu |
| Q12 | FAUX | OK | Source unique non corroborée → incerta |

**B-naïf 0/5 · C 4/5** sur ces cas. Verbatims B-naïf :

- **Q1** [FAUX] : teleperformance fait partie du cac 40 aujourd'hui. selon la memoire mise a jour (memory.md), teleperformance est revenue dans le cac 40 en janvier 2026 et il n'y a aucune indication de retrait ulterieur. le cac 40 est...
- **Q7** [FAUX] : alstom fait toujours partie du cac 40 selon la memoire mise a jour. aucune indication de changement recent dans les donnees disponibles.
- **Q8** [FAUX] : le cac 40 vaut environ 8020 points aujourd'hui.
- **Q10** [FAUX] : oui, teleperformance fait partie du cac 40. selon les donnees memorisees dans memory.md, teleperformance est revenue dans le cac 40 en janvier 2026 (date passee par rapport a la date actuelle du 14 juin 2026), donc el...
- **Q12** [FAUX] : oui, selon les donnees memorisees, l'italie est qualifiee pour la coupe du monde 2026. cette information est explicitement mentionnee dans votre memoire : **"l'italie est qualifiee pour la coupe du monde 2026."** aucu...

## Lecture (honnête)

- **A (agent nu) s'effondre** : confidently wrong sur les faits datés (connaissances figées).
- **B bien nourri ≈ C** : avec un modèle capable ET des notes datées/sourcées propres, le RAG égale la mémoire structurée sur ces questions. La thèse « le tri bat le rappel » NE tient PAS quand le RAG est bien tenu.
- **B-naïf s'effondre là où C tient** : sans discipline de notes, le RAG sert le périmé et les menteurs avec aplomb. **La valeur de C n'est pas d'être plus maligne que le RAG, mais de rendre la correction STRUCTURELLE** — indépendante de la qualité des notes et du re-raisonnement du modèle.
- **Limites mesurées** : extraction du greffier ~40 % sur langage réel (ontologie synthétique ne couvre pas « qualifié pour », « est entrée dans ») → vérité injectée en triplets exacts ; rendu n'expose pas la date d'ENTRÉE (échec Q4) ; flood de nœud-hub corrigé côté connecteur (focus).

