# -*- coding: utf-8 -*-
"""
etape_ariane_2_notation.py — ARIANE · étape 2 : la notation se comporte-t-elle bien ?

On note QUATRE réponses factices (aucun LLM), pour prouver que le scoring fait ce qu'il faut :
  1. PARFAITE            → complétude 1, pureté 1, F 1, statut juste.
  2. VIDE                → complétude 0, F 0 (pureté vide = vacuité).
  3. DÉVERSE-TOUT        → complétude 1 mais pureté basse → F médiocre (anti-hedging).
  4. DÉVERSE-LE-CAPITAL  → remonte les faits importants à TOUTES les questions (même Q8 triviale et
                           Q2 par attribut) : c'est le mode de défaillance de l'axe importance trop
                           agressif. Doit être NETTEMENT pénalisée en pureté.

+ démonstration : sur Q3/Q4, citer Marc AU PRÉSENT = statut FAUX, distinct de l'ABSENCE.

Lance :  python etape_ariane_2_notation.py
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
import ariane_notation as N


def main():
    J = Journal("ariane_2_notation")
    dire = J.dire
    entites, faits, questions = A.generer_mini()

    def statut_attendu(f):
        return "imparfait" if f.statut() == "clos" else "present"

    # ── Les quatre réponses factices ─────────────────────────────────────
    parfaite, vide, deverse_tout, deverse_capital = {}, {}, {}, {}
    capital = [f for f in faits if f.profil in ("P1", "P3")]
    for q in questions:
        cibles, _ = A.verite(q, faits)
        parfaite[q["qid"]] = [(f.fid, statut_attendu(f)) for f in cibles]
        vide[q["qid"]] = []
        deverse_tout[q["qid"]] = [(f.fid, "present") for f in faits]
        deverse_capital[q["qid"]] = [(f.fid, "present") for f in capital]

    REPONSES = [("PARFAITE", parfaite), ("VIDE", vide),
                ("DÉVERSE-TOUT", deverse_tout), ("DÉVERSE-LE-CAPITAL", deverse_capital)]

    dire("=" * 92)
    dire(" ARIANE · ÉTAPE 2 — LA NOTATION SE COMPORTE-T-ELLE BIEN ? (4 réponses factices)")
    dire("=" * 92)
    dire(f"\n   {'Réponse':<20} {'Complétude':>11} {'Pureté':>9} {'F-mesure':>9} {'Statut faux':>12}")
    aggs = {}
    for nom, rep in REPONSES:
        agg, _ = N.noter_banc(rep, questions, faits)
        aggs[nom] = agg
        dire(f"   {nom:<20} {agg['completude']:>10.0%} {agg['purete']:>9.0%} "
             f"{agg['f_mesure']:>9.0%} {agg['statut_faux']:>12}")

    # ── Détail de DÉVERSE-LE-CAPITAL (où la pureté s'effondre) ───────────
    dire("\n— DÉTAIL « DÉVERSE-LE-CAPITAL » par question (la pureté doit chuter hors T3) —")
    _, lignes = N.noter_banc(deverse_capital, questions, faits)
    dire(f"   {'Q':<4} {'type':<5} {'compl.':>7} {'pureté':>7}  (pertinents/remontés)")
    for r in lignes:
        dire(f"   {r['qid']:<4} {r['type']:<5} {r['completude']:>6.0%} {r['purete']:>7.0%}"
             f"  ({r['pert']}/{r['ret']})")
    dire("   → Sur Q1/Q2/Q8 (où la vérité n'est PAS capitale) : pureté 0 % — le banc attrape bien")
    dire("     le déversement de capital hors-sujet. C'est le garde-fou contre l'importance trop agressive.")

    # ── Démonstration : statut de Marc sur Q3 (présent = faux ≠ absence) ──
    dire("\n— STATUT DE MARC (Q3) : présent = FAUX, imparfait = juste, absence = ni l'un ni l'autre —")
    q3 = next(q for q in questions if q["qid"] == "Q3")
    cas = {
        "Marc cité au PRÉSENT": [(6, "present")],
        "Marc cité à l'IMPARFAIT": [(6, "imparfait")],
        "Marc ABSENT (omis)": [],
    }
    for libelle, rep in cas.items():
        r = N.noter(rep, q3, faits)
        verdict = ("statut FAUX" if r["statut_faux"] else
                   ("statut juste" if r["statut_ok"] else "pas d'erreur de statut (perte de complétude)"))
        dire(f"   {libelle:<28} → statut_faux={r['statut_faux']} statut_ok={r['statut_ok']} "
             f"compl={r['completude']:.0%}  ⇒ {verdict}")

    # ── Vérifications ────────────────────────────────────────────────────
    dire("\n" + "=" * 92)
    dire(" VÉRIFICATIONS")
    dire("=" * 92)
    ok = []

    def chk(c, label):
        ok.append(c)
        dire(f"   {'✅' if c else '❌'} {label}")

    chk(aggs["PARFAITE"]["f_mesure"] > 0.99 and aggs["PARFAITE"]["statut_faux"] == 0,
        "PARFAITE : F-mesure ≈ 100 %, 0 statut faux")
    chk(aggs["VIDE"]["completude"] < 0.01 and aggs["VIDE"]["f_mesure"] < 0.01,
        "VIDE : complétude et F-mesure ≈ 0")
    chk(aggs["DÉVERSE-TOUT"]["completude"] > 0.9 and aggs["DÉVERSE-TOUT"]["purete"] < 0.4,
        "DÉVERSE-TOUT : complétude haute MAIS pureté basse (anti-hedging)")
    chk(aggs["DÉVERSE-LE-CAPITAL"]["purete"] < aggs["PARFAITE"]["purete"]
        and aggs["DÉVERSE-LE-CAPITAL"]["statut_faux"] > 0,
        "DÉVERSE-LE-CAPITAL : nettement pénalisée en pureté + statut faux (capital servi partout)")
    chk(N.noter([(6, "present")], q3, faits)["statut_faux"] == 1
        and N.noter([], q3, faits)["statut_faux"] == 0,
        "Marc au présent = 1 statut faux ; Marc absent = 0 statut faux (distinct)")

    dire("\n" + "=" * 92)
    dire(f" {'✅ Notation validée' if all(ok) else '❌ À revoir'}. Journal : {J.chemin}")
    dire("=" * 92)
    J.fermer()


if __name__ == "__main__":
    main()
