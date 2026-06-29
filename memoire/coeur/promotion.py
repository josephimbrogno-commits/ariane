# -*- coding: utf-8 -*-
"""
memoire/coeur/promotion.py — CHANTIER 2C : PROMOTION RÉTROACTIVE.

Vision NOYAU : « un fait nouveau réveille le dormant qui devient pertinent ». À l'insertion d'un
fait NEUF sur une entité E, on RE-EXAMINE de façon CIBLÉE — voisinage BORNÉ de E (et de l'objet O
du fait neuf), via l'index 2A `faits_voisins` — les faits DORMANTS candidats. Un dormant devenu
pertinent au regard du fait neuf est PROMU dans la toile active comme fait QUALIFIÉ « promu »
(JAMAIS présenté comme « observé neuf »), en passant LES MÊMES GARDE-FOUS qu'un fait neuf
(cardinal / péremption / conflit 0-CW), réutilisés EN LECTURE depuis le cœur (jamais réécrits).

INTERRUPTEUR (variable d'env UNIQUEMENT — pas de config.py) :
  NOYAU_PROMOTION=1   → promotion active.
  défaut (absent/≠"1") → INERTE : aucun appel n'est fait (le hook api.py rend la main avant toute
                         action) → comportement d'écriture historique strictement inchangé.
Lu UNE fois au chargement du module (pas de bascule à chaud — évite tout état hybride).

COUPLAGE INDEX (2A) — explicite et mesuré : la fouille ciblée s'appuie sur `g.faits_voisins()`,
BORNÉE en O(degré) UNIQUEMENT si NOYAU_INDEX=1. Sans index, `faits_voisins` retombe en scan
O(toile) : la promotion reste CORRECTE (mêmes élus) mais REDEVIENT non bornée. On loue donc à
PROMOTION ON de supposer INDEX ON ; sinon on LOGUE un avertissement (une fois), jamais un cap muet.

GARDE-FOU HUBS (graphes scale-free) : PLAFOND DE FAN-OUT sur le voisinage d'une entité-hub. Si
|voisinage(E)| dépasse le plafond, on BORNE (troncature déterministe, fid croissant) et on LOGUE
la troncature — jamais silencieuse.
"""

import os
import logging

from .ontologie import spec_predicat

_log = logging.getLogger("noyau.promotion")

# ── statut d'un fait promu : qualif EXPLICITE, distincte de « courant » (observé neuf) ───────────
STATUT_PROMU = "promu"

# ── interrupteurs / paramètres (lus UNE fois au chargement) ──────────────────────────────────────
ACTIF = os.environ.get("NOYAU_PROMOTION") == "1"
_INDEX_ON = os.environ.get("NOYAU_INDEX") == "1"
PLAFOND_FANOUT = int(os.environ.get("NOYAU_PROMOTION_CAP", "64"))   # cap fan-out hub (configurable)
SIM_SEUIL = float(os.environ.get("NOYAU_PROMOTION_SIM", "0.60"))    # seuil pertinence par embedding

# Un fait promu compte parmi les valeurs ACTIVES (au même titre que courant/disputé) pour le cardinal.
_STATUTS_ACTIFS = ("courant", "disputé", STATUT_PROMU)

_avert_couplage_emis = False


def _avertir_couplage():
    """LOGUE une fois si PROMOTION ON mais INDEX OFF (fouille ciblée non bornée — cf. sonde 1B)."""
    global _avert_couplage_emis
    if ACTIF and not _INDEX_ON and not _avert_couplage_emis:
        _avert_couplage_emis = True
        _log.warning(
            "NOYAU_PROMOTION=1 SANS NOYAU_INDEX=1 : faits_voisins() retombe en O(toile) ; "
            "la fouille ciblée n'est plus bornée (couplage index↔promotion, sonde 1B)."
        )


# ── VOISINAGE BORNÉ (index 2A + plafond de fan-out) ───────────────────────────────────────────────
def _voisinage_borne(g, eid, stats):
    """Voisinage d'une entité via l'index 2A, PLAFONNÉ. `faits_voisins` renvoie déjà les faits triés
    par fid → la troncature aux N premiers est DÉTERMINISTE. Toute troncature est LOGUÉE."""
    vois = g.faits_voisins(eid)
    n = len(vois)
    if n > PLAFOND_FANOUT:
        _log.warning(
            "PLAFOND DE FAN-OUT : entité hub #%s a %d faits incidents > cap %d → voisinage TRONQUÉ "
            "aux %d premiers (fid croissant). Troncature LOGUÉE (jamais silencieuse).",
            eid, n, PLAFOND_FANOUT, PLAFOND_FANOUT,
        )
        if stats is not None:
            stats["tronque"] = True
            stats.setdefault("tronque_detail", []).append(
                {"entite": eid, "incident": n, "cap": PLAFOND_FANOUT})
        vois = vois[:PLAFOND_FANOUT]
    return vois


