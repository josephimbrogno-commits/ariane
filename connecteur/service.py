# -*- coding: utf-8 -*-
"""
connecteur/service.py — la bibliothèque `memoire/` exposée en service HTTP local (Voie A).

Un petit serveur FastAPI qui instancie `Memoire(llm, embed)` avec l'adaptateur Ollama EXISTANT et
expose les 6 gestes + l'inspection. Aucune réécriture du cœur : on l'importe tel quel (48 verdicts
intacts). La persistance est ajoutée ICI (pickle du graphe, embed détaché), pas dans la lib.

Endpoints :
  CONTENU    POST /ecrire · POST /lire · POST /consolider
  STRUCTURE  GET  /parcourir · POST /lier · POST /retoucher
  INSPECTION GET  /inspecter
  PONT       POST /contexte   ← lecture LÉGÈRE (récup + grammaire épistémique, SANS répondeur LLM)
                                 c'est ce que appellera assemble() d'OpenClaw.
  + GET /sante · POST /ecrire_triplet (déterministe, tests) · POST /reset (tests)

Règle d'or préservée à travers le réseau : `lier`/`retoucher` sans source → HTTP 422 (échec propre).

Lancer :  python -m uvicorn connecteur.service:app --host 127.0.0.1 --port 8077
"""

import os
import pickle
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from memoire import Memoire, config
from memoire.coeur import lecture
from memoire.coeur.graphe import norm_nom
from memoire.coeur.ontologie import PREDICATS
from memoire.adaptateurs.ollama_qwen import OllamaLLM, faire_embed

# ── persistance (côté service, le cœur reste intact) ─────────────────────────
CHEMIN = os.environ.get(
    "MEMOIRE_STORE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees", "graphe.pkl"),
)
_verrou = threading.Lock()        # une seule mutation du graphe à la fois

print("[service] chargement de l'adaptateur Ollama + embeddings…")
_llm = OllamaLLM(modele=os.environ.get("MEMOIRE_MODELE", "qwen3:30b-a3b"))
_embed = faire_embed()
mem = Memoire(llm=_llm, embed=_embed)


def sauver():
    os.makedirs(os.path.dirname(CHEMIN), exist_ok=True)
    e = mem.g.embed                       # l'embed (closure sur le modèle) n'est pas picklable
    mem.g.embed = None
    try:
        with open(CHEMIN, "wb") as f:
            pickle.dump(mem.g, f)
    finally:
        mem.g.embed = e


def charger():
    if os.path.exists(CHEMIN):
        with open(CHEMIN, "rb") as f:
            g = pickle.load(f)
        g.embed = _embed                  # on rebranche l'embed à la volée
        mem.g = g
        return True
    return False


_charge = charger()
print(f"[service] base mémoire : {CHEMIN} ({'chargée' if _charge else 'neuve'}) — "
      f"{len(mem.g.faits)} faits, {len(mem.g.entites)} entités")

app = FastAPI(title="memoire-qui-trie · service", version="1.0")


# ── schémas d'entrée ─────────────────────────────────────────────────────────
class Ecrire(BaseModel):
    enonce: str
    source_id: str
    date: str | None = None


class Triplet(BaseModel):
    sujet: str
    predicat: str
    objet: str
    source_id: str
    date: str | None = None
    validite: str | None = None


class Question(BaseModel):
    question: str
    date: str | None = None


class Consolider(BaseModel):
    date: str | None = None


class Lier(BaseModel):
    entite_a: str
    relation: str
    entite_b: str
    source_id: str | None = None
    date: str | None = None
    validite: str | None = None


class Retoucher(BaseModel):
    fait_id: int
    action: str                            # clore | contester | corroborer
    source_id: str | None = None
    date: str | None = None


# ── helpers ──────────────────────────────────────────────────────────────────
def _resume_touches(res):
    """Compte rendu JSON-safe d'un résultat d'ingestion (action + faits touchés)."""
    if not isinstance(res, dict):
        return res
    out = {"action": res.get("action")}
    out["faits"] = [mem.g.fait_court(f) for f in res.get("touches", [])]
    return out


FOCUS_MAX = 10   # plafond de faits injectés (anti-flood sur les nœuds-hub)


