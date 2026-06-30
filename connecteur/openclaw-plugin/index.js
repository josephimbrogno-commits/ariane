// connecteur/openclaw-plugin/index.js
//
// Le PONT : un ContextEngine OpenClaw qui branche « la mémoire qui trie » (service Python).
//
//   assemble()  → POST /contexte  : injecte le BLOC épistémique VERBAL (présent / « était… jusqu'à »
//                                   / « à revérifier »). JAMAIS de score numérique.
//   afterTurn() → POST /ecrire    : écrit le fait dit ce tour, source = identité de session.
//   compact()   → no-op           : ownsCompaction=false, on délègue la compaction à OpenClaw.
//
// Tri fait/texte à la porte (décision Hobb) : seul un énoncé court et déclaratif part en mémoire
// structurée ; le texte long figé est laissé au RAG natif (memory-core), notre greffier s'y
// étoufferait. On lit la toile librement ; on ne tisse jamais un fil sans source (la source ici =
// la session). La règle d'or vit dans le service, pas dans le pont.

import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

const SERVICE = process.env.MEMOIRE_SERVICE_URL || "http://127.0.0.1:8077";
const MAX_FAIT = 600; // au-delà : texte figé → pas notre mémoire

const ENTETE =
  "## Mémoire VÉRIFIÉE ET DATÉE — fait AUTORITÉ sur la fraîcheur\n" +
  "Ces faits sont horodatés et triés (le présent séparé du passé). Ils FONT AUTORITÉ sur ce qui est " +
  "à jour : si une autre note (mémoire de rappel, fichier, historique) présente comme actuel un fait " +
  "marqué ici [CLOS], c'est CETTE mémoire datée qui tranche — sers la valeur COURANTE, jamais la close.\n" +
  "Respecte le temps de chaque fait : présent pour [ACTUEL — sûr] ; réserve « il s'agirait de…, à " +
  "revérifier » pour [ACTUEL — incertain] (donne quand même la valeur) ; imparfait borné « était… " +
  "jusqu'à » pour [CLOS]. Pour [DISPUTÉ] : la mémoire n'a PAS tranché — tu DOIS citer LES DEUX " +
  "valeurs avec leurs sources et dire que c'est non tranché ; n'en choisis JAMAIS une seule et " +
  "n'invente aucun label. N'invente aucun chiffre de confiance.\n" +
  "Pour [INFÉRÉ — composé de …] : ce fait n'est PAS observé, il est DÉDUIT en reliant deux faits. " +
  "Présente-le TOUJOURS EXPLICITEMENT comme une déduction (« en reliant ces faits, il semblerait que… ») " +
  "et JAMAIS comme un fait établi ou observé. Si la réponse repose sur un [INFÉRÉ], dis-le. " +
  "Pour [PROMU — dormant redevenu pertinent] : c'est un fait en réserve réactivé par le contexte ; " +
  "tu peux t'en servir, mais signale qu'il a été repêché (« un élément en réserve refait surface… »).\n\n";

// ── helpers messages ─────────────────────────────────────────────────────────
function texteDe(m) {
  if (!m) return "";
  const c = m.content ?? m.text ?? "";
  if (typeof c === "string") return c;
  if (Array.isArray(c))
    return c.map((p) => (typeof p === "string" ? p : p?.text ?? p?.content ?? "")).join(" ");
  return String(c ?? "");
}
function roleDe(m) {
  return String(m?.role ?? m?.author ?? "").toLowerCase();
}
function dernierUser(messages) {
  if (!Array.isArray(messages)) return "";
  for (let i = messages.length - 1; i >= 0; i--)
    if (roleDe(messages[i]) === "user") return texteDe(messages[i]).trim();
  return "";
}
function estimerTokens(messages, ajout) {
  let n = ajout ? ajout.length : 0;
  if (Array.isArray(messages)) for (const m of messages) n += texteDe(m).length;
  return Math.ceil(n / 4); // approximation grossière (4 car ≈ 1 token)
}

// ── tri fait / texte / ignorer (la porte d'entrée) ───────────────────────────
function classer(texte) {
  const t = (texte || "").trim();
  if (!t) return "ignorer";
  if (t.length > MAX_FAIT) return "texte"; // figé → RAG natif, pas notre greffier
  if (t.endsWith("?")) return "ignorer"; // une question n'est pas un fait à stocker
  return "fait";
}

// ── appels au service Python ─────────────────────────────────────────────────
async function poster(chemin, corps) {
  const r = await fetch(`${SERVICE}${chemin}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corps),
  });
  if (!r.ok) throw new Error(`${chemin} → HTTP ${r.status}`);
  return r.json();
}

export default definePluginEntry({
  id: "memoire-qui-trie",
  name: "Memoire qui trie",
  description:
    "Moteur de TRI du périmé : injecte des faits datés (grammaire épistémique) avant la réponse et " +
    "écrit les faits du tour. Coexiste avec memory-core (qui garde le rappel/RAG + dreaming).",
  register(api) {
    const log = api.logger ?? console;

    api.registerContextEngine("memoire-qui-trie", () => ({
      info: { id: "memoire-qui-trie", name: "Mémoire qui trie", ownsCompaction: false },

      // LECTURE : injecter le bloc épistémique verbal (sans répondeur, c'est /contexte).
      async assemble({ messages, prompt }) {
        const base = { messages, estimatedTokens: estimerTokens(messages) };
        const question = (prompt && prompt.trim()) || dernierUser(messages);
        if (!question) return base;
        try {
          const r = await poster("/contexte", { question });
          const bloc = (r && r.bloc) || "";
          if (!bloc.trim()) return base;
          const ajout = ENTETE + bloc;
          return { messages, estimatedTokens: estimerTokens(messages, ajout), systemPromptAddition: ajout };
        } catch (e) {
          log.warn?.(`[memoire-qui-trie] assemble: service muet (${e.message}) — aucune injection`);
          return base;
        }
      },

      // ingest requis mais l'écriture passe par afterTurn (tour complet) : ici no-op.
      async ingest() {
        return { ingested: false };
      },

      // ÉCRITURE : trier puis écrire le fait dit ce tour, source = la session.
      async afterTurn({ messages, sessionKey, sessionId, isHeartbeat }) {
        if (isHeartbeat) return;
        const texte = dernierUser(messages);
        const genre = classer(texte);
        if (genre !== "fait") {
          if (genre === "texte")
            log.info?.(`[memoire-qui-trie] tri: énoncé long → laissé au RAG natif (non écrit)`);
          return;
        }
        const source = `openclaw:${sessionKey || sessionId || "session"}`;
        try {
          const r = await poster("/ecrire", { enonce: texte, source_id: source });
          log.info?.(`[memoire-qui-trie] écrit ← « ${texte.slice(0, 60)} » : ${r.action ?? r.erreur}`);
        } catch (e) {
          log.warn?.(`[memoire-qui-trie] afterTurn: écriture impossible (${e.message})`);
        }
      },

      // ownsCompaction=false : on délègue la compaction au runtime OpenClaw.
      async compact() {
        return { ok: true, compacted: false, reason: "compaction déléguée à OpenClaw (ownsCompaction:false)" };
      },
    }));

    log.info?.(`[memoire-qui-trie] ContextEngine enregistré (service ${SERVICE})`);
  },
});
