# -*- coding: utf-8 -*-
"""
etape_v2_duel_repondeurs.py — MINI-DUEL DE RÉPONDEURS (préparation du grand run V2).

Avant de choisir le répondeur du grand run « au flair », on le décide sur mesure : llama3.1:8b
vs qwen3:30b-a3b, sur les MÊMES 10 questions de l'étape 2 et le MÊME contexte injecté (même
rendu épistémique). On mesure deux choses :
  - REFUS    : combien de fois le répondeur botte en touche alors que l'info est présente.
  - FIDÉLITÉ : respecte-t-il la grammaire épistémique (présent / imparfait pour un clos /
               les deux valeurs pour un disputé / réserve pour un incertain) et donne-t-il la
               bonne valeur ?

Si qwen gagne, on NOTE l'angle mort du « double rôle » : qwen serait alors à la fois extracteur,
juge d'usage ET répondeur — un même biais pourrait se propager dans les trois rôles.

Lance :  python etape_v2_duel_repondeurs.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import modele
import v2_lecture
from util import Journal
from v2_modele import GrapheMemoire, norm_valeur
from etape_v2_2_lecture import BASE, QUESTIONS, LECTURE, d

REPONDEURS = ["llama3.1:8b", "qwen3:30b-a3b"]


def construire():
    g = GrapheMemoire()
    for (su, pr, ob, src, dt, va) in BASE:
        g.ingerer(su, pr, ob, source_id=src, date_obs=d(dt), date_validite=va)
    g.appliquer_decroissances(LECTURE)
    return g


def refus(rep):
    s = rep.lower()
    return any(m in s for m in ["pas d'info", "ne dispose", "aucun", "pas trouv", "ne sais",
                                "souvenir concernant", "ne peux pas", "ne peux répondre",
                                "pas en mesure"])


def fidele(i, rep):
    """Fidélité à la grammaire épistémique + bonne valeur, par question (index 0..9)."""
    r = rep.lower()
    n = norm_valeur(rep)
    ref = refus(rep)
    regles = {
        0: ("doss" in r) and not ref,                       # présent
        1: ("karel" in r) and ("etait" in n),               # clos → imparfait
        2: ("lyon" in r) and ("brest" in r),                # disputé → les deux
        3: ("sora" in r) and not ref,                       # érodé → réserve, pas refus
        4: ("nexora" in r),                                 # 1 saut
        5: ("avocat" in r),                                 # dormant
        6: ("1998" in r),                                   # immuable
        7: ("panneau" in r) and ("batter" in r),            # multi-valué : les deux
        8: ("520" in r),                                    # incertain → valeur + réserve
        9: ref,                                             # absent → refus légitime
    }
    return regles[i], ref


def main():
    J = Journal("etape_v2_duel_repondeurs")
    dire = J.dire
    dire("=" * 100)
    dire(" V2 · MINI-DUEL DE RÉPONDEURS — llama3.1:8b vs qwen3:30b-a3b (mêmes 10 questions, même contexte)")
    dire("=" * 100)

    stats = {m: {"refus": 0, "fidele": 0} for m in REPONDEURS}

    for i, (q, attendu) in enumerate(QUESTIONS):
        g = construire()
        faits_e, v = v2_lecture.entree_vectorielle(g, q, k=3)
        faits_m = v2_lecture.marche_graphe(g, faits_e, v)
        vus, injectes = set(), []
        for f in faits_e + faits_m:
            if f.id not in vus:
                vus.add(f.id)
                injectes.append(f)
        bloc = v2_lecture.rendu_epistemique(g, injectes)
        prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {q}\nRéponse :"

        dire("\n" + "─" * 100)
        dire(f"[{i+1:2}] « {q} »   (attendu : {attendu})")
        for m in REPONDEURS:
            rep = modele.repondre(prompt, systeme=v2_lecture.SYS_REPONSE_V2, temperature=0.0, model=m)
            fid, ref = fidele(i, rep)
            if ref and i != 9:        # le refus n'est légitime QUE pour la Q10 (absente)
                stats[m]["refus"] += 1
            if fid:
                stats[m]["fidele"] += 1
            court = (rep[:96] + "…") if len(rep) > 97 else rep
            dire(f"    {m:14} {'✅' if fid else '❌'}{' ⛔refus' if ref and i!=9 else ''}  « {court} »")

    # ── BILAN ────────────────────────────────────────────────────────────
    dire("\n" + "=" * 100)
    dire(" BILAN DU DUEL (sur 10 questions)")
    dire("=" * 100)
    dire(f"   {'Répondeur':16} | Fidélité épistémique | Refus injustifiés")
    for m in REPONDEURS:
        dire(f"   {m:16} |        {stats[m]['fidele']:2}/10         |        {stats[m]['refus']:2}")
    dire("")

    fl, fq = stats["llama3.1:8b"]["fidele"], stats["qwen3:30b-a3b"]["fidele"]
    rl, rq = stats["llama3.1:8b"]["refus"], stats["qwen3:30b-a3b"]["refus"]
    gagnant = "qwen3:30b-a3b" if (fq, -rq) > (fl, -rl) else "llama3.1:8b"
    dire(f"   → Répondeur retenu pour le grand run V2 : **{gagnant}**")
    if gagnant == "qwen3:30b-a3b":
        dire("")
        dire("   ⚠ ANGLE MORT « DOUBLE RÔLE » (à noter dans le rapport) : qwen serait alors")
        dire("     EXTRACTEUR (écriture) + JUGE D'USAGE (lecture) + RÉPONDEUR. Un même biais du")
        dire("     modèle (ex. sur la récence, déjà mesuré à 15 % en V1) pourrait se corréler")
        dire("     entre les rôles : il faudra garder un garde-fou (extraction et contradiction")
        dire("     restent RÈGLE/DONNÉES, jamais un verdict de lecture) et mesurer séparément.")
    dire("\n" + "=" * 100)
    dire(f" ✅ Duel terminé. Journal : {J.chemin}")
    dire("=" * 100)
    J.fermer()


if __name__ == "__main__":
    main()
