# Connecteur OpenClaw — brancher « la mémoire qui trie » comme moteur de contexte

Ce connecteur branche la bibliothèque [`memoire/`](../README.md) (le moteur de **tri du périmé** :
dates, clôture, provenance, grammaire épistémique) sur **[OpenClaw](https://docs.openclaw.ai)**, un
assistant IA multi-canal local-first (Node.js/TypeScript). Il ne réécrit rien de la bibliothèque
testée : il l'expose en service et la branche par un petit pont.

> **L'idée en une phrase.** OpenClaw a déjà une mémoire de **rappel** (memory-core : du RAG sur des
> notes Markdown, qui *retrouve* ce qui a été dit). Il lui manquait une mémoire de **tri** : qui
> *date*, qui *clôt* l'ancien sans le détruire, qui tranche le présent du passé. C'est ce qu'on
> ajoute — **à côté** du rappel, pas à sa place.

---

## 1. Installation

Trois pré-requis, dans l'ordre. Tout est **local** ; aucune clé d'API cloud.

### Node.js ≥ 22.19
OpenClaw l'exige. Vérifier `node --version`. Si trop ancien (le poste était en v18) :
```powershell
winget install OpenJS.NodeJS.22      # → v22.22.3 ; rien d'autre ne dépendait de Node 18 (juste pnpm, compatible)
```

### OpenClaw
```powershell
npm install -g openclaw               # → openclaw 2026.6.6
openclaw setup --non-interactive --accept-risk   # crée ~/.openclaw/openclaw.json + workspace
```

### Brancher l'Ollama **déjà présent** (ne rien réinstaller)
Le poste a déjà Ollama + qwen + les embeddings (utilisés par la bibliothèque). On pointe OpenClaw
dessus, sans `/v1` (sinon le *tool calling* casse) :
```powershell
# models.providers.ollama = { baseUrl: "http://127.0.0.1:11434", apiKey: "ollama-local", api: "ollama" }
openclaw config patch --file ./ollama.patch.json5
openclaw models set "ollama/qwen3:30b-a3b"
```
Point de contrôle : `openclaw agent --local --session-key agent:main:test --message "Bonjour"` doit
répondre via qwen, **100 % local**.

---

## 2. Architecture — Voie A : service Python + pont TypeScript

La bibliothèque est en **Python** ; OpenClaw est en **TypeScript**. Plutôt que de réécrire le cœur
(et perdre ses 48 verdicts de non-régression), on garde le code Python prouvé et on le branche :

```
   OpenClaw (agent, qwen local)
        │
        │  ContextEngine plugin (TypeScript/JS)   ← connecteur/openclaw-plugin/
        │     assemble() ──HTTP──► POST /contexte   (LECTURE : le bloc épistémique)
        │     afterTurn() ─HTTP──► POST /ecrire     (ÉCRITURE : le fait du tour)
        ▼
   Service FastAPI (Python)                        ← connecteur/service.py
        │     importe memoire/ tel quel, Memoire(llm, embed) avec l'adaptateur Ollama
        ▼
   memoire/  (le cœur testé, intact) + persistance disque (pickle)
```

### Le slot `contextEngine`, en coexistence avec `memory-core`
La vraie interface d'OpenClaw (vérifiée dans le code installé, pas seulement la doc) distingue
**deux slots** :

- `plugins.slots.memory` — la mémoire de **rappel** (memory-core : `memory_search`/`memory_get`,
  héberge le *dreaming*). **Slot exclusif** : le remplacer détruirait le dreaming.
- `plugins.slots.contextEngine` — ce qui **contrôle ce que le modèle voit** avant de répondre.

On prend le slot **`contextEngine`** et on **laisse memory-core sur le slot memory**. Notre tri se
greffe à côté du rappel ; rien n'est cassé. C'est la stratégie d'autres acteurs tiers (Lossless
Claw, Mem0). L'interface réelle, confirmée sur `openclaw/plugin-sdk` :

```ts
api.registerContextEngine("memoire-qui-trie", () => ({
  info:     { id, name, ownsCompaction: false },         // false → on délègue la compaction à OpenClaw
  assemble: async ({ messages, prompt }) => ({ messages, estimatedTokens, systemPromptAddition }),
  ingest:   async () => ({ ingested: false }),            // no-op : l'écriture passe par afterTurn
  afterTurn:async ({ messages, sessionKey }) => { /* … */ },
  compact:  async () => ({ ok: true, compacted: false }), // délégué
}));
```

