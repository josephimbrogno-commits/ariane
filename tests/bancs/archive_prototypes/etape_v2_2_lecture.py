# -*- coding: utf-8 -*-
"""
etape_v2_2_lecture.py — MICRO-TEST DE LECTURE (V2, étape de construction 2).

Base taillée pour exercer la lecture : entrée vectorielle (pondérée Force) + marche de graphe
+ rendu épistémique verbal. Dates étalées pour produire un fait COURANT ÉRODÉ et un fait DORMANT.

10 questions, dont les 4 demandées :
 (1) fait courant érodé      → réponse AVEC RÉSERVE (pas un refus)
 (2) disputé Lyon/Brest      → les DEUX valeurs avec sources
 (3) question à 1 saut       → PDG → personne → conjoint
 (4) fait DORMANT via marche → métier de l'épouse du PDG (dormant réveillé par la marche)
+ une question sur un fait CLOS (attendu : imparfait) et une question sans réponse (refus légitime).

Pour CHAQUE question, on affiche le CHEMIN de récupération (entrée vectorielle vs marche).

Lance :  python etape_v2_2_lecture.py
"""

import os
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
from util import Journal
from v2_modele import GrapheMemoire, norm_nom, norm_valeur
import v2_lecture


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


LECTURE = d("2026-12-15")   # « maintenant » au moment des questions

# Base : (sujet, predicat, objet, source, date_obs, validite)
BASE = [
    ("Nexora", "pdg_de", "Mme Karel", "Gazette", "2026-01-10", None),
    ("Nexora", "pdg_de", "M. Doss", "Officiel", "2026-11-20", "2026-11"),     # clôture Karel
    ("Nexora", "pdg_de", "M. Doss", "Presse", "2026-11-25", None),            # corrobore Doss
    ("M. Doss", "marie_a", "Mme Lefort", "Presse", "2026-11-10", None),       # lien graphe
    ("Mme Lefort", "profession_de", "avocate", "Annuaire", "2025-06-01", None),  # → DORMANT
    ("Veltis", "siege_de", "Lyon", "Gazette", "2026-10-05", None),
    ("Veltis", "siege_de", "Brest", "BlogX", "2026-10-20", None),             # → DISPUTÉ
    ("M. Dupont", "marie_a", "Mme Sora", "Gazette", "2026-06-01", None),      # → érodé (réserve)
    ("Veltis", "date_fondation_de", "1998", "Gazette", "2026-01-03", "1998"),
    ("Veltis", "date_fondation_de", "1998", "Almanach", "2026-02-01", "1998"),  # immuable corroboré
    ("Veltis", "produit", "des panneaux solaires", "Gazette", "2026-09-01", None),
    ("Veltis", "produit", "des batteries", "Gazette", "2026-09-02", None),
    ("Nexora", "effectif_de", "520", "Officiel", "2026-11-01", None),
]

QUESTIONS = [
    ("Qui dirige actuellement l'entreprise Nexora ?",        "ACTUEL sûr → présent (Doss)"),
    ("Qui dirigeait Nexora au début de l'année 2026 ?",      "CLOS → imparfait (Karel jusqu'en 2026-11)"),
    ("Où se trouve le siège de Veltis ?",                    "(2) DISPUTÉ → Lyon ET Brest avec sources"),
    ("Avec qui M. Dupont est-il marié ?",                    "(1) érodé → réserve, PAS un refus (Sora)"),
    ("Quelle entreprise est dirigée par le mari de Mme Lefort ?", "(3) 1 saut : Lefort→mari Doss→dirige (Nexora)"),
    ("Quel métier exerce l'épouse du PDG de Nexora ?",       "(4) DORMANT via marche (avocate)"),
    ("En quelle année l'entreprise Veltis a-t-elle été fondée ?", "IMMUABLE → présent (1998)"),
    ("Que fabrique l'entreprise Veltis ?",                   "MULTI-VALUÉ (panneaux + batteries)"),
    ("Combien de personnes Nexora emploie-t-elle ?",         "ACTUEL incertain → réserve (520)"),
    ("Qui est le maire de la ville de Sève ?",               "ABSENT → refus légitime"),
]


def ent(g, nom):
    for e in g.entites.values():
        if norm_nom(nom) in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
            return e
    return None


def label(g, f):
    return f"#{f.id} {f.predicat}({g.nom_entite(f.sujet_id)})={f.objet}[{f.statut}]"


