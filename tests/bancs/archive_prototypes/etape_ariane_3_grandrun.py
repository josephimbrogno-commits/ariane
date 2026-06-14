# -*- coding: utf-8 -*-
"""
etape_ariane_3_grandrun.py — ARIANE · étape 3 : le grand run (mécanique, sans LLM).

Banc figé (graine loguée). Quatre configs sur le MÊME graphe :
  • inerte   : RAG plancher (similarité seule, pas de dormance, pas d'importance).
  • porte     : reconnaissance/rappel, dormance V2 (β=0), SANS importance.
  • axe       : reconnaissance + importance (dormance β=0.9 + terme de score). L'axe complet.
  • axe-retr  : importance dans le RETRIEVAL seulement (β=0). (confirmation V3.)

Notation MÉCANIQUE contre la vérité-terrain du générateur :
  - complétude = rappel@K (les faits-vérité sont-ils dans le top-K évoqué ?)
  - pureté     = précision@|vérité| (les pertinents arrivent-ils en tête, ou des capitaux hors-sujet
                 les déplacent-ils ?)
  - justesse de statut sur les P3 (clos servi à l'imparfait = juste).

DEUX CHIFFRES EN PRIORITÉ, par config :
  (1) complétude sur les P1 aux questions T3 — le terrain où l'axe peut GAGNER.
  (2) pureté sur Q8 (T3b) + les T1 — le terrain où il peut SE TRAHIR par inondation.

Lance :  python etape_ariane_3_grandrun.py
"""

import json
import os
import sys
from datetime import timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import ariane_monde as A
import ariane_notation  # noqa (réutilisable ; ici on note mécaniquement au niveau récupération)
import v2_lecture
import v3_importance
from util import Journal, assurer_dossiers
from embeddings import encoder_un
from v2_modele import GrapheMemoire, norm_nom

SEED = 42
HORIZON_MOIS = 24
K = 10                       # budget d'évocation (rappel@K)
BONUS_RECONNAISSANCE = 5.0   # une entité nommée → ses faits remontent en tête


def construire(entites, faits):
    g = GrapheMemoire()
    debut = config.MONDE_DEBUT
    objs = {}
    for f in sorted(faits, key=lambda x: (x.mois_de, x.fid)):
        date = debut + timedelta(days=30 * f.mois_de)
        dv = date.strftime("%Y-%m") if f.mois_de > 0 else None
        res = g.ingerer(f.sujet, f.predicat, f.objet, source_id="gen", date_obs=date, date_validite=dv)
        fa = res["touches"][-1]
        objs[f.fid] = fa
        for k in range(f.acces):
            jour = 30 * (HORIZON_MOIS - 1 if f.acces_recents else f.mois_de) + k
            g.acceder(fa, debut + timedelta(days=jour))
    for nom, t in entites.items():
        e = g.trouver_entite(nom)
        if e:
            e.type = t
    horizon = debut + timedelta(days=30 * HORIZON_MOIS)
    g._decroitre(horizon)
    v3_importance.calculer(g)
    gfid_to_afid = {gf.id: afid for afid, gf in objs.items()}
    return g, objs, gfid_to_afid


def ranking(g, q, mode, qtok, v):
    reconnu = {f.id for f in v2_lecture.reconnaissance(g, q["libelle"])} if mode != "inerte" else set()
    cands = []
    for f in g.faits.values():
        rec = f.id in reconnu
        if mode != "inerte" and f.statut == "dormant" and not rec:
            continue
        sim = float(v @ f.embedding)
        if mode == "inerte":
            s = sim
        else:
            s = config.IMP_W_SIM * sim + config.IMP_W_FORCE * f.force
            if mode in ("axe", "axe_retr"):
                s += config.IMP_W_IMPORTANCE * f.importance
            e = g.entites.get(f.sujet_id)
            if e:
                et = set(norm_nom(e.nom).split())
                if et and et <= qtok:
                    s += config.IMP_W_ENTITE
            if rec:
                s += BONUS_RECONNAISSANCE
        cands.append((f.id, s))
    cands.sort(key=lambda x: -x[1])
    return [fid for fid, _ in cands]


