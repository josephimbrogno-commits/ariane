# -*- coding: utf-8 -*-
"""
tests/unitaires/test_regle_or.py — LA RÈGLE D'OR du registre STRUCTURE.

  « On LIT la toile librement ; on ne TISSE jamais un fil sans dire d'où il vient. »

Prouve que :
  • parcourir LIT (voisinage, degrés, statuts) sans engager de croyance ;
  • lier SANS source ÉCHOUE proprement ; lier AVEC source produit un fait soumis au plafond menteur ;
  • (cas 1) un lier qui CONTREDIT un fait corroboré retombe dans le pipeline de conflit normal —
    disputé + plafonné 0.60 — SANS détrôner la vérité corroborée ; lier n'est pas une porte dérobée ;
  • (cas 2) retoucher(clore) EXIGE source ET date → « était… jusqu'à [date] », clôture sourcée tracée ;
  • retoucher(corroborer) / retoucher(contester) passent par le pipeline et restent sourcés.

Embedding-stub déterministe, pas de LLM.  Lance :  python tests/unitaires/test_regle_or.py
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
    print(" RÈGLE D'OR — registre STRUCTURE (parcourir libre · lier/retoucher sourcés)")
    print("=" * 84)
    mem = Memoire(StubLLM(), stub_embed)

    # ── 0) PARCOURIR : lecture libre, aucune croyance engagée ────────────────
    print("\n— parcourir : on LIT la toile librement —")
    mem.ecrire_triplet("Orion", "appartient_a", "Nexora", "Gazette", D("2026-01"))
    mem.ecrire_triplet("Orion", "siege_de", "Lyon", "Gazette", D("2026-01"))
    n_faits_avant = len(mem.g.faits)
    vue = mem.parcourir("Orion", profondeur=1)
    chk(vue is not None and vue["degre"] >= 1 and len(vue["liens"]) == 2,
        f"parcourir rend le voisinage (degré={vue['degre']}, {len(vue['liens'])} liens)")
    chk(len(mem.g.faits) == n_faits_avant,
        "parcourir N'ÉCRIT RIEN : lire la toile n'engage aucune croyance")

    # ── 1) LIER sans source → ÉCHEC propre ───────────────────────────────────
    print("\n— lier : on ne tisse jamais un fil sans dire d'où il vient —")
    try:
        mem.lier("Orion", "dirige", "Helios", source_id=None)
        chk(False, "lier sans source aurait dû lever ValueError")
    except ValueError:
        chk(len(mem.g.faits) == n_faits_avant, "lier SANS source ÉCHOUE proprement (rien créé)")

    # ── 1bis) LIER avec source → fait soumis au plafond du menteur ───────────
    res = mem.lier("Orion", "dirige", "Helios", source_id="BlogX", date=D("2026-02"))
    lien = fait(mem, "Orion", "dirige", "helios")
    chk(lien is not None and lien.certitude <= 0.60 + 1e-9 and lien.n_sources() == 1,
        f"lier AVEC source crée un fait mono-source plafonné menteur (C={lien.certitude:.2f} ≤ 0.60)")

    # ── 2) CAS 1 : lier qui CONTREDIT un fait corroboré → pas de porte dérobée ─
    print("\n— cas 1 : lier ne détrône pas une vérité corroborée (≥2 sources) —")
    mem.ecrire_triplet("Veltis", "siege_de", "Lyon", "Gazette", D("2026-01"))
    mem.ecrire_triplet("Veltis", "siege_de", "Lyon", "Tribune", D("2026-01"))   # corroboré, C=0.75
    lyon = fait(mem, "Veltis", "siege_de", "lyon")
    c_lyon_avant = lyon.certitude
    mem.lier("Veltis", "siege_de", "Brest", source_id="BlogX", date=D("2026-03"))  # contradiction par lien
    lyon = fait(mem, "Veltis", "siege_de", "lyon")
    brest = fait(mem, "Veltis", "siege_de", "brest")
    chk(lyon.statut == "disputé" and brest.statut == "disputé",
        "le lien contradictoire retombe dans le PIPELINE DE CONFLIT (les deux → disputé)")
    chk(brest.certitude <= 0.60 + 1e-9,
        f"le lien menteur mono-source est plafonné 0.60 (C_brest={brest.certitude:.2f})")
    chk(lyon.certitude >= brest.certitude and lyon.certitude >= 0.55,
        f"la vérité corroborée N'EST PAS DÉTRÔNÉE (C_lyon={lyon.certitude:.2f} ≥ C_brest={brest.certitude:.2f})")
    chk(abs(lyon.certitude - c_lyon_avant) < 0.25 and lyon.certitude > 0.5,
        "lier n'est pas une porte dérobée : impossible d'imposer une contre-vérité par un simple lien")

    # ── 3) CAS 2 : retoucher(clore) EXIGE source ET date, et trace la clôture ─
    print("\n— cas 2 : clôturer est une affirmation sourcée ET datée —")
    mem.ecrire_triplet("Nexora", "pdg_de", "Mme Karel", "Officiel", D("2026-01"))
    karel = fait(mem, "Nexora", "pdg_de", "karel")
    try:
        mem.retoucher(karel.id, "clore", source_id="Officiel")          # pas de date
        chk(False, "clore sans date aurait dû lever ValueError")
    except ValueError:
        chk(karel.statut == "courant", "clore SANS date ÉCHOUE : une clôture doit être datée")
    try:
        mem.retoucher(karel.id, "clore", source_id=None, date=D("2026-05"))  # pas de source
        chk(False, "clore sans source aurait dû lever ValueError")
    except ValueError:
        chk(karel.statut == "courant", "clore SANS source ÉCHOUE : une clôture doit être sourcée")

    mem.retoucher(karel.id, "clore", source_id="JournalOfficiel", date=D("2026-05"))
    karel = fait(mem, "Nexora", "pdg_de", "karel")
    cloture = [p for p in karel.provenance if p.get("type") == "cloture"]
    chk(karel.statut == "clos" and karel.valide_jusqua == D("2026-05"),
        "clore AVEC source+date : fait clos, valide_jusqua = date de fin")
    chk(len(cloture) == 1 and cloture[0]["source_id"] == "JournalOfficiel",
        "la source de clôture est TRACÉE dans la provenance (type=cloture)")
    chk(karel.n_sources() == 1,
        "la clôture n'est pas une affirmation DU fait : elle ne gonfle pas le compte de sources")
    rendu = rendu_epistemique(mem.g, [karel])
    chk("était" in rendu and "2026-05" in rendu,
        "grammaire : « était… jusqu'à [date] » (l'imparfait borné)")

    # ── 4) retoucher(corroborer) & retoucher(contester) — sourcés, via pipeline
    print("\n— retoucher : corroborer / contester restent sourcés —")
    mem.ecrire_triplet("Astra", "siege_de", "Nantes", "Gazette", D("2026-01"))
    astra = fait(mem, "Astra", "siege_de", "nantes")
    mem.retoucher(astra.id, "corroborer", source_id="Tribune", date=D("2026-02"))
    astra = fait(mem, "Astra", "siege_de", "nantes")
    chk(astra.n_sources() == 2 and astra.certitude >= 0.55,
        f"corroborer (source indépendante) → 2 sources, plancher franchi (C={astra.certitude:.2f})")
    try:
        mem.retoucher(astra.id, "contester", source_id=None)
        chk(False, "contester sans source aurait dû lever ValueError")
    except ValueError:
        chk(True, "contester SANS source ÉCHOUE proprement")
    c_avant = astra.certitude
    mem.retoucher(astra.id, "contester", source_id="BlogX", date=D("2026-03"))
    astra = fait(mem, "Astra", "siege_de", "nantes")
    chk(astra.statut == "disputé" and astra.certitude < c_avant,
        "contester (sourcé) → disputé, Certitude baisse, source tracée")

    print("\n" + "=" * 84)
    print(f" {'✅ RÈGLE D OR TENUE — lire est libre, tisser est toujours sourcé' if all(OK) else '❌ RÈGLE D OR VIOLÉE'}"
          f"  ({sum(OK)}/{len(OK)})")
    print("=" * 84)
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
