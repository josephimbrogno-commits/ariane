# -*- coding: utf-8 -*-
"""
etape3b_fix_verbal.py — test du FIX « confiance verbale » (demi-vie 240 j seulement).

Diagnostic de l'étape 3 : C perd sur les faits STABLES parce que le répondeur, voyant une
confiance basse affichée EN CHIFFRES (« 0.20 »), devient timide et refuse — alors que le fait
est en mémoire. Le fix : remplacer le chiffre par un rendu VERBAL à deux niveaux (rien si OK,
« à confirmer » si bas), en gardant les dates.

On reconstruit C à demi-vie 240 j, puis on évalue les 60 questions DEUX FOIS sur la MÊME
mémoire : rendu numérique (actuel) vs rendu verbal (fix). On compare aux baselines B / B′
(chargées depuis etape3_data.json). Objectif : les stables remontent au niveau de B SANS
dégrader les changés → critère complet atteint.

Lance :  python etape3b_fix_verbal.py
"""

import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import cycle
from util import Journal, assurer_dossiers
import monde
from etape2_experience import correct, construire_memoire_C

DEMI_VIE = 240
CONSULT_PAR_MOIS = 10


def prec(lignes, cle, cat=None):
    sel = [l for l in lignes if cat is None or l["categorie"] == cat]
    if not sel:
        return 0.0
    return 100.0 * sum(1 for l in sel if l[cle]) / len(sel)


def main():
    assurer_dossiers()
    J = Journal("etape3b_fix_verbal")
    dire = J.dire
    config.CONSULT_CIBLE_PAR_MOIS = CONSULT_PAR_MOIS
    config.DEMI_VIE_JOURS = float(DEMI_VIE)

    dire("=" * 80)
    dire(f" ÉTAPE 3b — FIX « confiance verbale » (demi-vie {DEMI_VIE} j, seuil verbal "
         f"{config.SEUIL_VERBAL})")
    dire("=" * 80)

    # Baselines B / B′ / A depuis l'étape 3
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape3_data.json"), encoding="utf-8") as fp:
        d3 = json.load(fp)
    precB, precBp, precA = d3["baselines"]["B"], d3["baselines"]["Bprime"], d3["baselines"]["A"]

    faits = monde.generer_monde()
    questions = monde.choisir_questions_eval(faits, config.N_QUESTIONS_EVAL)

    dire(f"\nReconstruction de C à demi-vie {DEMI_VIE} j…")
    memC, meta, sid_vrai, snaps, juge, nconsult = construire_memoire_C(faits, dire)

    dire("\nÉvaluation : rendu NUMÉRIQUE vs rendu VERBAL (même mémoire)…")
    lignes = []
    for i, f in enumerate(questions, start=1):
        att = f.cle_vraie_finale()
        rep_num, _ = cycle.repondre_C(memC, f.question)
        rep_ver, _ = cycle.repondre_C_verbal(memC, f.question)
        lignes.append({
            "question": f.question, "categorie": f.categorie(), "attendu": att,
            "num": rep_num, "okNum": correct(rep_num, att),
            "ver": rep_ver, "okVer": correct(rep_ver, att),
        })
        if i % 20 == 0:
            dire(f"   …{i}/{len(questions)}")

    # Comptage des refus (« je n'ai pas / je ne dispose »)
    def refus(cle):
        return sum(1 for l in lignes if any(m in l[cle.replace("ok", "").lower()].lower()
                   for m in ["pas d'info", "pas trouv", "ne dispose", "aucune info",
                             "n'ai pas", "pas ce souvenir"]))

    res = {
        "C_num": {"global": prec(lignes, "okNum"), "changé": prec(lignes, "okNum", "changé"),
                  "stable": prec(lignes, "okNum", "stable"), "refus": refus("num")},
        "C_ver": {"global": prec(lignes, "okVer"), "changé": prec(lignes, "okVer", "changé"),
                  "stable": prec(lignes, "okVer", "stable"), "refus": refus("ver")},
    }

    dire("\n" + "=" * 80)
    dire(" RÉSULTAT (demi-vie 240 j)")
    dire("=" * 80)
    dire(f"   {'Config':28} | changés | stables | global | refus")
    dire(f"   {'B  (RAG inerte daté)':28} | {precB['changé']:5.0f} % | {precB['stable']:5.0f} % | "
         f"{precB['global']:5.0f} % |   —")
    dire(f"   {'B′ (RAG inerte aveugle)':28} | {precBp['changé']:5.0f} % | {precBp['stable']:5.0f} % | "
         f"{precBp['global']:5.0f} % |   —")
    dire(f"   {'C  (confiance NUMÉRIQUE)':28} | {res['C_num']['changé']:5.0f} % | "
         f"{res['C_num']['stable']:5.0f} % | {res['C_num']['global']:5.0f} % | {res['C_num']['refus']:3d}")
    dire(f"   {'C  (confiance VERBALE/fix)':28} | {res['C_ver']['changé']:5.0f} % | "
         f"{res['C_ver']['stable']:5.0f} % | {res['C_ver']['global']:5.0f} % | {res['C_ver']['refus']:3d}")
    dire("")

    # Verdict
    stable_ok = res["C_ver"]["stable"] >= precB["stable"] - 1e-9
    change_ok = res["C_ver"]["changé"] >= res["C_num"]["changé"] - 5  # pas dégradé (tolérance 5 pts)
    crit_complet = (res["C_ver"]["changé"] > precB["changé"]) and stable_ok
    if res["C_ver"]["stable"] > res["C_num"]["stable"] + 5:
        dire(f"   ✅ Le fix VERBAL fait remonter les faits stables "
             f"({res['C_num']['stable']:.0f}% → {res['C_ver']['stable']:.0f}%) "
             f"— confirme que c'était bien un problème d'AFFICHAGE.")
    else:
        dire(f"   ⚠ Le fix ne change pas nettement les stables "
             f"({res['C_num']['stable']:.0f}% → {res['C_ver']['stable']:.0f}%).")
    if crit_complet:
        dire("   ✅✅ CRITÈRE COMPLET ATTEINT : C (verbal) > B sur les changés ET ≥ B sur les stables.")
    elif stable_ok and change_ok:
        dire("   ✅ Stables au niveau de B sans dégrader les changés.")
    dire("=" * 80)

    with open(os.path.join(config.DOSSIER_RESULTATS, "etape3b_fix_verbal.json"), "w",
              encoding="utf-8") as fp:
        json.dump({"baselines": {"B": precB, "Bprime": precBp, "A": precA},
                   "resultats": res, "critere_complet": crit_complet,
                   "demi_vie": DEMI_VIE, "seuil_verbal": config.SEUIL_VERBAL,
                   "detail": lignes}, fp, ensure_ascii=False, indent=2)
    dire(f"\n Détails : resultats/etape3b_fix_verbal.json\n Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