def main():
    J = Journal("etape_v2_2_lecture")
    dire = J.dire
    dire("=" * 96)
    dire(" V2 · ÉTAPE 2 — MICRO-TEST DE LECTURE (entrée vectorielle + marche de graphe + rendu épistémique)")
    dire("=" * 96)

    def construire():
        """État FRAIS à chaque question (pas de fuite d'accès/réveil d'une question à l'autre)."""
        g = GrapheMemoire()
        for (su, pr, ob, src, dt, va) in BASE:
            g.ingerer(su, pr, ob, source_id=src, date_obs=d(dt), date_validite=va)
        g.appliquer_decroissances(LECTURE)
        return g

    g0 = construire()
    dormants = [f for f in g0.faits.values() if f.statut == "dormant"]
    dire(f"\n État initial : {len(g0.entites)} entités, {len(g0.faits)} faits. "
         f"Dormants (exclus de l'entrée vectorielle) : {[label(g0,f) for f in dormants]}")
    dire(" (état reconstruit à neuf pour CHAQUE question — entrée vectorielle limitée à k=3 "
         "pour laisser la marche travailler)\n")

    resultats = []
    for n, (q, attendu) in enumerate(QUESTIONS, start=1):
        g = construire()
        r = v2_lecture.lire(g, q, LECTURE, k=3)
        dire("─" * 96)
        dire(f"[{n:2}] « {q} »")
        dire(f"     attendu : {attendu}")
        ent_ids = [f for f in r["injectes"] if r["chemin"][f.id] == "entrée vectorielle"]
        mar_ids = [f for f in r["injectes"] if r["chemin"][f.id] == "marche de graphe"]
        dire(f"     CHEMIN ▸ entrée vectorielle : {[label(g,f) for f in ent_ids] or '—'}")
        dire(f"            ▸ marche de graphe    : {[label(g,f) for f in mar_ids] or '—'}")
        if r["reveils"]:
            dire(f"            ▸ ☼ RÉVEIL de dormant par la marche : #{r['reveils']}")
        dire("     souvenirs injectés (rendu épistémique) :")
        for ligne in r["bloc"].split("\n"):
            dire(f"        {ligne}")
        dire(f"     RÉPONSE : « {r['reponse']} »")
        resultats.append((q, attendu, r))

    # ── VÉRIFICATIONS ────────────────────────────────────────────────────
    dire("\n" + "=" * 96)
    dire(" VÉRIFICATIONS (les 4 questions ajoutées + clos + présent)")
    dire("=" * 96)

    def rep(i):
        return resultats[i][2]["reponse"].lower()

    def via_marche(i, nom_obj=None, predicat=None):
        r = resultats[i][2]
        for f in r["injectes"]:
            if r["chemin"][f.id] != "marche de graphe":
                continue
            if nom_obj and nom_obj not in norm_valeur(f.objet):
                continue
            if predicat and f.predicat != predicat:
                continue
            return True
        return False

    def ok(cond, label_):
        dire(f"   {'✅' if cond else '❌'} {label_}")

    refus = lambda s: any(m in s for m in ["pas d'info", "ne dispose", "aucun", "pas trouv",
                                           "ne sais", "souvenir concernant", "ne peux pas"])
    ok(("doss" in rep(0)) and not refus(rep(0)), "ACTUEL sûr : « Doss » affirmé au présent")
    ok(("karel" in rep(1)) and ("etait" in norm_valeur(rep(1))),
       "CLOS : Karel rendu à l'IMPARFAIT (« était »)")
    ok(("lyon" in rep(2)) and ("brest" in rep(2)), "(2) DISPUTÉ : les DEUX valeurs (Lyon ET Brest)")
    ok(("sora" in rep(3)) and not refus(rep(3)), "(1) ÉRODÉ : réponse avec réserve (Sora), pas un refus")
    ok(("nexora" in rep(4)) and via_marche(4, predicat="pdg_de"),
       "(3) 1 SAUT : « dirige Nexora » atteint par la MARCHE de graphe (Lefort→Doss→pdg)")
    ok(("avocat" in rep(5)) and (len(resultats[5][2]["reveils"]) > 0 or via_marche(5, nom_obj="avocate")),
       "(4) DORMANT : métier (avocate) atteint par la marche + réveil du dormant")
    ok("1998" in rep(6), "IMMUABLE : fondation 1998 au présent")
    ok(refus(rep(9)), "ABSENT : refus légitime (aucun fait sur Sève)")

    dire("\n" + "=" * 96)
    dire(f" ✅ Micro-test de lecture terminé. Journal : {J.chemin}")
    dire("=" * 96)
    J.fermer()


if __name__ == "__main__":
    main()