def main():
    assurer_dossiers()
    J = Journal("ariane_3_grandrun")
    dire = J.dire
    dire("=" * 92)
    dire(f" ARIANE · ÉTAPE 3 — GRAND RUN MÉCANIQUE (graine={SEED}, horizon={HORIZON_MOIS} mois, K={K})")
    dire("=" * 92)

    entites, faits, questions = A.generer_grand(seed=SEED, n_hubs=8, n_orgs=6)
    nP1 = sum(1 for f in faits if f.profil == "P1")
    dire(f"\n Monde GELÉ : {len(entites)} entités · {len(faits)} faits "
         f"(P1={nP1}, P2={sum(1 for f in faits if f.profil=='P2')}, "
         f"P3={sum(1 for f in faits if f.profil=='P3')}, P4={sum(1 for f in faits if f.profil=='P4')}) "
         f"· {len(questions)} questions")

    g, objs, gmap = construire(entites, faits)
    # combien de P1 survivent (non dormant) selon β ? (diagnostic)
    for beta, lbl in [(0.0, "β=0 (porte)"), (0.9, "β=0.9 (axe)")]:
        g.recalculer_dormance(beta)
        actifs_p1 = sum(1 for af, gf in objs.items()
                        if faits[af - 1].profil == "P1" and gf.statut != "dormant")
        dire(f"   P1 non-dormants à {lbl} : {actifs_p1}/{nP1}")

    MODES = [("inerte", None), ("porte", 0.0), ("axe", 0.9), ("axe_retr", 0.0)]
    res = {m: {"recallK": [], "precT": [], "P1T3_recall": [], "purete_Q8T1": [],
               "statut_total": 0, "statut_faux": 0} for m, _ in MODES}

    for mode, beta in MODES:
        if beta is not None:
            g.recalculer_dormance(beta)
        for q in questions:
            qtok = set(norm_nom(q["libelle"]).split())
            v = encoder_un(q["libelle"])
            ranked_g = ranking(g, q, mode, qtok, v)
            ranked = [gmap[g_] for g_ in ranked_g if g_ in gmap]
            cibles, _ = A.verite(q, faits)
            truth = {f.fid for f in cibles}
            if not truth:
                continue
            t = len(truth)
            recallK = len(truth & set(ranked[:K])) / t
            precT = len(truth & set(ranked[:t])) / t
            res[mode]["recallK"].append(recallK)
            res[mode]["precT"].append(precT)
            if q["type"] == "T3":
                res[mode]["P1T3_recall"].append(recallK)
            if q["type"] in ("T1", "T3b"):
                res[mode]["purete_Q8T1"].append(precT)
            # justesse de statut sur les P3 (clos) présents dans le top-K
            for fid in (truth & set(ranked[:K])):
                gf = objs[fid]
                if faits[fid - 1].profil == "P3":
                    res[mode]["statut_total"] += 1
                    if gf.statut != "clos":     # devrait être clos → imparfait
                        res[mode]["statut_faux"] += 1

    def moy(L):
        return 100.0 * sum(L) / len(L) if L else 0.0

    # ── RAPPORT ──────────────────────────────────────────────────────────
    R = []
    w = R.append
    w(f"# Ariane — étape 3 : le crash test de l'axe Importance (graine {SEED}, banc gelé)\n")
    w(f"Monde : {len(entites)} entités, {len(faits)} faits (P1={nP1}), {len(questions)} questions, "
      f"horizon {HORIZON_MOIS} mois, K={K}. Notation mécanique (sans LLM).\n")
    w("## LES DEUX CHIFFRES DÉCISIFS (séparés des moyennes globales)\n")
    w("| Config | (1) Complétude P1 @ T3 *(gagner)* | (2) Pureté @ Q8+T1 *(se trahir)* |")
    w("|---|---|---|")
    for m, _ in MODES:
        w(f"| {m} | **{moy(res[m]['P1T3_recall']):.0f} %** | **{moy(res[m]['purete_Q8T1']):.0f} %** |")
    w("\n*(1) = les faits capitaux jamais consultés remontent-ils en rappel libre ? "
      "(2) = les évocations triviales/par attribut restent-elles pures, ou le capital les inonde-t-il ?*\n")
    w("## Moyennes globales (contexte)\n")
    w("| Config | Complétude (rappel@K) | Pureté (précision@|vérité|) | Statut faux (P3) |")
    w("|---|---|---|---|")
    for m, _ in MODES:
        w(f"| {m} | {moy(res[m]['recallK']):.0f} % | {moy(res[m]['precT']):.0f} % | "
          f"{res[m]['statut_faux']}/{res[m]['statut_total']} |")
    w("")

    # ── VERDICT ──────────────────────────────────────────────────────────
    c_porte = moy(res["porte"]["P1T3_recall"])
    c_axe = moy(res["axe"]["P1T3_recall"])
    p_porte = moy(res["porte"]["purete_Q8T1"])
    p_axe = moy(res["axe"]["purete_Q8T1"])
    gain_compl = c_axe - c_porte
    perte_purete = p_porte - p_axe
    w("## VERDICT\n")
    w(f"- Complétude P1@T3 : porte **{c_porte:.0f}%** → axe **{c_axe:.0f}%** (gain **{gain_compl:+.0f} pts**).")
    w(f"- Pureté @ Q8+T1 : porte **{p_porte:.0f}%** → axe **{p_axe:.0f}%** (variation **{-perte_purete:+.0f} pts**).")
    if gain_compl >= 15 and perte_purete <= 10:
        verdict = ("✅ L'AXE A GAGNÉ SA PLACE : il fait remonter les faits capitaux que la porte laisse "
                   "muets, SANS effondrement de pureté.")
    elif gain_compl >= 15 and perte_purete > 10:
        verdict = ("⚠️ NUANCÉ : l'axe récupère des capitaux (gain de complétude) MAIS au prix d'une "
                   "chute de pureté (inondation). Arbitrage, pas victoire nette.")
    else:
        verdict = ("❌ L'AXE EST RÉFUTÉ : aucun gain de complétude P1 significatif sur son terrain — "
                   "la porte seule suffit (ou l'importance n'a pas surclassé la similarité/Force).")
    w(verdict + "\n")

    chemin = os.path.join(config.DOSSIER_RESULTATS, "ariane_3_rapport.md")
    with open(chemin, "w", encoding="utf-8") as fp:
        fp.write("\n".join(R))
    with open(os.path.join(config.DOSSIER_RESULTATS, "ariane_3_data.json"), "w", encoding="utf-8") as fp:
        json.dump({m: {"P1T3": moy(res[m]["P1T3_recall"]), "purete_Q8T1": moy(res[m]["purete_Q8T1"]),
                       "recallK": moy(res[m]["recallK"]), "precT": moy(res[m]["precT"]),
                       "statut_faux": res[m]["statut_faux"]} for m, _ in MODES},
                  fp, ensure_ascii=False, indent=2)

    dire("\n" + "=" * 92)
    dire(" LES DEUX CHIFFRES (complétude P1@T3 | pureté @Q8+T1) :")
    for m, _ in MODES:
        dire(f"   {m:9} : {moy(res[m]['P1T3_recall']):3.0f}%  |  {moy(res[m]['purete_Q8T1']):3.0f}%")
    dire("")
    dire(" VERDICT : " + verdict.split(":")[0].replace("✅", "").replace("❌", "").replace("⚠️", "").strip())
    dire("=" * 92)
    dire(f"\n Rapport : {chemin}\n Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
