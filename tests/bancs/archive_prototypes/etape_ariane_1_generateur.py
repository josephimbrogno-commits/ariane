# -*- coding: utf-8 -*-
"""
etape_ariane_1_generateur.py — ARIANE · étape 1 : générateur + vérité-terrain (mini-monde).

Affiche le mini-monde (faits étiquetés par profil) et, pour CHAQUE question de rappel libre, la
LISTE-VÉRITÉ attendue (calculée mécaniquement). But : vérifier À LA MAIN que ces listes sont
correctes — tout le banc en dépend. Aucun LLM, aucune config, aucun score ici.

Lance :  python etape_ariane_1_generateur.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from util import Journal
import ariane_monde as A


def main():
    J = Journal("ariane_1_generateur")
    dire = J.dire
    entites, faits, questions = A.generer_mini()

    dire("=" * 92)
    dire(" ARIANE · ÉTAPE 1 — GÉNÉRATEUR + VÉRITÉ-TERRAIN (mini-monde, vérification à la main)")
    dire(f"   {len(entites)} entités · {len(faits)} faits · {len(questions)} questions · horizon {A.HORIZON} mois")
    dire("=" * 92)

    # ── Profils ──────────────────────────────────────────────────────────
    prof = {}
    for f in faits:
        prof.setdefault(f.profil, []).append(f)
    dire("\n— RÉPARTITION PAR PROFIL —")
    libelles = {"P1": "Capital & jamais consulté (CIBLE de l'importance)",
                "P2": "Trivial & récent (distracteur)",
                "P3": "Capital & PÉRIMÉ (piège : imparfait only)",
                "P4": "Moyen (bruit)"}
    for p in ("P1", "P2", "P3", "P4"):
        dire(f"   {p} ({len(prof.get(p, []))}) — {libelles[p]}")

    # ── Faits ────────────────────────────────────────────────────────────
    dire("\n— FAITS (état final à l'horizon) —")
    dire(f"   {'#':>2} {'profil':<6} {'statut':<8} {'accès':<6} fait")
    for f in faits:
        val = f"{f.mois_de}→{f.mois_jusqua if f.mois_jusqua is not None else '…'}"
        acc = f"{f.acces}{'↑' if f.acces_recents else ''}"
        dire(f"   {f.fid:>2} {f.profil:<6} {f.statut():<8} {acc:<6} "
             f"{f.predicat}({f.sujet})={f.objet}  [{val}]")

    # ── Listes-vérité par question ───────────────────────────────────────
    dire("\n" + "=" * 92)
    dire(" LISTES-VÉRITÉ PAR QUESTION (ce qui DOIT remonter — à vérifier à la main)")
    dire("=" * 92)
    for q in questions:
        cibles, perimes = A.verite(q, faits)
        dire(f"\n  [{q['qid']} · {q['type']}] « {q['libelle']} »")
        if not cibles:
            dire("     vérité : (aucun fait attendu)")
        for f in cibles:
            tag = "À L'IMPARFAIT" if f.statut() == "clos" else "au présent"
            dire(f"     ✓ #{f.fid} {f.predicat}({f.sujet})={f.objet}  [{f.profil}] → {tag}")
        if perimes:
            for f in perimes:
                dire(f"     ⓘ périmé (NE doit PAS être servi comme courant) : "
                     f"#{f.fid} {f.predicat}({f.sujet})={f.objet}  [{f.profil}]")

    # ── Le cœur du test : les P1 jamais consultés ───────────────────────
    dire("\n" + "=" * 92)
    dire(" L'ENJEU EN UNE LIGNE")
    dire("=" * 92)
    p1 = prof.get("P1", [])
    dire(f"   {len(p1)} faits P1 (capitaux, 0 accès → Force basse à l'horizon). Questions T3 (Q5-Q7) "
         f"les évoquent SANS nommer l'entité.")
    dire("   → Sans l'axe importance : endormis, muets, introuvables (entité non nommée → pas de porte).")
    dire("   → Avec l'axe importance : survivent (dormance modulée) et remontent (saillance).")
    dire("   C'est CE gain (complétude P1) sans effondrement de pureté (distracteurs P2) que l'étape 3 mesure.")
    dire("\n" + "=" * 92)
    dire(f" ✅ Générateur affiché. Journal : {J.chemin}")
    dire("=" * 92)
    J.fermer()


if __name__ == "__main__":
    main()