# ── PERTINENCE : un dormant devient-il pertinent au regard du fait neuf ? ─────────────────────────
def _pertinent(f, trigger, ents):
    """Toucher E SEUL ne suffit PAS (sinon tout dormant de E serait promu → sur-promotion). Il faut
    un signal de parenté avec le CONTENU du fait neuf :
      (S1) MÊME prédicat que le fait neuf (nouvelle occurrence de la même relation sur E) ;
      (S2) le dormant RELIE les deux bouts du fait neuf {E, O} (arête latente entre entités
           désormais co-mentionnées) ;
      (S3) similarité d'embedding ≥ SIM_SEUIL (parenté sémantique fine, déterministe).
    """
    f_ents = {f.sujet_id, f.objet_id} - {None}
    if not (f_ents & ents):                       # garanti par le voisinage, mais explicite
        return False
    if f.predicat == trigger.predicat:                                   # S1
        return True
    if len(ents) == 2 and {f.sujet_id, f.objet_id} >= ents:             # S2 : relie E et O
        return True
    try:                                                                 # S3 : embeddings déterministes
        if float(f.embedding @ trigger.embedding) >= SIM_SEUIL:
            return True
    except Exception:
        pass
    return False


# ── GARDE-FOUS : mêmes contrôles qu'un fait neuf, EN LECTURE (GO/NO-GO de la résurrection) ─────────
def _garde_fous_ok(g, f):
    """Décide si réveiller `f` violerait un garde-fou — on NE réécrit PAS la résolution de conflit du
    cœur, on en réutilise les primitives (faits_de, cle_objet, n_sources, spec) pour trancher GO/NO-GO.
    Refus si :
      • le fait est déjà CLOS (intervalle fermé) → historique, jamais ressuscité au présent ;
      • prédicat FONCTIONNEL et une valeur ACTIVE DIFFÉRENTE existe qui est, soit au moins aussi
        RÉCENTE (péremption / cardinal), soit CORROBORÉE ≥0.6 & ≥2 sources (conflit 0-CW — ne pas
        réveiller un contradicteur d'une vérité corroborée, comme `ingerer` le ferait pour un neuf).
    """
    if f.valide_jusqua is not None:
        return False
    if not spec_predicat(f.predicat)["fonctionnel"]:
        return True                                # multi-valué : aucun cardinal à violer
    cle = f.cle_objet()
    for autre in g.faits_de(f.sujet_id, f.predicat):
        if autre.id == f.id or autre.statut not in _STATUTS_ACTIFS:
            continue
        if autre.cle_objet() == cle:               # même valeur → corroboration, pas conflit
            continue
        if (autre.valide_de is not None and f.valide_de is not None
                and autre.valide_de >= f.valide_de):
            return False                           # PÉREMPTION : incumbent au moins aussi récent
        if autre.certitude >= 0.6 and autre.n_sources() >= 2:
            return False                           # CONFLIT 0-CW : incumbent corroboré
    return True


# ── PROMOTION D'UN ÉLU : réutilise la mécanique d'accès du cœur, puis QUALIFIE « promu » ───────────
def _promouvoir_un(g, f, date):
    g.acceder(f, date)                             # mécanique de réveil du cœur (Force ↑, accès daté)
    seuil = g._seuil_dormance(f)                   # plante le fait DANS la toile active (≥ ligne de dormance)
    if f.force < seuil:
        f.force = seuil
    f.statut = STATUT_PROMU                         # qualif EXPLICITE — jamais « courant/observé neuf »
    f.statut_avant_dormance = None
    if not hasattr(g, "journal_promotion"):
        g.journal_promotion = []
    g.journal_promotion.append({
        "fait": f.id, "predicat": f.predicat, "sujet": g.nom_entite(f.sujet_id),
        "objet": g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet,
        "statut": STATUT_PROMU, "date": date,
    })


# ── POINT D'ENTRÉE : re-fouille ciblée + promotion ───────────────────────────────────────────────
def examiner(g, trigger, sujet_id, date, stats=None):
    """À l'arrivée du fait NEUF `trigger` (entité E = `sujet_id`), re-fouille CIBLÉE et bornée du
    voisinage (E + objet O), promotion des dormants pertinents passant les garde-fous.
    Retourne la liste des fids promus. `stats` (dict optionnel) reçoit les compteurs de COÛT
    (voisinage, candidats, promus, troncature) — pour le banc 2C, sans polluer le chemin de prod.
    """
    _avertir_couplage()
    obj_id = trigger.objet_id
    vu = {}
    for eid in (sujet_id, obj_id):
        if eid is None:
            continue
        for f in _voisinage_borne(g, eid, stats):
            vu[f.id] = f
    # CANDIDATS = faits DORMANTS du voisinage borné, hors le fait neuf lui-même. Ordre fid → déterministe.
    candidats = [vu[i] for i in sorted(vu)
                 if vu[i].statut == "dormant" and vu[i].id != trigger.id]
    ents = {sujet_id, obj_id} - {None}
    promus = []
    for f in candidats:
        if not _pertinent(f, trigger, ents):
            continue
        if not _garde_fous_ok(g, f):
            _log.info("PROMOTION REFUSÉE (garde-fou) : fait #%s %s reste dormant "
                      "(péremption/conflit/clos).", f.id, f.predicat)
            continue
        _promouvoir_un(g, f, date)
        promus.append(f.id)
    if stats is not None:
        stats["voisinage"] = len(vu)               # faits RE-EXAMINÉS (coût structurel, esprit sonde 1B)
        stats["candidats"] = len(candidats)
        stats["promus"] = len(promus)
        stats.setdefault("tronque", False)
    return promus
