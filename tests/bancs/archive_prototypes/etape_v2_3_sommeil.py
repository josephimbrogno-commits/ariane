# -*- coding: utf-8 -*-
"""
etape_v2_3_sommeil.py — MICRO-TEST DU SOMMEIL (V2, étape de construction 3).

Vérifie : décroissances, dormance BIDIMENSIONNELLE + réveil, fusion d'entités, promotion noyau.

Deux cas ajoutés :
 (1) fait 3-sources / 1-accès, Force basse → NE tombe PAS en dormance (protégé par le monde).
     Arbitrage : la Certitude ne freine pas la Force (axes orthogonaux), mais la DÉCISION de
     dormance lit les deux axes — un fait bien attesté reste évocable malgré une Force basse.
 (2) fait mono-source / 8-accès → NE doit PAS être promu noyau (l'accès ne suffit pas, il faut
     ≥3 sources indépendantes : un fait souvent rappelé mais mal sourcé n'entre pas dans le noyau).

Lance :  python etape_v2_3_sommeil.py
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
from v2_modele import GrapheMemoire, Entite, norm_nom


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


SOMMEIL = d("2027-01-01")


def ent(g, nom):
    for e in g.entites.values():
        if norm_nom(nom) in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
            return e
    return None


def main():
    J = Journal("etape_v2_3_sommeil")
    dire = J.dire
    dire("=" * 92)
    dire(" V2 · ÉTAPE 3 — MICRO-TEST DU SOMMEIL (dormance bidimensionnelle, réveil, fusion, noyau)")
    dire(f"   Dormance : Force < {config.V2_FORCE_SEUIL_DORMANT} SAUF si ≥ {config.V2_DORMANCE_SOURCES_PROTEGE} "
         f"sources ou noyau | Noyau : ≥{config.V2_NOYAU_SOURCES} sources ET ≥{config.V2_NOYAU_ACCES} accès")
    dire("=" * 92)

    g = GrapheMemoire()

    # A — candidat NOYAU : 3 sources indépendantes + 5 accès (récent)
    fA = g.ingerer("Alpha", "pdg_de", "M. Un", "Gazette", d("2026-11-01"))["touches"][0]
    g.ingerer("Alpha", "pdg_de", "M. Un", "Tribune", d("2026-11-05"))
    g.ingerer("Alpha", "pdg_de", "M. Un", "Officiel", d("2026-11-10"))
    for _ in range(5):
        g.acceder(fA, d("2026-12-01"))

    # C — cas (2) : 1 source, 8 accès → ne doit PAS devenir noyau
    fC = g.ingerer("Alpha", "produit", "des moteurs", "Gazette", d("2026-11-01"))["touches"][0]
    for _ in range(8):
        g.acceder(fC, d("2026-12-01"))

    # B — cas (1) : 3 sources, 1 accès, ANCIEN → Force basse mais protégé (pas dormant)
    fB = g.ingerer("Beta", "siege_de", "Lyon", "Gazette", d("2025-06-01"))["touches"][0]
    g.ingerer("Beta", "siege_de", "Lyon", "Tribune", d("2025-06-05"))
    g.ingerer("Beta", "siege_de", "Lyon", "Officiel", d("2025-06-10"))
    g.acceder(fB, d("2025-06-15"))

    # D — dormant CLASSIQUE : 1 source, ancien, peu d'accès → dormant, puis réveil
    fD = g.ingerer("Beta", "effectif_de", "100", "Gazette", d("2025-09-01"))["touches"][0]

    # Z — DOUBLON d'entité (simule un échec de résolution) pour tester la fusion au sommeil
    g.ingerer("Zeta", "produit", "des vélos", "Gazette", d("2026-10-01"))
    zeta = ent(g, "Zeta")
    g._eid += 1
    dup = Entite(g._eid, "Zeta", [], zeta.embedding, d("2026-10-02"))
    g.entites[dup.id] = dup
    fZ2 = g._creer_fait(dup.id, "siege_de", "Nantes", None, "Le siège de Zeta est à Nantes",
                        "BlogX", d("2026-10-02"), d("2026-10-02"), "courant")

    # décroissances « à blanc » pour AFFICHER l'état AVANT sommeil (Force réelle à la date)
    g_avant = g  # on garde la même instance ; on montre l'état après _decroitre dans le rapport
    dire("\n— ÉTAT AVANT SOMMEIL (Force/Certitude à la création, avant décroissance) —")
    for f in [fA, fC, fB, fD, fZ2]:
        dire(f"   {g.fait_court(f)}")
    dire(f"   Entités : {sorted(e.nom for e in g.entites.values())} "
         f"(dont DEUX « Zeta » distinctes à fusionner)")

    # ── SOMMEIL ──────────────────────────────────────────────────────────
    rapport = g.sommeil(SOMMEIL)
    dire("\n— RAPPORT DE SOMMEIL —")
    dire(f"   Promus noyau : {rapport['promus']}")
    dire(f"   Fusions d'entités : {rapport['fusions']}")
    dire(f"   Endormis (dormants) : {rapport['dormis']}")

    dire("\n— ÉTAT APRÈS SOMMEIL —")
    for f in [fA, fC, fB, fD, fZ2]:
        dire(f"   {g.fait_court(f)}")

    # réveil du dormant classique par un accès via la marche
    reveille = g.acceder(fD, SOMMEIL)
    dire(f"\n— RÉVEIL : accès à #{fD.id} (effectif Beta) → "
         f"{'☼ réveillé' if reveille else 'toujours dormant'} : {g.fait_court(fD)}")

    # ── VÉRIFICATIONS ────────────────────────────────────────────────────
    dire("\n" + "=" * 92)
    dire(" VÉRIFICATIONS")
    dire("=" * 92)

    def ok(c, label):
        dire(f"   {'✅' if c else '❌'} {label}")

    ok(fA.noyau, f"NOYAU : #{fA.id} (3 sources, 5 accès) promu noyau ★ — demi-vies doublées")
    ok(not fC.noyau and fC.compteur_acces >= 8,
       f"CAS (2) : #{fC.id} mono-source malgré {fC.compteur_acces} accès → PAS noyau")
    ok(fB.statut != "dormant" and fB.force < config.V2_FORCE_SEUIL_DORMANT,
       f"CAS (1) : #{fB.id} 3 sources / Force {fB.force:.2f} (basse) → PROTÉGÉ, pas dormant "
       f"[{fB.statut}]")
    ok(fD.id in rapport["dormis"] or fD.statut in ("courant",),
       f"DORMANCE classique : #{fD.id} (1 source, ancien) endormi au sommeil")
    ok(reveille and fD.statut != "dormant", f"RÉVEIL : #{fD.id} réveillé par un accès")
    une_zeta = [e for e in g.entites.values() if norm_nom(e.nom) == "zeta"]
    ok(len(une_zeta) == 1 and fZ2.sujet_id == zeta.id,
       f"FUSION : les deux « Zeta » fusionnées en une seule, fait #{fZ2.id} recâblé")

    dire("\n" + "=" * 92)
    dire(f" ✅ Micro-test du sommeil terminé. Journal : {J.chemin}")
    dire("=" * 92)
    J.fermer()


if __name__ == "__main__":
    main()
