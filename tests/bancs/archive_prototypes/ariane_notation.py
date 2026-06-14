# -*- coding: utf-8 -*-
"""
ariane_notation.py — NOTATION MÉCANIQUE du banc Ariane (complétude × pureté × F-mesure + statut).

Une réponse de rappel libre est une LISTE de faits, chacun assorti d'un STATUT asserté
(« present » ou « imparfait »). On la compare à la vérité-terrain du générateur :

  - Complétude (rappel)  : parmi les faits qui DEVAIENT remonter, combien ont remonté ?
  - Pureté (précision)   : parmi les faits remontés, combien étaient pertinents ?
  - F-mesure             : moyenne harmonique (anti-hedging : déverser tout → complétude haute mais
                           pureté basse → F médiocre).
  - Justesse de STATUT   : un fait clos (P3) remonté À L'IMPARFAIT compte juste ; remonté AU PRÉSENT
                           compte FAUX — et c'est DISTINCT de l'absence (ne pas le citer = simple
                           perte de complétude, pas une erreur de statut).

Aucun LLM ici : tout est mécanique contre la vérité du générateur.
"""

import ariane_monde as A


def noter(reponse_q, q, faits):
    """reponse_q : liste de (fid, statut_asserté ∈ {'present','imparfait'}). Renvoie un dict de scores."""
    cibles, _ = A.verite(q, faits)
    attendu = {f.fid: ("imparfait" if f.statut() == "clos" else "present") for f in cibles}
    truth = set(attendu)
    clos_fids = {f.fid for f in faits if f.statut() == "clos"}

    ret = {fid for fid, _ in reponse_q}
    stat = dict(reponse_q)
    pert = ret & truth

    completude = len(pert) / len(truth) if truth else (1.0 if not ret else 0.0)
    purete = len(pert) / len(ret) if ret else 1.0
    f_mesure = (2 * completude * purete / (completude + purete)) if (completude + purete) > 0 else 0.0

    statut_total = statut_ok = statut_faux = 0
    for fid in ret:
        if fid in attendu:
            statut_total += 1
            if stat[fid] == attendu[fid]:
                statut_ok += 1
            elif attendu[fid] == "imparfait" and stat[fid] == "present":
                statut_faux += 1        # ex : Marc cité au présent alors qu'il est clos
        elif fid in clos_fids and stat[fid] == "present":
            statut_faux += 1            # un périmé hors-vérité servi comme courant

    return {"completude": completude, "purete": purete, "f_mesure": f_mesure,
            "ret": len(ret), "pert": len(pert), "truth": len(truth),
            "statut_total": statut_total, "statut_ok": statut_ok, "statut_faux": statut_faux}


def noter_banc(reponses, questions, faits):
    """reponses : dict qid -> liste de (fid, statut). Agrège sur tout le banc (macro-moyenne)."""
    lignes, sc = [], []
    sf_total = 0
    for q in questions:
        r = noter(reponses.get(q["qid"], []), q, faits)
        r["qid"] = q["qid"]
        r["type"] = q["type"]
        lignes.append(r)
        sc.append(r)
        sf_total += r["statut_faux"]
    n = len(sc)
    agg = {
        "completude": sum(r["completude"] for r in sc) / n,
        "purete": sum(r["purete"] for r in sc) / n,
        "f_mesure": sum(r["f_mesure"] for r in sc) / n,
        "statut_faux": sf_total,
    }
    return agg, lignes
