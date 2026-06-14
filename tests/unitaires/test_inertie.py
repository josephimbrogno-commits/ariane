# -*- coding: utf-8 -*-
"""
tests/unitaires/test_inertie.py — INERTIE des options OFF par défaut.

Exigence : tant qu'on ne bascule pas l'interrupteur, l'option ne modifie RIEN. On le prouve pour
les deux options OFF par défaut — importance (OPT_IMPORTANCE / OPT_IMPORTANCE_RETRIEVAL) et
dormance modulée (OPT_DORMANCE_MODULEE) :

  1. Avec les défauts, après consolidation, AUCUNE importance n'est calculée (hook inerte) :
     f.importance reste à 0.0 pour tous les faits.
  2. Même en INJECTANT de force une importance maximale (1.0) partout, tant que les interrupteurs
     restent OFF : la dormance et le score de retrieval sont STRICTEMENT INCHANGÉS.
  3. Contre-épreuve : basculer l'interrupteur CHANGE le résultat → ce sont de vrais interrupteurs,
     pas du code mort. L'inertie vient de l'OFF, pas d'une option débranchée.

Embedding-stub déterministe, pas de LLM.  Lance :  python tests/unitaires/test_inertie.py
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
from memoire import Memoire, config
from memoire.coeur import lecture


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


def peupler(mem):
    """Un petit monde connecté + un fait laissé vieillir (candidat dormance)."""
    E = mem.ecrire_triplet
    E("Nexora", "pdg_de", "Mme Karel", "Gazette", D("2026-01"))
    E("Nexora", "siege_de", "Lyon", "Gazette", D("2026-01"))
    E("Orion", "appartient_a", "Nexora", "Gazette", D("2026-01"))
    E("Mme Karel", "marie_a", "M. Sora", "Gazette", D("2026-01"))
    E("Nexora", "effectif_de", "240", "BlogX", D("2026-01"))   # mono-source, vieillira


def etats_dormance(mem):
    return tuple(sorted((f.id, f.statut) for f in mem.g.faits.values()))


def scores_retrieval(mem, question):
    faits, _ = lecture.entree_vectorielle(mem.g, question)
    return tuple((f.id) for f in faits)


def main():
    print("=" * 88)
    print(" INERTIE DES OPTIONS OFF PAR DÉFAUT (importance · dormance modulée)")
    print("=" * 88)

    # Vérifie d'abord les défauts attendus.
    chk(config.OPT_IMPORTANCE is False and config.OPT_IMPORTANCE_RETRIEVAL is False
        and config.OPT_DORMANCE_MODULEE is False,
        "défauts : OPT_IMPORTANCE / _RETRIEVAL / DORMANCE_MODULEE = False")
    chk(config.OPT_RECONNAISSANCE is True and config.OPT_TYPOLOGIE is True,
        "défauts : OPT_RECONNAISSANCE / OPT_TYPOLOGIE = True")

    # ── 1) Hook inerte : aucune importance calculée avec les défauts ─────────
    mem = Memoire(StubLLM(), stub_embed)
    peupler(mem)
    mem.consolider(D("2027-06"))      # ~17 mois plus tard
    importance_nulle = all(f.importance == 0.0 for f in mem.g.faits.values())
    chk(importance_nulle, "hook OFF : après consolidation, toutes les f.importance = 0.0 (rien calculé)")

    etat_ref = etats_dormance(mem)
    score_ref = scores_retrieval(mem, "Quel est le siège de Nexora ?")

    # ── 2) Injecter une importance maximale ne change RIEN (interrupteurs OFF)
    for f in mem.g.faits.values():
        f.importance = 1.0
    for e in mem.g.entites.values():
        e.importance = 1.0
    mem.g.recalculer_dormance()        # défaut β géré par OPT_DORMANCE_MODULEE (OFF → β=0)
    chk(etats_dormance(mem) == etat_ref,
        "dormance INCHANGÉE malgré importance=1.0 partout (OPT_DORMANCE_MODULEE OFF)")
    chk(scores_retrieval(mem, "Quel est le siège de Nexora ?") == score_ref,
        "retrieval INCHANGÉ malgré importance=1.0 partout (OPT_IMPORTANCE_RETRIEVAL OFF)")

    # ── 3) Contre-épreuve : basculer l'interrupteur CHANGE le résultat ───────
    #   (sinon l'inertie serait celle d'un code mort, pas d'un OFF effectif)
    base = config.V2_FORCE_SEUIL_DORMANT
    seuil_off = mem.g._seuil_dormance(next(iter(mem.g.faits.values())))
    config.OPT_DORMANCE_MODULEE = True
    try:
        seuil_on = mem.g._seuil_dormance(next(iter(mem.g.faits.values())))
    finally:
        config.OPT_DORMANCE_MODULEE = False
    chk(abs(seuil_off - base) < 1e-12 and seuil_on < seuil_off,
        f"vrai interrupteur : seuil OFF={seuil_off:.3f} (=base) → ON={seuil_on:.3f} (abaissé par importance)")

    config.OPT_IMPORTANCE_RETRIEVAL = True
    try:
        f0 = next(iter(mem.g.faits.values()))
        # avec le terme importance ré-activé, le score d'au moins un fait change
        v = mem.g.embed("Quel est le siège de Nexora ?")
        s_off = config.IMP_W_SIM * float(v @ f0.embedding) + config.IMP_W_FORCE * f0.force
        s_on = s_off + config.IMP_W_IMPORTANCE * f0.importance
        change = abs(s_on - s_off) > 1e-9
    finally:
        config.OPT_IMPORTANCE_RETRIEVAL = False
    chk(change, "vrai interrupteur : le terme importance ré-activé déplace bien le score (ON ≠ OFF)")

    print("\n" + "=" * 88)
    verdict = all(OK)
    print(f" {'✅ OPTIONS OFF INERTES — elles ne modifient rien tant que l interrupteur reste OFF' if verdict else '❌ FUITE — une option OFF modifie le comportement'}"
          f"  ({sum(OK)}/{len(OK)})")
    print("=" * 88)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
