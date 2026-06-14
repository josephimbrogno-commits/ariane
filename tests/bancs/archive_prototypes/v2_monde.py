# -*- coding: utf-8 -*-
"""
v2_monde.py — MONDE SYNTHÉTIQUE ENRICHI pour le grand run V2 (mission §5).

Reprend les 40 entités, mais produit désormais un FLUX d'énoncés DATÉS et SOURCÉS (plusieurs
canaux fictifs), avec classes de volatilité correctes (dont des faits IMMUABLES : fondations,
naissances). Inclut les injections des tests menteur / rumeur / Dupont. Déterministe (graine).
"""

import random
from dataclasses import dataclass, field
from datetime import timedelta

import config
import monde
from monde import normaliser, mois_annee
from v2_ontologie import phrase

SOURCES = ["la Gazette", "la Tribune", "le Quotidien", "la Dépêche",
           "Radio Centre", "l'Officiel", "l'Almanach", "le Canard"]

QUESTIONS_PRED = {
    "pdg_de": "Qui dirige actuellement {e} ?",
    "maire_de": "Qui est le maire de {e} ?",
    "siege_de": "Où se trouve le siège de {e} ?",
    "effectif_de": "Combien de personnes {e} emploie-t-elle ?",
    "population_de": "Combien d'habitants compte {e} ?",
    "profession_de": "Quel est le métier de {e} ?",
    "ville_exercice_de": "Dans quelle ville exerce {e} ?",
    "horaire_de": "À quelle heure ferme {e} ?",
    "rue_de": "Dans quelle rue se trouve {e} ?",
    "date_fondation_de": "En quelle année {e} a-t-elle été fondée ?",
    "date_naissance_de": "En quelle année {e} est-elle née ?",
}

ATTRS = {
    "entreprise": [("pdg_de", "dirigeants"), ("siege_de", "villes"),
                   ("effectif_de", "effectif"), ("date_fondation_de", "annee_fond")],
    "ville": [("maire_de", "dirigeants"), ("population_de", "population")],
    "personne": [("profession_de", "professions"), ("ville_exercice_de", "villes"),
                 ("date_naissance_de", "annee_naiss")],
    "lieu": [("horaire_de", "horaires"), ("rue_de", "rues")],
}
IMMUABLES = {"date_fondation_de", "date_naissance_de"}


@dataclass
class FaitVT:
    fid: int
    entite: str
    predicat: str
    val_init: str
    cle_init: str
    val_fin: str
    cle_fin: str
    change: bool
    date_change: object
    immuable: bool
    special: str = ""    # "", "dupont", "menteur", "rumeur"

    def cle_vraie(self):
        return self.cle_fin if self.change else self.cle_init

    def val_vraie(self):
        return self.val_fin if self.change else self.val_init

    def question(self):
        return QUESTIONS_PRED[self.predicat].format(e=self.entite)

    def categorie(self):
        return "changé" if self.change else "stable"


@dataclass
class Enonce:
    texte: str
    source: str
    date_obs: object
    sujet: str
    predicat: str
    objet: str
    date_validite: object   # str "AAAA-MM"/"AAAA" ou None
    kind: str               # init / final / menteur / rumeur


def _valeur(rng, pool):
    if pool == "annee_fond":
        a = str(rng.randrange(1970, 2016)); return (a, a)
    if pool == "annee_naiss":
        a = str(rng.randrange(1950, 1991)); return (a, a)
    return monde._tirer(rng, pool)


