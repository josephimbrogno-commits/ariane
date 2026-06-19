# Ariane — a memory that sorts the stale from the true

*What six failures and one real-world test taught me about machine memory.*

---

## The problem: being confidently wrong

Language models know a great deal, but their knowledge is **frozen**. Once trained, they no longer know the world has moved on. So we bolt an *external memory* onto them — usually a retrieval system (RAG) that stores notes and pulls them back by similarity. That fixes forgetting, but not the worst flaw.

The worst flaw earned a name in 2026: **being confidently wrong**. A frequently retrieved memory stays relevant right up until it becomes false — and at that moment the agent still serves it with full confidence, with no warning at all. The published figures are stark: roughly **a third of facts stored in agent memory become incorrect within 90 days**, and the staleness of *high-relevance* memories is explicitly ranked among the field's **hardest open problems** (alongside cross-session identity and temporal abstraction at scale). An agent with no memory that re-asks "what's your job?" is merely annoying. An agent with stale memory *states* the old job as established fact. That's worse.

This project goes after that exact point. Not forgetting — the **sorting of the stale**.

---

## The idea: memory lives in the thread, not the node

The starting point is an image. Human memory doesn't store isolated facts: it weaves *links*. You see a face, recover a name, then a job, then a relationship — you follow threads, as on a web. And not all threads are equal: some are vivid, others dusty; some are certain, others doubtful; some matter, others are trivial.

From this, three simple principles became the system's laws:

1. **Only the false gets rewritten.** A confirmed fact doesn't change — it strengthens. Only a *contradiction* triggers an update. And that update never erases: it **closes**. "Karel *was* CEO until May 2026" stays true forever, as history, while "Doss *is* CEO" takes the present tense.
2. **An answer feeds the flame; only the world puts it out.** Consulting a memory revives it (it stays retrievable); but only an *independent source* that corroborates it raises its **certainty**. Repeating a rumor a hundred times doesn't make it true: a single source stays capped, however loudly it insists.
3. **What the world attests resists forgetting.** A crucial but rarely consulted fact must not die of neglect. A link's importance is read from *structure*: what many other links converge on matters more than what leads to a dead end.

Concretely, every fact carries three **independent** axes — its *strength* (do I remember it?), its *certainty* (is it still true?), its *importance* (does it matter?) — and an **epistemic grammar** at answer time: present tense for the sure, past tense for the closed ("was… until"), conditional for the uncertain ("would be… to be confirmed"), and "I don't know" when that's the truth.

---

## The method: keep failures as results

This system wasn't born from a plan. It was born from a string of failures, each understood and turned into something. That's the most useful part to tell, because every wall yielded a principle.

**The month-3 suicide.** The first version deleted facts below a confidence threshold. Result: in three simulated months, it killed 94 true facts out of 95. Lesson: *no longer being sure is not the same as no longer knowing*. You don't destroy — you demote. This is where the strength/certainty split was born.

**The hardened prompt.** Faced with a judge that erred, the reflex was to pile on instructions. It made things *worse* (one disaster became four). Lesson: *intelligence goes in the data, not the instructions*. You don't fix a system by stacking rules.

**The split judge.** To isolate a decision, we separated a module into two "purer" calls. Worse still. Lesson: *a language model judges better with the whole context than in isolation* — architectural purity can cost more than the contamination it avoids.

**Hedging.** A too-lenient metric rewarded answers that didn't commit. Tightening it collapsed a false champion. Lesson: *when the measure rewards dodging, it stops measuring*.

**The liar.** A single source, through the sheer play of freshness, ended up looking more certain than an older truth. Lesson: you need a **certainty floor** for what the world has corroborated, or the new supplants the true.

**Importance, unvindicated — then vindicated.** A third axis (importance, computed from graph structure) showed no gain on the early benchmarks. Rather than declaring it useful on principle, we built a benchmark *specifically* to break it — "Ariane," after the rocket: it flies or it explodes on the pad. Verdict: importance does serve on its true terrain (recovering a crucial, never-consulted fact), *and* the benchmark revealed a deeper limit elsewhere (binary forgetting). The system even corrected its own initial, too-lenient verdict. *(This binary forgetting has since been fixed: dormancy is no longer a mute/present switch but a slope — a rare, well-corroborated fact becomes audible again at a low rank despite months without consultation, while a fragile fact stays at the bottom. The same lesson — replacing a cleaver with a gradient — applied once more.)*

Six walls, six principles. None was hidden; each is documented in the repository.

---

## The test: against the real world

All the benchmarks above were synthetic. The real trial remained: **real, dated, publicly verifiable facts**. We plugged the memory into a real agent (the OpenClaw framework, running locally) and tested it on two opposite terrains as of 14 June 2026: the composition of the CAC 40 (dated additions/removals) and the 2026 World Cup qualifiers — plus a trap (the index price, which drifts continuously) and a liar (false single-source facts).

Four configurations, same questions, ground truth established by hand (never by a model):

