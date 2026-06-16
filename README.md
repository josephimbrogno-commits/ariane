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

## Ce qui distingue Ariane / What sets Ariane apart

- **Grammaire épistémique / Epistemic grammar** — présent / imparfait (« était… jusqu'à ») / conditionnel (« serait… à revérifier ») / « je ne sais pas ». Present / past / conditional / "I don't know."
- **Trois axes indépendants / Three independent axes** — force (vivacité), certitude (validité), importance (structure). Strength, certainty, importance.
- **Contradiction à l'écriture / Contradiction at write time** — fait contre fait, dates contre dates, sans LLM dans la boucle de décision. Fact vs fact, no model in the decision loop.
- **Règle d'or / Golden rule** — on lit la toile librement, on ne tisse jamais un fil sans dire d'où il vient. Read freely, never weave a thread without a source.

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

## Structure du dépôt / Repository layout

```
memoire/        la bibliothèque (cœur testé) / the library (tested core)
connecteur/     le connecteur OpenClaw (service + pont) / the OpenClaw connector
tests/          bancs synthétiques + tests unitaires / synthetic benchmarks + unit tests
ARTICLE_FR.md   l'article complet (français)
ARTICLE_EN.md   the full article (English)
CHANGELOG.md    journal des évolutions / changelog
```

## Journal des évolutions / Changelog

Voir [CHANGELOG.md](./CHANGELOG.md) pour la liste des évolutions, du plus récent au plus ancien.
See [CHANGELOG.md](./CHANGELOG.md) for the list of changes, newest first.

## Limites assumées / Acknowledged limits

Extraction sur langage réel : refondue en quatre axes (polarité, modalité, temporalité, rôle), 0 faux positif de polarité, greffier généraliste à ~90 % de couverture sur six domaines (banc à l'aveugle) · résolution d'entités traitée (collision par type, fragmentation par structure pondérée, acronymes courts par normalisation + malus de brièveté) · le cours continu hors périmètre · prototype-laboratoire, pas un produit.
/ Real-language extraction: rebuilt along four axes (polarity, modality, temporality, role), 0 polarity false positives, generalist extractor at ~90% coverage across six domains (blind benchmark) · entity resolution handled (collision by type, fragmentation by weighted structure, short acronyms by normalization + brevity penalty) · continuous prices out of scope · a lab prototype, not a product.

## Licence / License

MIT.

---

*Projet-laboratoire. Conçu par le raisonnement, implémenté avec l'aide d'un assistant. / A lab project. Designed by reasoning, implemented with an assistant's help. — voir le post-scriptum de l'article / see the article's postscript.*
