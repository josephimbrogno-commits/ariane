# -*- coding: utf-8 -*-
"""
etape_structure_2.py — TYPOLOGIE · étape 2 : prédicteur + matrice de confusion + ablation.

Sur le mini-monde : précision globale (contexte), puis LE VERDICT sur les cas-pièges, et l'ablation
S1 / S2 / S1+S2 — en montrant en plus que la HIÉRARCHIE interne de S2 (date d'abord) sauve P-B/P-C,
et que le contre-exemple C-E (date de DÉBUT) n'est bien classé que si on distingue occurrence/début.

Lance :  python etape_structure_2.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from util import Journal
import structure_monde as S
from structure_predicteur import predire


def main():
    J = Journal("structure_2")
    dire = J.dire
    entites, liens = S.generer_mini()
    deg = S.degres(liens)
    primaires = [l for l in liens if l.primaire]

    dire("=" * 100)
    dire(" TYPOLOGIE DES LIENS · ÉTAPE 2 — prédicteur structurel + matrice de confusion + ablation")
    dire("=" * 100)

    # ── Précision globale par mode (contexte, PAS le verdict) ────────────
    dire("\n— PRÉCISION GLOBALE par mode (contexte) —")
    modes_ctx = ["S1", "S2", "S1S2"]
    for m in modes_ctx:
        ok = sum(1 for l in primaires if predire(S.features(l, liens, deg), m) == l.nature)
        dire(f"   {m:<6} : {ok}/{len(primaires)} bien classés")

    # ── LE VERDICT : cas-pièges + contre-exemple ─────────────────────────
    dire("\n" + "=" * 100)
    dire(" LE VERDICT — prédiction sur les CAS-PIÈGES (et le contre-exemple), par mode")
    dire("=" * 100)
    pieges = [l for l in primaires if l.piege]
    dire(f"   {'cas':<5} {'lien':<30} {'vérité':<9} | {'S1':<9} {'S2':<9} {'S1+S2':<9}")
    score = {m: 0 for m in modes_ctx}
    for l in sorted(pieges, key=lambda x: x.piege):
        f = S.features(l, liens, deg)
        preds = {m: predire(f, m) for m in modes_ctx}
        cells = []
        for m in modes_ctx:
            bon = preds[m] == l.nature
            score[m] += 1 if bon else 0
            cells.append(("✓" if bon else "✗") + preds[m][:7])
        dire(f"   {l.piege:<5} {l.sujet+'→'+l.objet:<30} {l.nature:<9} | "
             f"{cells[0]:<9} {cells[1]:<9} {cells[2]:<9}")
    n = len(pieges)
    dire(f"\n   SCORE cas-pièges : S1 {score['S1']}/{n} · S2 {score['S2']}/{n} · S1+S2 {score['S1S2']}/{n}")
    dire("   → S1 (connectivité seule) échoue les pièges ; S2 (forme temporelle + réciprocité) les récupère.")

    # ── La hiérarchie interne de S2 : date d'abord (P-B) ─────────────────
    dire("\n— LA HIÉRARCHIE DE S2 : « date d'abord » sauve P-B (réciprocité confondue) —")
    pb = next(l for l in primaires if l.piege == "P-B")
    fpb = S.features(pb, liens, deg)
    dire(f"   P-B « {pb.sujet}→{pb.objet} » : réciproque={fpb['reciproque']}, occurrence={fpb['est_occurrence']}, vérité={pb.nature}")
    dire(f"      réciprocité AVANT date  → {predire(fpb,'S2_recip_first')}  "
         f"{'✗ FAUX' if predire(fpb,'S2_recip_first')!=pb.nature else '✓'}")
    dire(f"      date AVANT réciprocité  → {predire(fpb,'S2')}  "
         f"{'✓ JUSTE' if predire(fpb,'S2')==pb.nature else '✗'}")

    # ── Le contre-exemple : date de DÉBUT ≠ occurrence (C-E) ─────────────
    dire("\n— LE CONTRE-EXEMPLE C-E : « marié DEPUIS 2015 » (date de début, pas occurrence) —")
    ce = next(l for l in primaires if l.piege == "C-E")
    fce = S.features(ce, liens, deg)
    dire(f"   C-E « {ce.sujet}→{ce.objet} » : porte_date={fce['porte_date']}, occurrence={fce['est_occurrence']}, vérité={ce.nature}")
    dire(f"      « porte une date » (naïf) → {predire(fce,'S2_naif_date')}  "
         f"{'✗ FAUX (date de début prise pour occurrence)' if predire(fce,'S2_naif_date')!=ce.nature else '✓'}")
    dire(f"      « occurrence ponctuelle » → {predire(fce,'S2')}  "
         f"{'✓ JUSTE (distingue début/occurrence)' if predire(fce,'S2')==ce.nature else '✗'}")

    # ── Faux-amis (où la structure se trompe, hors pièges) ──────────────
    dire("\n— FAUX-AMIS sous S1+S2 (structure insuffisante, hors cas-pièges) —")
    fa = [l for l in primaires if not l.piege and predire(S.features(l, liens, deg), "S1S2") != l.nature]
    if not fa:
        dire("   (aucun)")
    for l in fa:
        f = S.features(l, liens, deg)
        dire(f"   ✗ {l.sujet} —{l.predicat}→ {l.objet} : vérité {l.nature}, prédit "
             f"{predire(f,'S1S2')} (degrés {f['deg_sujet']}/{f['deg_objet']}, récip={f['reciproque']}, "
             f"occ={f['est_occurrence']}) → durable ASYMÉTRIQUE non daté : la structure ne le voit pas.")

    # ── Vérifications ────────────────────────────────────────────────────
    dire("\n" + "=" * 100)
    dire(" VÉRIFICATIONS")
    dire("=" * 100)
    chk = []

    def ok(c, label):
        chk.append(c)
        dire(f"   {'✅' if c else '❌'} {label}")

    ok(score["S1"] == 0, f"S1 (connectivité) échoue TOUS les cas-pièges ({score['S1']}/{n})")
    ok(score["S2"] >= n, f"S2 (date + réciprocité) récupère tous les cas-pièges ({score['S2']}/{n})")
    ok(predire(fpb, "S2_recip_first") != pb.nature and predire(fpb, "S2") == pb.nature,
       "Hiérarchie : date-d'abord sauve P-B, réciprocité-d'abord le rate")
    ok(predire(fce, "S2_naif_date") != ce.nature and predire(fce, "S2") == ce.nature,
       "C-E : distinguer occurrence/début est nécessaire (sinon date de début = faux signal)")
    ok(len(fa) > 0, f"Faux-amis exposés : {len(fa)} durable(s) asymétrique(s) non daté(s) → "
       "une petite part de déclaration reste nécessaire")

    dire("\n" + "=" * 100)
    dire(f" {'✅ Étape 2 validée' if all(chk) else '❌ À revoir'}. Journal : {J.chemin}")
    dire("=" * 100)
    J.fermer()


if __name__ == "__main__":
    main()
