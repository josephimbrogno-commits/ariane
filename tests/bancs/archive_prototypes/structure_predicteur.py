# -*- coding: utf-8 -*-
"""
structure_predicteur.py — le PRÉDICTEUR structurel (ce qu'on teste).

À partir de la SEULE structure (degrés, réciprocité, forme temporelle — JAMAIS le prédicat ni la
nature), prédit DURABLE / ÉPHÉMÈRE. Plusieurs modes pour l'ablation :

  S1            : connectivité seule (le signal naïf).
  S2            : forme temporelle + réciprocité, avec la HIÉRARCHIE « date d'abord » :
                  1) occurrence ponctuelle → ÉPHÉMÈRE (prime sur tout — leçon de P-B)
                  2) sinon réciprocité     → DURABLE
                  3) sinon                 → ÉPHÉMÈRE
  S1S2          : S2 + départage par connectivité dans la zone ambiguë (non datée, non réciproque).
  S2_recip_first: ablation « mauvaise hiérarchie » (réciprocité AVANT date) → doit rater P-B.
  S2_naif_date  : ablation « porte une date » sans distinguer occurrence/début → doit rater C-E.
"""

from structure_monde import DURABLE, EPHEMERE


def predire(feat, mode):
    dS, dO = feat["deg_sujet"], feat["deg_objet"]
    occ = feat["est_occurrence"]
    recip = feat["reciproque"]
    porte_date = feat["porte_date"]

    if mode == "S1":
        return DURABLE if min(dS, dO) >= 2 else EPHEMERE

    if mode == "S2":
        if occ:
            return EPHEMERE          # 1) occurrence ponctuelle prime
        if recip:
            return DURABLE           # 2) réciprocité
        return EPHEMERE              # 3) défaut

    if mode == "S1S2":
        if occ:
            return EPHEMERE
        if recip:
            return DURABLE
        return DURABLE if min(dS, dO) >= 2 else EPHEMERE   # zone ambiguë : connectivité

    if mode == "S2_recip_first":     # MAUVAISE hiérarchie : réciprocité avant date
        if recip:
            return DURABLE           # P-B est réciproque (confondu) → DURABLE (faux)
        if occ:
            return EPHEMERE
        return EPHEMERE

    if mode == "S2_naif_date":       # « porte une date » sans distinguer occurrence / début
        if porte_date:
            return EPHEMERE          # C-E (depuis 2015) → ÉPHÉMÈRE (faux)
        if recip:
            return DURABLE
        return EPHEMERE

    raise ValueError(mode)