> **Correction au brief de départ.** La doc publique disait « se brancher sur le slot *memory*, et
> `assemble()` reçoit le prompt ». Le code réel dit : le bon slot est **`contextEngine`** ; `assemble`
> reçoit `messages` **et** un `prompt?` optionnel. On a suivi le code, pas le résumé.

### Installer le pont
Le plugin est en JS pur (pas de build). On lie l'install globale d'OpenClaw pour résoudre le SDK,
puis on installe en **lien** (pas copie) et on bascule le slot :
```powershell
cd connecteur/openclaw-plugin
npm link openclaw                                          # résout openclaw/plugin-sdk sans re-télécharger
openclaw plugins install . --link                          # PAS --force avec --link
openclaw config set plugins.slots.contextEngine memoire-qui-trie
```
Lancer le service avant l'agent :
```powershell
python -m uvicorn connecteur.service:app --host 127.0.0.1 --port 8077
```

---

## 3. Le tri fait / texte à la porte d'entrée (décision Hobb)

Tout ce qui entre ne va **pas** dans la mémoire structurée. Le pont aiguille (`classer()` dans
`index.js`) **avant** d'écrire :

| Entrée | Va vers | Pourquoi |
|---|---|---|
| **Fait du monde, susceptible de changer** (« X dirige Y », un prix, une préférence) | **notre mémoire** (`/ecrire`) | c'est ce qui date et périme — notre raison d'être |
| **Texte long figé** (un chapitre, un récit — « ingère toute la série de Hobb ») | **RAG natif** (memory-core) | notre greffier s'étoufferait sur du récit ; la résolution d'entités exploserait |
| **Question** (`… ?`) | **rien** | une question n'est pas un fait à stocker |

Heuristique de départ, volontairement simple : longueur > 600 caractères → « texte » ; finit par
`?` → « ignorer » ; sinon → « fait ». À raffiner (cf. limites).

---

## 4. La correspondance des gestes

| Moment OpenClaw | Geste mémoire | Détail |
|---|---|---|
| **`assemble()`** — avant que le modèle réponde | **`POST /contexte`** | extrait la dernière question (le `prompt`), récupère les faits et renvoie le **bloc épistémique VERBAL** (`systemPromptAddition`). **Jamais de score numérique** — uniquement présent / « était… jusqu'à » / « à revérifier » / disputé. Récupération **sans LLM** (embedding + marche de graphe) → rapide. |
| **`afterTurn()`** — après le tour | **`POST /ecrire`** | trie le dernier message (décision Hobb), et s'il s'agit d'un fait, l'écrit avec **`source_id` = l'identité de session** (provenance). |
| *promotion / dreaming* natifs | `/consolider` | laissés au cycle d'OpenClaw ; on ne réinvente pas de planificateur. |

La **règle d'or** (« on lit la toile librement ; on ne tisse jamais un fil sans source ») vit dans le
service, pas dans le pont : `/lier` ou `/retoucher` sans source renvoient **HTTP 422**. Elle tient
donc à travers le réseau.

---

## 5. Résultats des tests d'intégration (le vrai juge)

Banc : qwen3:30b-a3b local, plugin branché, service en marche.

### Les deux preuves centrales

**A/B contre memory-core.** Même question (« qui dirige Nexora ? ») sur le **même fait qui a
changé** (Karel → Doss), en basculant le slot `contextEngine` :

| Moteur de contexte | Réponse de l'agent |
|---|---|
| `legacy` (natif seul, RAG `MEMORY.md`) | **« Mme Karel »** ❌ — le fait périmé, servi avec aplomb |
| **le nôtre** | **« M. Doss — à revérifier »** ✅ — le fait à jour, daté, trié |

C'est le problème ouvert du domaine en une image : le moteur de *rappel* ressort l'ancien avec
assurance (« confidently wrong ») ; le moteur de *tri* sert le frais.

**Divergence — quand rappel et tri se contredisent, le tri gagne.** On a fait diverger
explicitement les deux mémoires : une note **périmée** dans le RAG natif (`MEMORY.md` : « le PDG est
Mme Karel »), le fait **à jour** dans la nôtre (Doss courant, Karel clos). Question en session
neuve :

> *« Le PDG actuel de Nexora est M. Doss — à revérifier (dernière confirmation : mai 2026). »*

L'agent **n'a pas cru la note périmée**. La victoire est devenue nette après avoir présenté notre
bloc comme **« Mémoire VÉRIFIÉE ET DATÉE — fait autorité sur la fraîcheur »** — sans pour autant
surévaluer la certitude (le « à revérifier » du mono-source est resté).

### Les autres tests