def _focaliser(g, injectes, question, maxf=FOCUS_MAX):
    """Focus connecteur (la mémoire ne change pas) : sur un graphe réel, un nœud-HUB nommé dans la
    question (« CAC 40 », « Coupe du monde 2026 ») fait remonter par reconnaissance TOUS les faits qui
    le visent (40 membres, 15 qualifiés). On écarte les faits HORS-SUJET (aucun mot commun avec la
    question), on classe l'entité SPÉCIFIQUEMENT nommée en tête (et son histoire close), on plafonne."""
    qtok = set(norm_nom(question).split())
    scored = []
    for f in injectes:
        s_tok = set(norm_nom(g.nom_entite(f.sujet_id)).split())
        o_nom = g.nom_entite(f.objet_id) if f.objet_id is not None else str(f.objet)
        o_tok = set(norm_nom(o_nom).split())
        sujet_nomme, objet_nomme = bool(s_tok & qtok), bool(o_tok & qtok)
        if not (sujet_nomme or objet_nomme):
            continue                       # autre domaine → écarté
        clos = f.statut == "clos" or f.statut_avant_dormance == "clos"
        score = (2 if sujet_nomme else 0) + (1 if (clos and sujet_nomme) else 0)
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    gardes = [f for _, f in scored[:maxf]]
    return gardes if gardes else injectes[:maxf]   # filet : jamais vide si on avait quelque chose


def _bloc(question, date_lecture):
    """Récupération LÉGÈRE : entrée vectorielle + reconnaissance + marche de graphe → focus → bloc
    épistémique VERBAL. Reproduit l'assemblage de lecture.lire SANS le répondeur ni le juge.
    C'est ce que assemble() injectera dans le prompt système d'OpenClaw."""
    g = mem.g
    faits_e, v = lecture.entree_vectorielle(g, question)
    reco = lecture.reconnaissance(g, question) if config.OPT_RECONNAISSANCE else []
    vus, injectes = set(), []
    for f in reco + faits_e:               # reconnaissance d'abord (priorité au nœud nommé)
        if f.id not in vus:
            vus.add(f.id)
            injectes.append(f)
    for f in lecture.marche_graphe(g, faits_e + reco, v):
        if f.id not in vus:
            vus.add(f.id)
            injectes.append(f)
    # ── INFÉRENCE 2B (chantier RACCORD) — LE LABEL AVANT LE PUSH ───────────────────────────────────
    # On compose sur le pool COMPLET (AVANT _focaliser) : la chaîne (ex. Velora→Damien) n'est pas nommée
    # dans la question, donc _focaliser l'écarterait et la composition échouerait. On résout le « focus
    # jette la chaîne » SANS affaiblir l'anti-flood (qui ne protège que les faits OBSERVÉS poussés).
    # La discipline 2B (table blanche + gate de type) garantit 0 faux chemin ; chaque fait composé porte
    # TOUJOURS son label « inféré » + provenance (FaitInfere.rendu) — jamais servi comme observé.
    inferes = []
    if lecture.NOYAU_GRAMMAIRE:
        from memoire.coeur.grammaire import composer
        inferes = composer(g, injectes)
    injectes = _focaliser(g, injectes, question)   # anti-flood (connecteur) sur les faits OBSERVÉS
    for f in injectes:                     # la consultation renforce la Force (réveil éventuel)
        g.acceder(f, date_lecture)
    bloc = lecture.rendu_epistemique(g, injectes)
    # On ne POUSSE que les inférences PERTINENTES (entité nommée dans la question), labellisées inféré.
    if inferes:
        from memoire.coeur.grammaire import rendu_infere
        qtok = set(norm_nom(question).split())
        pert = [fi for fi in inferes
                if (set(norm_nom(fi.sujet).split()) & qtok) or (set(norm_nom(fi.objet).split()) & qtok)]
        bloc_inf = rendu_infere(pert, actifs_seulement=True)
        if bloc_inf:
            bloc = (bloc + "\n" + bloc_inf) if bloc else bloc_inf
    return bloc, injectes


# ── CONTENU ──────────────────────────────────────────────────────────────────
@app.post("/ecrire")
def ecrire(c: Ecrire):
    with _verrou:
        res = mem.ecrire(c.enonce, source_id=c.source_id, date=c.date)
        sauver()
    return _resume_touches(res)


@app.post("/ecrire_triplet")
def ecrire_triplet(t: Triplet):
    with _verrou:
        res = mem.ecrire_triplet(t.sujet, t.predicat, t.objet, source_id=t.source_id,
                                 date=t.date, validite=t.validite)
        sauver()
    return _resume_touches(res)


