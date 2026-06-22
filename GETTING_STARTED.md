# Essayer Ariane / Getting started

> 🇫🇷 Un chemin reproductible pour **voir le tri** (pas le rappel — c'est là qu'Ariane se distingue),
> d'abord sur la bibliothèque seule, puis branchée sur un agent réel.
> 🇬🇧 A reproducible path to **see the sorting** (not recall — that's where Ariane stands out),
> first on the library alone, then wired into a real agent.

---

## 1. Prérequis / Prerequisites

🇫🇷
- **Python 3.10+**.
- **Ollama** en marche avec un modèle d'instruction — testé sur `qwen3:30b-a3b`. Un modèle plus petit
  fonctionne aussi (qualité d'**extraction** moindre ; le **tri**, lui, ne dépend pas du modèle).
- **Embeddings** locaux : `sentence-transformers` (modèle `paraphrase-multilingual-MiniLM-L12-v2`,
  téléchargé au premier lancement).
- **Matériel, honnêtement** : `qwen3:30b-a3b` est un MoE de 30 B — comptez un **GPU costaud
  (~24–32 Go de VRAM)** pour un débit confortable. Avec un modèle plus léger, un GPU modeste suffit.
- Dépendances Python : `pip install sentence-transformers requests` (pour la bibliothèque) ;
  ajoutez `fastapi uvicorn` pour le service du connecteur.

🇬🇧
- **Python 3.10+**.
- **Ollama** running with an instruction model — tested on `qwen3:30b-a3b`. A smaller model also works
  (lower **extraction** quality; **sorting** itself does not depend on the model).
- Local **embeddings**: `sentence-transformers` (model `paraphrase-multilingual-MiniLM-L12-v2`,
  downloaded on first run).
- **Hardware, honestly**: `qwen3:30b-a3b` is a 30B MoE — expect a **beefy GPU (~24–32 GB VRAM)** for
  comfortable throughput. With a lighter model, a modest GPU is enough.
- Python deps: `pip install sentence-transformers requests` (for the library); add `fastapi uvicorn`
  for the connector service.

---

## 2. La bibliothèque seule — voir le tri / The library alone — see the sorting

🇫🇷 L'essentiel tient en deux scénarios. Lancez Ollama, puis :
🇬🇧 The essence fits in two scenarios. Start Ollama, then:

```python
from memoire import Memoire
from memoire.adaptateurs.ollama_qwen import OllamaLLM, faire_embed

mem = Memoire(llm=OllamaLLM(modele="qwen3:30b-a3b"), embed=faire_embed())

# 1) PÉREMPTION — deux faits datés qui se succèdent / a dated succession
mem.ecrire("De 2019 à 2024, Léa Marin a dirigé Zephyr Corp.", source_id="src1")
mem.ecrire("Depuis 2024, Tom Vasseur dirige Zephyr Corp.",     source_id="src2")
print(mem.lire("Qui dirige Zephyr Corp aujourd'hui ?")["reponse"])
# → sert l'ACTUEL (Tom Vasseur) ; le fait clos (Léa Marin) n'est jamais servi comme courant.
#   serves the CURRENT one (Tom Vasseur); the closed fact (Léa Marin) is never served as current.

# 2) CONFLIT — deux sources, deux valeurs, même époque / two sources, two values, same period
mem.ecrire("Onyx Group a son siège social à Lyon.",  source_id="srcA")
mem.ecrire("Onyx Group a son siège social à Brest.", source_id="srcB")
print(mem.lire("Où se trouve le siège de Onyx Group ?")["reponse"])
# → SIGNALE le conflit (« disputé » : Lyon vs Brest) au lieu de trancher à plat.
#   FLAGS the conflict ("disputed": Lyon vs Brest) instead of resolving it flatly.
```

🇫🇷 C'est exactement là qu'Ariane se voit : pas sur *combien* de faits elle retrouve, mais sur le fait
qu'elle ne sert **jamais** le périmé et **n'invente pas** une certitude sur un conflit.
🇬🇧 This is exactly where Ariane shows: not on *how many* facts it retrieves, but on the fact that it
**never** serves the stale one and **doesn't fabricate** certainty on a conflict.

> 🇫🇷 **Rappel de portée.** Cette garantie vaut sur les faits **captés et structurés** ; un fait que
> l'extraction a **manqué** échappe au garde-fou (voir le README, « Portée du 0-CW »).
> 🇬🇧 **Scope reminder.** This guarantee holds on facts **captured and structured**; a fact the
> extraction **missed** escapes the guardrail (see the README, "Scope of 0-CW").

---

## 3. Brancher sur OpenClaw — l'usage réel / Wire it into OpenClaw — the real use

🇫🇷 C'est le mode d'emploi détaillé (service Python loopback + plugin sur le slot `contextEngine`,
en **coexistence** avec le RAG natif sur le slot `memory`) : **[connecteur/README_CONNECTEUR.md](./connecteur/README_CONNECTEUR.md)**.
En bref :
🇬🇧 The detailed wiring (loopback Python service + plugin on the `contextEngine` slot, **coexisting**
with the native RAG on the `memory` slot): **[connecteur/README_CONNECTEUR.md](./connecteur/README_CONNECTEUR.md)**.
In short:

```powershell
# 1) lancer le service (avant l'agent) / start the service (before the agent)
python -m uvicorn connecteur.service:app --host 127.0.0.1 --port 8077

# 2) installer le pont et basculer le slot / install the bridge and switch the slot
cd connecteur/openclaw-plugin
npm link openclaw
openclaw plugins install . --link
openclaw config set plugins.slots.contextEngine memoire-qui-trie
```

---

## 4. Quoi OBSERVER / What to WATCH FOR

🇫🇷 C'est **là** qu'Ariane se juge — pas sur le rappel brut :
- **Un fait qui a changé** : posez une question sur l'état actuel → l'agent sert-il **l'actuel** (et non
  le périmé) ? Sans Ariane (RAG natif seul), le même agent ressert souvent l'ancien avec aplomb.
- **Un fait disputé** : deux sources contradictoires → l'agent **signale-t-il le conflit** plutôt que de
  trancher ? (Note honnête : sur un disputé, un **répondeur faible** peut trancher quand même malgré le
  bloc injecté — c'est une limite du *modèle*, pas du tri ; détaillé dans le README du connecteur, §6.)

🇬🇧 This is **where** Ariane is judged — not on raw recall:
- **A changed fact**: ask about the current state → does the agent serve the **current** one (not the
  stale)? Without Ariane (native RAG alone), the same agent often re-serves the old one confidently.
- **A disputed fact**: two contradictory sources → does the agent **flag the conflict** rather than pick?
  (Honest note: on a disputed fact a **weak responder** may still pick one despite the injected block —
  a *model* limit, not a sorting one; detailed in the connector README, §6.)

---

## 5. Sécurité du raccord / Wiring safety

🇫🇷
- Service en **loopback** (`127.0.0.1`) — pas d'exposition réseau.
- **Aucun secret en clair** : tout est local (Ollama + embeddings locaux), aucune clé d'API cloud requise.
- **Store local** : la mémoire persiste dans un fichier local ; sauvegardez-le, ne le committez pas
  (les `*.pkl` et `connecteur/donnees/` sont déjà ignorés par git).

🇬🇧
- Service on **loopback** (`127.0.0.1`) — no network exposure.
- **No secrets in clear**: everything is local (Ollama + local embeddings), no cloud API key required.
- **Local store**: memory persists in a local file; back it up, don't commit it (`*.pkl` and
  `connecteur/donnees/` are already git-ignored).

---

*🇫🇷 Projet-laboratoire — retours et essais bienvenus. / 🇬🇧 A lab project — feedback and trials welcome.*
