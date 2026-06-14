# -*- coding: utf-8 -*-
"""
etape_v3_2_dormance.py — MICRO-TEST V3 · étape 2 : dormance modulée + reconnaissance/rappel.

A) Cas canonique proche/repas : à Force ÉGALE et basse, le fait CAPITAL (nom du proche) SURVIT
   tandis que le fait TRIVIAL (repas) s'efface — l'importance module le seuil de dormance.
B) Reconnaissance / rappel : un fait DORMANT redevient lisible dès que la question NOMME son entité
   (la dormance ne bloque que l'évocation libre, jamais la reconnaissance directe).
C) Cas ajouté : un fait à importance MAXIMALE, contredit par une info nouvelle, est CLOS normalement
   et rendu à l'imparfait — l'importance protège de l'OUBLI, jamais de la CONTRADICTION.

Pas d'appel LLM. Lance :  python etape_v3_2_dormance.py
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
import v3_importance
import v2_lecture
from util import Journal
from v2_modele import GrapheMemoire, norm_nom, norm_valeur

D0 = datetime(2026, 1, 1)
FAITS = [
    ("ma mère", "nom_de", "Marie", "état civil"),
    ("ma mère", "nom_de", "Marie", "carnet"),
    ("ma mère", "marie_a", "mon père", "famille"),
    ("ma mère", "marie_a", "mon père", "mairie"),
    ("ma mère", "parent_de", "moi", "famille"),
    ("ma mère", "parent_de", "ma sœur", "famille"),
    ("grand-mère", "parent_de", "ma mère", "famille"),
    ("ma mère", "connait", "grand-mère", "famille"),
    ("ma mère", "profession_de", "médecin", "ordre"),
    ("ma mère", "repas_de", "des pâtes", "moi"),
    ("grand-mère", "profession_de", "couturière", "souvenir"),
]
TYPES = {n: "personne" for n in ["ma mère", "mon père", "moi", "ma sœur", "grand-mère"]}


def ent(g, nom):
    for e in g.entites.values():
        if norm_nom(nom) in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
            return e
    return None


def fait(g, pred, sujet, obj=None):
    e = ent(g, sujet)
    for f in g.faits.values():
        if f.predicat == pred and f.sujet_id == e.id and (obj is None or obj in norm_valeur(f.objet)):
            return f
    return None


def main():
    J = Journal("etape_v3_2_dormance")
    dire = J.dire
    dire("=" * 90)
    dire(" V3 · ÉTAPE 2 — DORMANCE MODULÉE PAR L'IMPORTANCE + RECONNAISSANCE/RAPPEL")
    dire(f"   seuil_dormance = {config.V2_FORCE_SEUIL_DORMANT} × (1 − {config.IMP_BETA}·importance)")
    dire("=" * 90)

    g = GrapheMemoire()
    for (su, pr, ob, src) in FAITS:
        g.ingerer(su, pr, ob, source_id=src, date_obs=D0)
    for nom, typ in TYPES.items():
        e = ent(g, nom)
        if e:
            e.type = typ
    v3_importance.calculer(g)

    f_nom = fait(g, "nom_de", "ma mère")
    f_repas = fait(g, "repas_de", "ma mère")
    f_gm = fait(g, "profession_de", "grand-mère")

    def ligne(f, label):
        s = g._seuil_dormance(f)
        return (f"   {label:22} imp={f.importance:.2f}  Force={f.force:.2f}  "
                f"seuil={s:.3f}  → [{f.statut}]")

    # ── A) Dormance modulée : proche vs repas ────────────────────────────
    dire("\n— A) CAS CANONIQUE : à Force basse, le CAPITAL survit, le TRIVIAL s'efface —")
    f_nom.force, f_repas.force = 0.05, 0.60            # « aujourd'hui » : le repas est plus frais !
    g._appliquer_dormance()
    dire("  Aujourd'hui (le repas a une Force PLUS HAUTE que le nom du proche) :")
    dire(ligne(f_nom, "nom de ma mère"))
    dire(ligne(f_repas, "repas de ma mère"))
    f_repas.force = 0.05                               # quelques mois plus tard : le repas a décliné
    g._appliquer_dormance()
    dire("  Quelques mois plus tard (les deux Forces sont basses, 0.05) :")
    dire(ligne(f_nom, "nom de ma mère"))
    dire(ligne(f_repas, "repas de ma mère"))
    a_ok = f_nom.statut != "dormant" and f_repas.statut == "dormant"
    dire(f"\n   {'✅' if a_ok else '❌'} INVERSION RÉPARÉE : à Force égale (0.05), le nom du proche "
         f"SURVIT [{f_nom.statut}] et le repas s'efface [{f_repas.statut}].")

    # ── B) Reconnaissance / rappel ───────────────────────────────────────
    dire("\n— B) RECONNAISSANCE / RAPPEL : un fait dormant redevient lisible si on NOMME l'entité —")
    f_gm.force = 0.05
    g._appliquer_dormance()
    dire(f"   « {f_gm.predicat}(grand-mère)=couturière » : imp={f_gm.importance:.2f} "
         f"Force={f_gm.force:.2f} → [{f_gm.statut}]")
    q = "Quel est le métier de grand-mère ?"
    par_evocation = [x.id for x, _ in [(f, 0) for f in v2_lecture.entree_vectorielle(g, q)[0]]]
    par_reco = [x.id for x in v2_lecture.reconnaissance(g, q)]
    dire(f"   Question : « {q} »")
    dire(f"   ▸ évocation libre (similarité, dormants exclus) : fait #{f_gm.id} présent ? "
         f"{'oui' if f_gm.id in par_evocation else 'NON'}")
    dire(f"   ▸ reconnaissance (la question nomme « grand-mère ») : fait #{f_gm.id} présent ? "
         f"{'OUI' if f_gm.id in par_reco else 'non'}")
    b_ok = (f_gm.id not in par_evocation) and (f_gm.id in par_reco)
    dire(f"   {'✅' if b_ok else '❌'} La dormance bloque l'évocation libre mais PAS la reconnaissance "
         f"directe (le fait muet redevient lisible).")

    # ── C) Cas ajouté : le CAPITAL contredit est CLOS, pas protégé ───────
    dire("\n— C) IMPORTANCE ≠ PROTECTION CONTRE LA CONTRADICTION —")
    f_marie = fait(g, "marie_a", "ma mère")
    dire(f"   Avant : {g.fait_court(f_marie)}")
    # une info nouvelle, datée et indépendante : remariage
    g.ingerer("ma mère", "marie_a", "M. Nouveau", source_id="annonce",
              date_obs=datetime(2026, 5, 1), date_validite="2026-05")
    v3_importance.calculer(g)                          # l'importance reste haute
    dire(f"   Après contradiction datée (remariage) :")
    dire(f"     {g.fait_court(f_marie)}")
    rendu = v2_lecture.rendu_epistemique(g, [f_marie])
    dire(f"     rendu épistémique : {rendu}")
    c_ok = (f_marie.statut == "clos" and f_marie.importance > 0.5
            and "etait" in norm_valeur(rendu))
    dire(f"   {'✅' if c_ok else '❌'} Le fait CAPITAL (imp={f_marie.importance:.2f}) est CLOS et rendu "
         f"à l'imparfait — l'importance protège de l'oubli, jamais de la contradiction.")

    dire("\n" + "=" * 90)
    dire(f" Bilan : A {'✅' if a_ok else '❌'} | B {'✅' if b_ok else '❌'} | C {'✅' if c_ok else '❌'}")
    dire(f" Micro-test terminé. Journal : {J.chemin}")
    dire("=" * 90)
    J.fermer()


if __name__ == "__main__":
    main()