@app.post("/lire")
def lire(q: Question):
    """Lecture COMPLÈTE : récupération + réponse en langue naturelle via le répondeur LLM."""
    with _verrou:
        r = mem.lire(q.question, date=q.date)
        sauver()
    return {"reponse": r["reponse"], "bloc": r["bloc"],
            "injectes": [mem.g.fait_court(f) for f in r["injectes"]],
            "reveils": r["reveils"]}


@app.post("/consolider")
def consolider(c: Consolider):
    with _verrou:
        rapport = mem.consolider(date=c.date)
        sauver()
    return rapport


# ── PONT (lecture légère pour assemble) ──────────────────────────────────────
@app.post("/contexte")
def contexte(q: Question):
    """Le bloc épistémique VERBAL seul (sans répondeur). Rapide : embeddings + marche de graphe.
    À injecter tel quel dans systemPromptAddition côté OpenClaw."""
    with _verrou:
        bloc, injectes = _bloc(q.question, mem._date(q.date))
        sauver()
    return {"bloc": bloc, "injectes": [mem.g.fait_court(f) for f in injectes],
            "n": len(injectes)}


# ── STRUCTURE ────────────────────────────────────────────────────────────────
@app.get("/parcourir")
def parcourir(entite: str, profondeur: int = 1):
    vue = mem.parcourir(entite, profondeur=profondeur)
    if vue is None:
        raise HTTPException(404, f"entité inconnue : {entite}")
    return vue


@app.post("/lier")
def lier(l: Lier):
    try:
        with _verrou:
            res = mem.lier(l.entite_a, l.relation, l.entite_b, source_id=l.source_id,
                           date=l.date, validite=l.validite)
            sauver()
    except ValueError as e:                # règle d'or : pas de source → échec PROPRE (422)
        raise HTTPException(422, str(e))
    return _resume_touches(res)


@app.post("/retoucher")
def retoucher(r: Retoucher):
    try:
        with _verrou:
            res = mem.retoucher(r.fait_id, r.action, source_id=r.source_id, date=r.date)
            sauver()
    except ValueError as e:
        raise HTTPException(422, str(e))
    return res if isinstance(res, dict) and "touches" not in res else _resume_touches(res)


# ── INSPECTION ───────────────────────────────────────────────────────────────
@app.get("/faits")
def faits():
    """Liste structurée de TOUS les faits (lecture seule) — pour le tableau de bord."""
    g = mem.g
    out = []
    for f in g.faits.values():
        statut_eff = f.statut_avant_dormance if f.statut == "dormant" else f.statut
        out.append({
            "id": f.id, "sujet": g.nom_entite(f.sujet_id), "predicat": f.predicat,
            "objet": g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet,
            "statut": f.statut, "statut_effectif": statut_eff,
            "force": round(f.force, 2), "certitude": round(f.certitude, 2),
            "n_sources": f.n_sources(), "sources": sorted({p["source_id"] for p in f.provenance}),
            "valide_de": f.valide_de.strftime("%Y-%m") if f.valide_de else None,
            "valide_jusqua": f.valide_jusqua.strftime("%Y-%m") if f.valide_jusqua else None,
            "volatilite": PREDICATS.get(f.predicat, {}).get("volatilite"),
        })
    out.sort(key=lambda x: (x["sujet"], x["predicat"]))
    return {"n": len(out), "faits": out, "entites": sorted(e.nom for e in g.entites.values())}


@app.get("/inspecter")
def inspecter(ref: str):
    cible = int(ref) if ref.lstrip("-").isdigit() else ref
    res = mem.inspecter(cible)
    if res is None:
        raise HTTPException(404, f"référence inconnue : {ref}")
    return res


# ── SANTÉ / RESET ────────────────────────────────────────────────────────────
@app.get("/sante")
def sante():
    return {"ok": True, "faits": len(mem.g.faits), "entites": len(mem.g.entites),
            "modele": _llm.modele, "store": CHEMIN,
            "options": {"reconnaissance": config.OPT_RECONNAISSANCE,
                        "typologie": config.OPT_TYPOLOGIE,
                        "importance": config.OPT_IMPORTANCE}}


@app.post("/reset")
def reset():
    """Repart d'une mémoire vierge (tests / vitrine)."""
    from memoire.coeur.graphe import GrapheMemoire
    with _verrou:
        mem.g = GrapheMemoire(_embed)
        sauver()
    return {"ok": True, "faits": 0}