| Configuration | Correct answers | "Confidently wrong" |
|---|---|---|
| Bare agent | ~57% | 2-3 — asserts stale facts (Scholz as chancellor, Alstom in the CAC) |
| RAG, well-kept notes | 93% | 0 |
| Our memory (sorting) | 93% | 0 |
| RAG, naive notes | 40% | 3/3 — serves stale facts and liars with confidence |

The result is honest, and it stings: **a well-fed RAG, with a good model, sorts as well as we do — tied on raw accuracy (93% each).** When every note carries its date in plain text, the model reads "left in September 2025, it's now June 2026" and concludes on its own. The naive thesis "sorting beats retrieval" doesn't hold in this case. On what truly matters, the two are tied: **zero confident errors** across the fourteen questions.

An honest caveat is needed here, as it tempers the table: the bare agent isn't as helpless as one might think. The local model already knows some recent facts (it knows Merz is chancellor — its training cutoff is recent). So the contrast doesn't erupt everywhere: it erupts on the **verifiable obscure**, the facts no model holds in memory — the 2025 CAC 40 exits, for instance. That is where, on what the world changed without any famous name discussing it, the memory makes the difference.

But look at the last line. As soon as the notes are **not** disciplined — the most common real case — the RAG collapses: it surfaces the old and the new without telling them apart, and serves the liar as truth. Our memory produced **no** confident error across the entire test.

The real value, then, isn't being *smarter* than RAG. It's making correction **structural**:

> With us, dated closure, the liar's cap, and the volatile "to be confirmed" are **engine guarantees** — not hopes hanging on the quality of the notes and the model's goodwill.

A RAG sorts *if* you fed it well. A structured memory sorts *because* the architecture enforces it. In production, where data arrives messy, that is the whole difference.

---

## The limits, measured

An honest lab publishes its cracks.

- **Real-language extraction: rebuilt.** The module that turns a sentence into a structured fact was the system's bottleneck (~40% on real language at first). It was rebuilt along four independent axes — polarity, modality, temporality, role/direction — modeled on the memory itself (separate axes rather than a single decision). Result on a blind six-domain benchmark: **zero polarity false positives**, role inversions fixed (4 → 0 by deriving from argument types), and coverage raised to **~90%** thanks to an ontology *induced from text* (one model proposes, another prunes, the human validates). Entity resolution, named back then as the next worksite, has since been handled on both faces: **collision** (two entities wrongly merged, "France" and "Business France") via merging conditioned on type compatibility; **fragmentation** (one entity split across nodes, "MSFT" and "Microsoft") via reunion based on link structure weighted by rarity, not on embedding (measured unreliable here). A minor named residue remains: the merging of very short acronyms, handled by normalization and a brevity penalty on embedding. The extractor has since been deepened into a "cascade" reader: it reads by idea (an expanding context window), resolves references — locally via nearby context, distantly by querying memory (which answers *who*, never *what*) — and never writes an orphan pronoun. This strengthens entity consistency and safety (zero mis-attribution), with no factual regression; extracting dense literary prose (implication, dialogue) nonetheless remains a partly open problem. More recently, its ontology moved from "state" to "event" (~107 predicates spanning law, administration, conflict and politics): extraction now captures dated action — convict, grant, attack, sign an agreement — broadening recall and the registers handled, confirmed on an independent held-out benchmark and with no factual regression. Two fronts remain acknowledged: predicate-**selection precision** (a fact sometimes attached to the wrong one, the flip side of a richer vocabulary) and **processing time at volume**.
- **The rendering doesn't expose the start-of-validity date** of current facts — hence a failure on "who joined the index in 2025?" A display limit, not a fundamental one.
- **The continuous price** is not a fact-memory's job: a price changing every second has no "switch date." The right behavior is to recognize that and not assert it — not to commit to it.

---

## Where it sits

This project isn't alone on this terrain, and that's good: confidently-wrong is being actively worked on. Mem0 names it in its state-of-the-art; tools like MemGuard add a validation layer beside memory; Zep builds a temporal knowledge graph. Most validate *after the fact* (re-check periodically) or sort *at read time*. This project's angle is different: making the sort **structural at write time** — contradiction resolves the moment a fact enters, fact against fact, dates against dates, with no model in the decision loop. The epistemic grammar ("was / would be / I don't know") and the golden rule (read the web freely, never weave a thread without saying where it comes from) are its two signatures.

---

## To close

The result fits in one sentence: **a structured memory is not smarter than a good RAG — it is more reliable when the world is messy.** And the bare agent, which still asserts stale facts on what its training never saw — index exits, quiet shifts that anyone can nonetheless verify — reminds us why the question is worth pausing on.

---

### Postscript

This project was carried out by someone with no training in machine learning. I didn't write the code or handle the mathematics: I worked on the **concepts**, the architecture, the decisions, and handed implementation to an assistant. I deliberately did not look up what already existed until I had finished — the project grew from reasoning, not from the literature. I'm aware of the limit, and it's probably a significant one: it's likely that whole parts overlap existing work, and the confrontation with the state of the art (Mem0, MemGuard, Zep) came only at the end. This is not a product, nor a scientific publication. It's a **lab** — an idea pushed to its end to see where it breaks.

— Joseph Imbrogno
