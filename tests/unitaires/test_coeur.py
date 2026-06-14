# -*- coding: utf-8 -*-
"""
tests/unitaires/test_coeur.py — NON-RÉGRESSION du cœur V2 unifié.

Rejoue la logique d'écriture + le rendu épistémique DEPUIS la bibliothèque `memoire`, avec un
embedding-stub déterministe (pas de modèle à charger, pas de LLM). Les verdicts V2 doivent passer
À L'IDENTIQUE : corroboration, anti-rumeur, clôture, menteur, immuable, plancher, Dupont, grammaire.

Lance :  python tests/unitaires/test_coeur.py
"""

import os
import sys
from datetime import datetime

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
os.chdir(_RACINE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
from memoire import Memoire
from memoire.coeur.lecture import rendu_epistemique
from memoire.coeur.graphe import norm_valeur


def stub_embed(texte):
    """Embedding déterministe (hash → vecteur 24d normalisé). Suffit : la résolution se fait
    surtout par nom exact/tokens ; on évite juste les fusions accidentelles."""
    v = np.zeros(24, dtype=np.float32)
    for i, c in enumerate(str(texte)):
        v[(i * 7 + ord(c)) % 24] += (ord(c) % 13) + 1
    n = np.linalg.norm(v)
    return v / n if n else v


class StubLLM:
    def texte(self, prompt, systeme=None, temperature=0.0):
        return ""

    def json(self, prompt, systeme=None):
        return {}


def D(s):
    return datetime.strptime(s, "%Y-%m")


OK = []


def chk(cond, label):
    OK.append(bool(cond))
    print(f"   {'✅' if cond else '❌'} {label}")


def fait(mem, sujet, pred, contient=None, statut=None):
    e = mem.g.trouver_entite(sujet)
    if not e:
        return None
    for f in mem.g.faits_de(e.id, pred):
        if contient is not None and contient not in norm_valeur(f.objet):
            continue
        if statut is not None and f.statut != statut:
            continue
        return f
    return None


def main():
    print("=" * 84)
    print(" NON-RÉGRESSION DU CŒUR V2 UNIFIÉ (bibliothèque `memoire`, stub embed)")
    print("=" * 84)
    mem = Memoire(StubLLM(), stub_embed)
    E = mem.ecrire_triplet

    # — A) corroboration + répétition même source —
    E("Nexora", "pdg_de", "Mme Karel", "Gazette", D("2026-01"))
    f = fait(mem, "Nexora", "pdg_de", "karel")
    chk(abs(f.certitude - 0.55) < 1e-6 and f.n_sources() == 1, "création : C=0.55, 1 source")
    E("Nexora", "pdg_de", "Mme Karel", "Tribune", D("2026-01"))
    chk(abs(f.certitude - 0.75) < 1e-6 and f.n_sources() == 2, "corroboration indépendante : C=0.75, 2 sources")
    E("Nexora", "pdg_de", "Mme Karel", "Tribune", D("2026-02"))
    chk(abs(f.certitude - 0.75) < 1e-6, "répétition même source : C INCHANGÉE (anti-rumeur)")

    # — B) clôture + grammaire imparfait —
    E("Nexora", "pdg_de", "M. Doss", "Officiel", D("2026-05"), validite="2026-05")
    karel, doss = fait(mem, "Nexora", "pdg_de", "karel"), fait(mem, "Nexora", "pdg_de", "doss")
    chk(karel.statut == "clos" and karel.valide_jusqua is not None and doss.statut == "courant",
        "clôture : ancien PDG clos (daté), nouveau courant")
    rendu_clos = rendu_epistemique(mem.g, [karel])
    chk("CLOS" in rendu_clos and "était" in rendu_clos, "grammaire : clos → IMPARFAIT (« était »)")

    # — C) menteur + anti-rumeur —
    E("Veltis", "siege_de", "Lyon", "Gazette", D("2026-01"))
    E("Veltis", "siege_de", "Lyon", "Tribune", D("2026-01"))     # corroboré (2 src, 0.75)
    E("Veltis", "siege_de", "Brest", "BlogX", D("2026-03"))      # mensonge mono-source
    lyon, brest = fait(mem, "Veltis", "siege_de", "lyon"), fait(mem, "Veltis", "siege_de", "brest")
    chk(lyon.statut == "disputé" and brest.statut == "disputé" and lyon.certitude >= brest.certitude,
        "menteur : vérité corroborée résiste (disputé, Lyon ≥ Brest)")
    chk(brest.certitude <= 0.60 + 1e-9, "menteur : mensonge mono-source plafonné à 0.60")
    avant = brest.certitude
    E("Veltis", "siege_de", "Brest", "BlogX", D("2026-04"))      # répétition même source
    chk(abs(brest.certitude - avant) < 1e-6, "anti-rumeur : répéter la même source ≠ corroborer")

    # — D) immuable : la Certitude ne décroît jamais —
    E("Veltis", "date_fondation_de", "1998", "Gazette", D("2026-01"))
    E("Veltis", "date_fondation_de", "1998", "Almanach", D("2026-02"))
    fond = fait(mem, "Veltis", "date_fondation_de")
    c_avant = fond.certitude
    mem.consolider(D("2030-01"))                                  # +4 ans
    chk(abs(fond.certitude - c_avant) < 1e-6, "immuable : Certitude inchangée après 4 ans")

    # — E) plancher de Certitude (≥2 sources) — la vérité reste plus certaine que le mensonge —
    chk(lyon.certitude >= 0.55 and lyon.certitude > brest.certitude,
        "plancher : fait corroboré ≥ 0.55, reste au-dessus du mensonge")

    # — F) Dupont : fait stable jamais reconfirmé → réserve (Certitude < 0.6) —
    mem2 = Memoire(StubLLM(), stub_embed)
    mem2.ecrire_triplet("M. Dupont", "marie_a", "Mme Sora", "Gazette", D("2026-01"))
    fd = fait(mem2, "M. Dupont", "marie_a", "sora")
    mem2.consolider(D("2027-09"))                                 # ~20 mois sans reconfirmation
    chk(fd.certitude < 0.6, f"Dupont : stable non reconfirmé → réserve (C={fd.certitude:.2f} < 0.6)")
    rendu_dupont = rendu_epistemique(mem2.g, [fd])
    chk("à revérifier" in rendu_dupont, "grammaire : incertain → « à revérifier »")

    # — G) grammaire présent sûr (≥2 sources, courant) —
    chk("ACTUEL — sûr" in rendu_epistemique(mem.g, [fond]) and "1998" in rendu_epistemique(mem.g, [fond]),
        "grammaire : courant sûr → présent affirmé")

    print("\n" + "=" * 84)
    print(f" {'✅ NON-RÉGRESSION OK — le cœur V2 unifié passe tous les verdicts' if all(OK) else '❌ RÉGRESSION DÉTECTÉE'}"
          f"  ({sum(OK)}/{len(OK)})")
    print("=" * 84)
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
