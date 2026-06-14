# -*- coding: utf-8 -*-
"""
tests/bancs/banc_ariane.py — NON-RÉGRESSION de l'option importance en RAPPEL LIBRE (mission Ariane).

Rejoue le grand run mécanique (graine 42) avec le graphe, la reconnaissance et l'importance de la
BIBLIOTHÈQUE (embed injecté = le même modèle `encoder_un` que le prototype). ariane_monde reste la
fixture de banc. Notation mécanique contre la vérité-terrain (sans LLM). Chiffres au pourcent près.

Référence (prototype plat etape_ariane_3_grandrun, graine 42, horizon 24, K=10) :
  P1 non-dormants : β=0 → 8/38 · β=0.9 → 38/38
  complétude P1@T3 | pureté @Q8+T1 :  inerte 44|87 · porte 12|8 · axe 58|0 · axe_retr 29|3

Lance :  python tests/bancs/banc_ariane.py
"""

import os
import sys
from datetime import timedelta

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)                                  # racine : pour `import memoire`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # ce dossier : fixtures de banc
os.chdir(_RACINE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config as bench_config                                # fixture : MONDE_DEBUT, etc.
import ariane_monde as A                                     # fixture : monde + vérité-terrain
from embeddings import encoder_un                            # MÊME modèle d'embedding que le proto
from memoire.coeur.graphe import GrapheMemoire, norm_nom     # graphe de la BIBLIOTHÈQUE
from memoire.coeur.lecture import reconnaissance             # reconnaissance de la BIBLIOTHÈQUE
from memoire.options.importance import calculer as importance_calculer
from memoire import config

SEED = 42
HORIZON_MOIS = 24
K = 10
BONUS_RECONNAISSANCE = 5.0
REF = {"P1_b0": (8, 38), "P1_b09": (38, 38),
       "inerte": (44, 87), "porte": (12, 8), "axe": (58, 0), "axe_retr": (29, 3)}


def construire(entites, faits):
    g = GrapheMemoire(encoder_un)                            # ← embed INJECTÉ
    debut = bench_config.MONDE_DEBUT
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
    importance_calculer(g)
    return g, objs


def ranking(g, q, mode, qtok, v):
    reconnu = {f.id for f in reconnaissance(g, q["libelle"])} if mode != "inerte" else set()
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


def moy(L):
    return 100.0 * sum(L) / len(L) if L else 0.0


def main():
    print("=" * 92)
    print(f" NON-RÉGRESSION ARIANE (lib) — graine {SEED}, horizon {HORIZON_MOIS} mois, K={K}")
    print("=" * 92)
    entites, faits, questions = A.generer_grand(seed=SEED, n_hubs=8, n_orgs=6)
    nP1 = sum(1 for f in faits if f.profil == "P1")
    g, objs = construire(entites, faits)
    gmap = {gf.id: afid for afid, gf in objs.items()}

    OK = []
    print(f"\n Monde gelé : {len(entites)} entités · {len(faits)} faits (P1={nP1}) · {len(questions)} q.")
    for beta, lbl, ref in [(0.0, "β=0 (porte)", REF["P1_b0"]), (0.9, "β=0.9 (axe)", REF["P1_b09"])]:
        g.recalculer_dormance(beta)
        actifs = sum(1 for af, gf in objs.items()
                     if faits[af - 1].profil == "P1" and gf.statut != "dormant")
        ok = (actifs, nP1) == ref
        OK.append(ok)
        print(f"   {'✅' if ok else '❌'} P1 non-dormants {lbl:<12} {actifs}/{nP1}  (réf {ref[0]}/{ref[1]})")

    MODES = [("inerte", None), ("porte", 0.0), ("axe", 0.9), ("axe_retr", 0.0)]
    res = {m: {"P1T3": [], "purete": []} for m, _ in MODES}
    for mode, beta in MODES:
        if beta is not None:
            g.recalculer_dormance(beta)
        for q in questions:
            qtok = set(norm_nom(q["libelle"]).split())
            v = encoder_un(q["libelle"])
            ranked_g = ranking(g, q, mode, qtok, v)
            ranked = [gmap[x] for x in ranked_g if x in gmap]
            cibles, _ = A.verite(q, faits)
            truth = {f.fid for f in cibles}
            if not truth:
                continue
            t = len(truth)
            recallK = len(truth & set(ranked[:K])) / t
            precT = len(truth & set(ranked[:t])) / t
            if q["type"] == "T3":
                res[mode]["P1T3"].append(recallK)
            if q["type"] in ("T1", "T3b"):
                res[mode]["purete"].append(precT)

    print("\n   complétude P1@T3 | pureté @Q8+T1 :")
    for m, _ in MODES:
        c, p = round(moy(res[m]["P1T3"])), round(moy(res[m]["purete"]))
        rc, rp = REF[m]
        ok = (c == rc and p == rp)
        OK.append(ok)
        print(f"   {'✅' if ok else '❌'} {m:<9} {c:>3} % | {p:>3} %   (réf {rc} | {rp})")

    gain = round(moy(res["axe"]["P1T3"])) - round(moy(res["porte"]["P1T3"]))
    print("\n" + "=" * 92)
    verdict = all(OK)
    print(f" {'✅ IMPORTANCE EN RAPPEL LIBRE : verdict reproduit (porte→axe +%d pts)' % gain if verdict else '❌ DÉRIVE — régression cachée'}"
          f"  ({sum(OK)}/{len(OK)})")
    print("=" * 92)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
