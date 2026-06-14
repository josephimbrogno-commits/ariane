# -*- coding: utf-8 -*-
"""
memoire/options/importance.py — OPTION : le troisième axe, l'IMPORTANCE (mission V3).

« Protéger ce qui COMPTE, pas ce qui est récent. » Orthogonale à Force et Certitude : ne décroît
PAS avec le temps, dérivée de la STRUCTURE du graphe.
  1. Importance des ENTITÉS : PageRank pondéré amorcé par des seeds (degré + sources + catégorie).
  2. Importance d'un FAIT : poids_relation × max(imp_sujet, imp_objet)^α.

OFF par défaut (OPT_IMPORTANCE). Quand ON, `calculer` est appelée pendant la consolidation (hook).
Code porté À L'IDENTIQUE du prototype v3_importance.py — aucune logique nouvelle.
"""

import numpy as np

from .. import config
from ..coeur.ontologie import poids_importance


def _norm01(d):
    if not d:
        return {}
    m = max(d.values())
    return {k: (v / m if m > 0 else 0.0) for k, v in d.items()}


def importance_entites(g):
    """PageRank pondéré sur le graphe entité–entité. Renvoie {eid: importance ∈ [0,1]}."""
    eids = list(g.entites)
    n = len(eids)
    if n == 0:
        return {}
    idx = {e: i for i, e in enumerate(eids)}

    degre = {e: 0 for e in eids}
    sources = {e: set() for e in eids}
    for f in g.faits.values():
        if f.sujet_id in degre:
            degre[f.sujet_id] += 1
            for p in f.provenance:
                sources[f.sujet_id].add(p["source_id"])
        if f.objet_id in degre:
            degre[f.objet_id] += 1
    dnorm = _norm01(degre)
    snorm = _norm01({e: len(sources[e]) for e in eids})
    seed = np.zeros(n)
    for e in eids:
        cat = config.IMP_BONUS_CATEGORIE.get(getattr(g.entites[e], "type", None), 0.3)
        seed[idx[e]] = (config.IMP_SEED_DEGRE * dnorm[e]
                        + config.IMP_SEED_SOURCES * snorm[e]
                        + config.IMP_SEED_CATEGORIE * cat)
    if seed.sum() <= 0:
        seed[:] = 1.0
    seed = seed / seed.sum()

    A = np.zeros((n, n))
    for f in g.faits.values():
        if f.objet_id is not None and f.objet_id in idx and f.sujet_id in idx:
            w = poids_importance(f.predicat) * max(0.05, f.certitude)
            A[idx[f.objet_id], idx[f.sujet_id]] += w
            A[idx[f.sujet_id], idx[f.objet_id]] += w

    col = A.sum(axis=0)
    M = np.zeros((n, n))
    for j in range(n):
        M[:, j] = A[:, j] / col[j] if col[j] > 0 else seed

    pr = seed.copy()
    d = config.IMP_DAMPING
    for _ in range(40):
        pr = d * (M @ pr) + (1 - d) * seed
        s = pr.sum()
        if s > 0:
            pr = pr / s
    return _norm01({e: float(pr[idx[e]]) for e in eids})


def importance_fait(g, f, imp_ent):
    """importance_fait = poids_relation × max(imp_sujet, imp_objet)^α (la relation peut écraser)."""
    imp_s = imp_ent.get(f.sujet_id, 0.0)
    imp_o = imp_ent.get(f.objet_id, 0.0) if f.objet_id is not None else 0.0
    return poids_importance(f.predicat) * (max(imp_s, imp_o) ** config.IMP_ALPHA)


def calculer(g):
    """Recalcule l'importance de toutes les entités ET stocke l'importance de chaque fait.
    À appeler pendant le SOMMEIL (pas à chaque écriture)."""
    imp_ent = importance_entites(g)
    for e_id, e in g.entites.items():
        e.importance = imp_ent.get(e_id, 0.0)
    for f in g.faits.values():
        f.importance = importance_fait(g, f, imp_ent)
    return imp_ent