def generer_monde_v2():
    rng = random.Random(config.SEED_MONDE + 7)
    debut = config.MONDE_DEBUT
    entites = ([(e, "entreprise") for e in monde.ENTREPRISES]
               + [(e, "ville") for e in monde.VILLES_ENT]
               + [(e, "personne") for e in monde.PERSONNES]
               + [(e, "lieu") for e in monde.LIEUX])

    faits, flux = [], []
    fid = 0
    for (entite, typ) in entites:
        for (pred, pool) in ATTRS[typ]:
            immuable = pred in IMMUABLES
            aff_i, cle_i = _valeur(rng, pool)
            change = (not immuable) and (rng.random() < 1.0 / 3.0)
            aff_f, cle_f, date_chg = aff_i, cle_i, None
            if change:
                for _ in range(20):
                    aff_f, cle_f = _valeur(rng, pool)
                    if normaliser(cle_f) != normaliser(cle_i):
                        break
                date_chg = debut + timedelta(days=rng.randint(60, 300))
            fid += 1
            f = FaitVT(fid, entite, pred, aff_i, normaliser(cle_i), aff_f, normaliser(cle_f),
                       change, date_chg, immuable)
            faits.append(f)

            # — énoncés de la valeur INITIALE (1 ou 2 sources, dates précoces) —
            n_src = rng.choice([1, 2, 2])
            srcs = rng.sample(SOURCES, n_src)
            for k, s in enumerate(srcs):
                dt = debut + timedelta(days=rng.randint(0, 40) + 5 * k)
                flux.append(Enonce(phrase(pred, entite, aff_i, "present"), s, dt,
                                   entite, pred, aff_i, None, "init"))
            # — énoncés de la valeur FINALE (si changement) —
            if change:
                n_src2 = rng.choice([1, 2])
                for k, s in enumerate(rng.sample(SOURCES, n_src2)):
                    dt = date_chg + timedelta(days=5 * k)
                    txt = f"Depuis {mois_annee(date_chg)}, {phrase(pred, entite, aff_f, 'present')[0].lower()}{phrase(pred, entite, aff_f, 'present')[1:]}"
                    flux.append(Enonce(txt, s, dt, entite, pred, aff_f,
                                       date_chg.strftime("%Y-%m"), "final"))

    # ── TEST DUPONT : 3 faits stables corroborés mais JAMAIS reconfirmés ──
    #   (déjà dans le flux via leurs énoncés init ; on les marque pour le contrôle grammatical)
    stables_corr = [f for f in faits if not f.change and not f.immuable]
    rng.shuffle(stables_corr)
    dupont = stables_corr[:3]
    for f in dupont:
        f.special = "dupont"

    # ── TEST MENTEUR : 5 vérités corroborées + 1 énoncé FAUX à source unique ──
    corrobores = [f for f in faits if not f.change and not f.immuable and f.special == ""]
    rng.shuffle(corrobores)
    menteur = corrobores[:5]
    for f in menteur:
        f.special = "menteur"
        # garantir une vérité CORROBORÉE (≥2 sources) avant l'attaque
        utilisees = {e.source for e in flux
                     if e.sujet == f.entite and e.predicat == f.predicat and e.kind == "init"}
        fraiches = [s for s in SOURCES if s not in utilisees][:1]
        for s in fraiches:
            flux.append(Enonce(phrase(f.predicat, f.entite, f.val_init, "present"), s,
                               debut + timedelta(days=12), f.entite, f.predicat, f.val_init,
                               None, "init"))
        pool = dict(ATTRS_FLAT())[f.predicat]
        for _ in range(20):
            faux_aff, faux_cle = _valeur(rng, pool)
            if normaliser(faux_cle) != f.cle_init:
                break
        dt = debut + timedelta(days=rng.randint(120, 200))
        flux.append(Enonce(phrase(f.predicat, f.entite, faux_aff, "present"),
                           "le Canard", dt, f.entite, f.predicat, faux_aff, None, "menteur"))
        f._faux = faux_cle  # pour le contrôle

    # ── TEST RUMEUR : une même source répète 5× un fait FAUX ──
    libres = [f for f in faits if not f.change and not f.immuable and f.special == ""]
    rng.shuffle(libres)
    rumeur = libres[0]
    rumeur.special = "rumeur"
    pool = dict(ATTRS_FLAT())[rumeur.predicat]
    for _ in range(20):
        ru_aff, ru_cle = _valeur(rng, pool)
        if normaliser(ru_cle) != rumeur.cle_init:
            break
    for k in range(5):
        dt = debut + timedelta(days=150 + 7 * k)
        flux.append(Enonce(phrase(rumeur.predicat, rumeur.entite, ru_aff, "present"),
                           "Radio Centre", dt, rumeur.entite, rumeur.predicat, ru_aff, None, "rumeur"))
    rumeur._faux = ru_cle

    flux.sort(key=lambda e: e.date_obs)
    return faits, flux, {"dupont": dupont, "menteur": menteur, "rumeur": rumeur}


def ATTRS_FLAT():
    out = []
    for lst in ATTRS.values():
        out.extend(lst)
    return out


def choisir_questions(faits, n):
    rng = random.Random(config.SEED_MONDE + 8)
    changes = [f for f in faits if f.change]
    stables = [f for f in faits if not f.change and f.special != "menteur" and f.special != "rumeur"]
    rng.shuffle(changes); rng.shuffle(stables)
    n_ch = min(len(changes), n // 2)
    q = changes[:n_ch] + stables[:n - n_ch]
    rng.shuffle(q)
    return q
