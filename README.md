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

Sur des faits réels (CAC 40, Coupe du monde 2026), branché sur un agent OpenClaw local :

| Config | Correct | Confidently wrong |
|---|---|---|
| Agent nu / Bare agent | ~33% | majoritaire / majority |
| RAG (notes propres / clean notes) | ~92% | 0 |
| Ariane | ~83% | 0 |
| RAG (notes naïves / naive notes) | 0/5 | 5/5 |

**Sur la justesse brute, un bon RAG fait jeu égal — voire un peu mieux (92 % contre 83 %) — quand ses notes sont parfaites. Ariane ne gagne pas là : elle ne se trompe jamais avec aplomb (0/12, comme le RAG propre) et tient quand les notes sont sales (le RAG naïf, lui, se trompe 5 fois sur 5).**
**On raw accuracy a good RAG ties — even edges ahead (92% vs 83%) — when its notes are perfect. Ariane doesn't win there: it is never confidently wrong (0/12, like clean RAG) and holds when notes are messy (naive RAG fails 5 out of 5).**

## Structure du dépôt / Repository layout

```
memoire/        la bibliothèque (cœur testé) / the library (tested core)
connecteur/     le connecteur OpenClaw (service + pont) / the OpenClaw connector
tests/          bancs synthétiques + tests unitaires / synthetic benchmarks + unit tests
ARTICLE_FR.md   l'article complet (français)
ARTICLE_EN.md   the full article (English)
```

## Limites assumées / Acknowledged limits

Extraction sur langage réel ~40 % · le cours continu hors périmètre · prototype-laboratoire, pas un produit. / Real-language extraction ~40% · continuous prices out of scope · a lab prototype, not a product.

## Licence / License

MIT.

---

*Projet-laboratoire. Conçu par le raisonnement, implémenté avec l'aide d'un assistant. / A lab project. Designed by reasoning, implemented with an assistant's help. — voir le post-scriptum de l'article / see the article's postscript.*