| Test | Résultat |
|---|---|
| **Tri Hobb** | 620 caractères de fiction → classés « texte » → **non écrits** ; la base de faits reste propre. |
| **Plafond menteur via l'agent** | 2 sessions = 2 sources (Lyon vs Brest) → les deux faits `disputé`, plafonnés (C=0.55). La provenance tient à travers l'agent. |
| **Latence `assemble()`** | **médiane 16 ms** (récupération sans LLM). |
| **Aller-retour complet** | un fait dit en conversation → écrit (`afterTurn`) → trié (clôture) → ressorti **au bon temps** au tour suivant, y compris en **session neuve sans historique** (donc venant uniquement de la mémoire injectée). |

---

## 6. Limites connues (ce sont des résultats, pas des angles morts)

**La dilution du « disputé » dans le gros prompt système.** C'est la limite la plus instructive.
Quand deux sources se contredisent, la mémoire fait son travail : `/contexte` injecte bien
`[DISPUTÉ — non tranché] Lyon VS Brest`. Mais dans l'agent, qwen **tranche quand même** (« Brest »)
au lieu de citer les deux. Diagnostic : le **même** qwen, interrogé via notre `/lire` (prompt
épistémique focalisé), cite correctement *« disputé entre Lyon et Brest »*. La cause n'est donc ni la
mémoire ni le modèle, mais la **dilution de notre instruction** dans le grand prompt système
d'OpenClaw (AGENTS.md ~8 Ko + SOUL.md + …). Et c'est l'instruction la plus **contre-intuitive** —
« cite les deux, ne tranche pas » — qui **cède la première** : présent, clos et « à revérifier »
survivent à la dilution, le disputé non. **Deux mitigations** : (a) un répondeur plus capable du
suivi d'instructions ; (b) attacher la directive *inline* au fait disputé lui-même (une ligne
impérative juste avant la question), plutôt que de compter sur l'en-tête.

> **Test ciblé (une variable, un verdict).** On a rejoué le scénario Lyon VS Brest en ne changeant
> QUE le modèle (OpenClaw pointé sur OpenRouter, **Owl Alpha** gratuit ; le connecteur, le bloc
> injecté, tout le reste identiques). Verdict : Owl Alpha répond *« C'est non tranché — deux sources
> contradictoires, Lyon et Brest ; je ne peux pas trancher »* — il **cite les deux et refuse de
> choisir**, là où qwen3:30b-a3b disait « Brest ». **La dilution du disputé est donc un problème de
> CAPACITÉ du modèle, pas une faille de l'injection** : la mitigation (a) est confirmée. La mémoire
> fait son travail à l'identique ; seul le répondeur faible casse sur l'instruction la plus
> contre-intuitive.

**La latence — négligeable, par conception.** `assemble()` bloque la réponse de l'agent, c'était le
risque annoncé de la Voie A. Il ne se matérialise pas : **16 ms**, parce qu'on a délibérément gardé
`/contexte` **sans LLM** (embedding de la question + marche de graphe). Le répondeur reste celui
d'OpenClaw.

**Le couple Python / TypeScript.** La mémoire tourne comme service local séparé. Avantage : zéro
réécriture, les 48 verdicts intacts. Coût : deux processus à lancer (le service + OpenClaw), un saut
réseau (local, négligeable), et la persistance ajoutée côté service (pickle du graphe). Une réécriture
TS unifierait le tout mais perdrait la non-régression — non recommandé.

**Le tri fait/texte, heuristique.** L'aiguillage de départ (longueur, point d'interrogation) est
volontairement grossier. Un énoncé factuel très long, ou une question qui contient un fait, seront mal
classés. Raffinement possible : un classifieur léger, ou un tag explicite de l'appelant. C'est un
point d'architecture assumé, pas un détail.

**La provenance, au grain de la session.** Aujourd'hui `source_id = openclaw:<session>`. Dans un
canal multi-locuteurs, distinguer les *personnes* (pour que la règle anti-menteur joue entre
interlocuteurs, pas entre sessions) demanderait de remonter l'expéditeur du message. À faire.

---

## 7. Fichiers du connecteur

```
connecteur/
  service.py            service FastAPI : 6 gestes + /contexte (lecture légère sans LLM)
  vitrine_http.py       la vitrine, servie par HTTP (grammaire épistémique au fil du réseau)
  openclaw-plugin/
    index.js            le ContextEngine : assemble→/contexte, afterTurn→/ecrire, tri à la porte
    openclaw.plugin.json  le manifeste
    package.json        lié à l'OpenClaw global (npm link)
  README_CONNECTEUR.md  ce fichier
```
