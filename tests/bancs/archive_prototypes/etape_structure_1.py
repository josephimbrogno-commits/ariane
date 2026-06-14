# -*- coding: utf-8 -*-
"""
etape_structure_1.py — TYPOLOGIE DES LIENS · étape 1 : générateur + vérité-terrain (mini-monde).

Affiche chaque lien primaire avec ses features structurelles (degrés, réciprocité, date unique) ET
sa vraie nature. VÉRIFIE À LA MAIN que les CAS-PIÈGES sont bien des pièges : la connectivité seule
(S1) y pointe la MAUVAISE réponse. Aucun prédicteur ici, juste la vérité-terrain à valider.

Lance :  python etape_structure_1.py
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


def s1_naif(feat):
    """Ce que dirait la CONNECTIVITÉ SEULE : durable si aucun bout n'est cul-de-sac, sinon éphémère."""
    return S.DURABLE if min(feat["deg_sujet"], feat["deg_objet"]) >= 2 else S.EPHEMERE


def main():
    J = Journal("structure_1")
    dire = J.dire
    entites, liens = S.generer_mini()
    deg = S.degres(liens)
    primaires = [l for l in liens if l.primaire]

    dire("=" * 98)
    dire(" TYPOLOGIE DES LIENS · ÉTAPE 1 — VÉRITÉ-TERRAIN (mini-monde, vérification à la main)")
    dire(f"   {len(entites)} entités · {len(primaires)} liens primaires "
         f"(+{len(liens)-len(primaires)} inverses auxiliaires) · 4 cas-pièges")
    dire("=" * 98)

    dire("\n— DEGRÉS (nb de voisins distincts) —")
    dire("   " + " · ".join(f"{e}:{deg[e]}" for e in sorted(entites, key=lambda x: -deg[x])))

    dire("\n— LIENS PRIMAIRES (features structurelles + vérité) —")
    dire(f"   {'lien':<34} {'dS':>3} {'dO':>3} {'récip':>6} {'daté':>5} {'NATURE':<9} {'piège':<5} {'S1 naïf':<9}")
    for l in primaires:
        f = S.features(l, liens, deg)
        s1 = s1_naif(f)
        marque = "✗" if (l.piege and s1 != l.nature) else (" " if not l.piege else "?")
        dire(f"   {l.sujet+' —'+l.predicat+'→ '+l.objet:<34} "
             f"{f['deg_sujet']:>3} {f['deg_objet']:>3} {'oui' if f['reciproque'] else 'non':>6} "
             f"{'oui' if f['date_unique'] else 'non':>5} {l.nature:<9} {l.piege:<5} {s1:<9} {marque}")

    # ── Vérification : les pièges trompent-ils bien S1 ? ─────────────────
    dire("\n" + "=" * 98)
    dire(" VÉRIFICATION — les cas-pièges cassent-ils la corrélation facile connectivité↔nature ?")
    dire("=" * 98)
    pieges = {l.piege: l for l in primaires if l.piege}
    descr = {
        "P-A": "DURABLE vers cul-de-sac (frère isolé) — S1 dit éphémère À TORT ; S2 (réciprocité) doit sauver",
        "P-B": "ÉPHÉMÈRE touchant un carrefour (a mangé avec Maman) — S1 dit durable À TORT ; S2 (daté) doit rabaisser",
        "P-C": "ÉPHÉMÈRE entre deux connectés — S1 dit durable À TORT ; seule la forme temporelle sauve",
        "P-D": "DURABLE entre deux isolés — ni S1 ni richesse n'aident ; seule la réciprocité S2 sauve",
    }
    tous_pieges_ok = True
    for fam in ("P-A", "P-B", "P-C", "P-D"):
        l = pieges.get(fam)
        f = S.features(l, liens, deg)
        s1 = s1_naif(f)
        trompe = (s1 != l.nature)
        tous_pieges_ok = tous_pieges_ok and trompe
        dire(f"\n   [{fam}] {l.sujet} —{l.predicat}→ {l.objet}")
        dire(f"        {descr[fam]}")
        dire(f"        structure : degrés {f['deg_sujet']}/{f['deg_objet']}, "
             f"réciproque={'oui' if f['reciproque'] else 'non'}, daté={'oui' if f['date_unique'] else 'non'}")
        dire(f"        vérité = {l.nature} | S1 naïf = {s1} → "
             f"{'✗ S1 SE TROMPE (bon piège)' if trompe else '⚠ S1 a raison (pas un vrai piège !)'}")

    dire("\n" + "=" * 98)
    dire(f"   {'✅' if tous_pieges_ok else '❌'} Les 4 cas-pièges trompent bien la connectivité seule "
         f"(S1) → la corrélation facile est CASSÉE. Le banc est honnête.")
    dire("   → L'étape 2 testera si la STRUCTURE (S1+S2) récupère ces pièges que S1 seul rate.")
    dire("=" * 98)
    dire(f" Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
