# -*- coding: utf-8 -*-
"""
memoire/options/typologie_liens.py — OPTION : typologie DURABLE / ÉPHÉMÈRE d'un lien (mission Typologie).

À partir de la SEULE structure (degrés, réciprocité, forme temporelle — JAMAIS le prédicat ni la
nature), prédit DURABLE / ÉPHÉMÈRE. Hiérarchie S2 « date d'abord » (leçon de P-B) :
  1) occurrence ponctuelle (début==fin) → ÉPHÉMÈRE (prime sur tout)
  2) sinon réciprocité                  → DURABLE
  3) sinon                              → ÉPHÉMÈRE
S1S2 départage la zone ambiguë (non datée, non réciproque) par la connectivité.

Le classifieur `predire` est porté À L'IDENTIQUE du prototype structure_predicteur.py. `features_fait`
permet d'appliquer la typologie EN LECTURE sur le vrai graphe (mêmes 5 features que le banc).
ON par défaut (OPT_TYPOLOGIE) ; n'altère jamais une croyance — c'est une lecture de la toile.
"""

DURABLE = "DURABLE"
EPHEMERE = "ÉPHÉMÈRE"

# Les 4 durables ASYMÉTRIQUES non datés que la structure seule ne voit pas (la « frange »).
ASYMETRIQUES_DURABLES = {"dirige", "appartient_a", "possede", "travaille_pour"}


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
            return DURABLE
        if occ:
            return EPHEMERE
        return EPHEMERE

    if mode == "S2_naif_date":       # « porte une date » sans distinguer occurrence / début
        if porte_date:
            return EPHEMERE
        if recip:
            return DURABLE
        return EPHEMERE

    raise ValueError(mode)


# ── Typologie EN LECTURE sur le vrai graphe (mêmes 5 features que le banc) ──────────
def degres_graphe(g):
    """Degré (nb de voisins distincts entité↔entité) de chaque entité du graphe."""
    vois = {eid: set() for eid in g.entites}
    for f in g.faits.values():
        if f.objet_id is not None and f.sujet_id in vois and f.objet_id in vois:
            vois[f.sujet_id].add(f.objet_id)
            vois[f.objet_id].add(f.sujet_id)
    return {eid: len(v) for eid, v in vois.items()}


def features_fait(g, f, deg=None):
    """Les 5 features structurelles d'un fait entité→entité (None si l'objet n'est pas une entité)."""
    if f.objet_id is None:
        return None
    if deg is None:
        deg = degres_graphe(g)
    recip = any(o.sujet_id == f.objet_id and o.objet_id == f.sujet_id
                for o in g.faits.values() if o.id != f.id)
    return {
        "deg_sujet": deg.get(f.sujet_id, 0),
        "deg_objet": deg.get(f.objet_id, 0),
        "reciproque": recip,
        "porte_date": f.valide_de is not None,
        "est_occurrence": (f.valide_de is not None and f.valide_jusqua is not None),
    }


def nature_lien(g, f, mode="S1S2", deg=None):
    """Typologie d'un lien du graphe (lecture seule). None si l'objet n'est pas une entité."""
    feat = features_fait(g, f, deg)
    return predire(feat, mode) if feat else None
