# -*- coding: utf-8 -*-
"""
monde.py — génère le MINI-MONDE synthétique de l'étape 2.

~40 entités (entreprises, villes, personnes, lieux) avec des faits DATÉS.
Sur 12 mois simulés, ~1/3 des faits CHANGENT (nouvelle valeur, à une date connue) :
c'est la VÉRITÉ-TERRAIN. Tout est déterministe (graine fixe) et inspectable.

Un « fait » = (entité, attribut). Il porte :
  - sa question d'évaluation,
  - sa valeur initiale (vraie dès le début),
  - éventuellement une valeur finale + une date de changement,
  - une « clé » de correspondance pour noter automatiquement les réponses.
"""

import random
import unicodedata
from dataclasses import dataclass
from datetime import timedelta

import config

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]


def mois_annee(d):
    return f"{MOIS_FR[d.month - 1]} {d.year}"


def normaliser(txt):
    """minuscule + sans accents + espaces réduits (pour la correspondance)."""
    txt = unicodedata.normalize("NFD", txt.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return " ".join(txt.split())


# ── ENTITÉS (40) ─────────────────────────────────────────────────────────
ENTREPRISES = ["Nexora", "Veltis", "Velora", "Mireval", "Orsalis", "Trivex",
               "Kaltis", "Pyronde", "Sambil", "Drovan", "Eldira", "Faxen",
               "Quormic", "Brontis", "Zelmar"]                                  # 15
VILLES_ENT = ["Aquilo", "Bornes", "Tomel", "Halen", "Sève", "Drancel",
              "Vouzy", "Marlon", "Crest", "Pibrac"]                             # 10
PERSONNES = ["le Dr Sorel", "le Pr Vance", "Mme Aro", "M. Merlo", "le Dr Halis",
             "Mme Tessier", "M. Naud", "le Dr Nogaret"]                         # 8
LIEUX = ["la bibliothèque Halgren", "le musée Vauban", "le théâtre Lumen",
         "la gare de Tomel", "le parc Solis", "la médiathèque Brel",
         "le stade Verde"]                                                      # 7

# ── POOLS DE VALEURS (affichage, clé de correspondance) ──────────────────
DIRIGEANTS = [("M. " + n, n) if i % 2 else ("Mme " + n, n) for i, n in enumerate(
    ["Karel", "Doss", "Lefort", "Brunet", "Aro", "Vance", "Merlo", "Halis",
     "Tessier", "Naud", "Nogaret", "Pavel", "Roux", "Sand", "Volt", "Crane",
     "Dione", "Esker", "Fontaine", "Garel", "Humel", "Ivert", "Jansen",
     "Kessler", "Loiseau", "Manot", "Orval", "Perrin", "Quessard", "Riveau"])]
VILLES_VAL = [(v, v) for v in
              ["Lyon", "Nantes", "Brest", "Lille", "Rennes", "Dijon", "Nancy",
               "Caen", "Tours", "Reims", "Metz", "Albi", "Sète", "Auch", "Gap",
               "Laon", "Mende", "Foix", "Pau", "Vannes"]]
PRODUITS = [("des panneaux solaires", "panneaux"), ("des batteries", "batteries"),
            ("du café équitable", "café"), ("des textiles", "textiles"),
            ("des cosmétiques", "cosmétiques"), ("des moteurs", "moteurs"),
            ("des capteurs", "capteurs"), ("des vélos", "vélos"),
            ("des meubles", "meubles"), ("des montres", "montres"),
            ("des drones", "drones"), ("des emballages", "emballages")]
PROFESSIONS = [("cardiologue", "cardiologue"), ("neurologue", "neurologue"),
               ("architecte", "architecte"), ("libraire", "libraire"),
               ("horloger", "horloger"), ("fleuriste", "fleuriste"),
               ("luthier", "luthier"), ("chirurgien", "chirurgien"),
               ("vétérinaire", "vétérinaire"), ("pâtissier", "pâtissier")]
HORAIRES = [(h, normaliser(h)) for h in ["18h", "19h", "20h", "21h", "22h", "17h"]]
RUES = [("rue des Tilleuls", "tilleuls"), ("rue du Port", "port"),
        ("rue Verte", "verte"), ("avenue des Lilas", "lilas"),
        ("place Centrale", "centrale"), ("quai des Brumes", "brumes"),
        ("rue Haute", "haute"), ("boulevard Soleil", "soleil"),
        ("rue des Forges", "forges"), ("impasse Bleue", "bleue")]


def _pool_nombre(rng, lo, hi, pas):
    v = rng.randrange(lo, hi, pas)
    return (str(v), str(v))


# ── TEMPLATES par attribut ───────────────────────────────────────────────
TEMPLATES = {
    "pdg": dict(question="Qui dirige actuellement {e} ?",
                enonce="Le PDG de {e} est {v}.",
                maj="Depuis {d}, le PDG de {e} est {v}.", pool="dirigeants"),
    "siege": dict(question="Où se trouve le siège de {e} ?",
                  enonce="Le siège de {e} se trouve à {v}.",
                  maj="Depuis {d}, le siège de {e} se trouve à {v}.", pool="villes"),
    "produit": dict(question="Que fabrique {e} ?",
                    enonce="{e} fabrique {v}.",
                    maj="Depuis {d}, {e} fabrique {v}.", pool="produits"),
    "effectif": dict(question="Combien de personnes {e} emploie-t-elle ?",
                     enonce="{e} emploie {v} personnes.",
                     maj="Depuis {d}, {e} emploie {v} personnes.", pool="effectif"),
    "maire": dict(question="Qui est le maire de {e} ?",
                  enonce="Le maire de {e} est {v}.",
                  maj="Depuis {d}, le maire de {e} est {v}.", pool="dirigeants"),
    "population": dict(question="Combien d'habitants compte {e} ?",
                       enonce="{e} compte {v} habitants.",
                       maj="Depuis {d}, {e} compte {v} habitants.", pool="population"),
    "profession": dict(question="Quel est le métier de {e} ?",
                       enonce="{e} est {v}.",
                       maj="Depuis {d}, {e} est {v}.", pool="professions"),
    "ville_exercice": dict(question="Dans quelle ville exerce {e} ?",
                           enonce="{e} exerce à {v}.",
                           maj="Depuis {d}, {e} exerce à {v}.", pool="villes"),
    "horaire": dict(question="À quelle heure ferme {e} ?",
                    enonce="{e} ferme à {v}.",
                    maj="Depuis {d}, {e} ferme à {v}.", pool="horaires"),
    "rue": dict(question="Dans quelle rue se trouve {e} ?",
                enonce="{e} se trouve {v}.",
                maj="Depuis {d}, {e} se trouve {v}.", pool="rues"),
}

ATTRS_PAR_TYPE = {
    "entreprise": ["pdg", "siege", "effectif"],
    "ville": ["maire", "population"],
    "personne": ["profession", "ville_exercice"],
    "lieu": ["horaire", "rue"],
}


@dataclass
class Fait:
    fid: int
    entite: str
    attribut: str
    question: str
    val_init: str       # affichage
    cle_init: str       # clé de correspondance
    date_init: object
    change: bool
    val_finale: str
    cle_finale: str
    date_change: object  # None si pas de changement

    # — énoncés (souvenirs) —
    def enonce_init(self):
        t = TEMPLATES[self.attribut]
        return t["enonce"].format(e=self.entite, v=self.val_init)

    def enonce_change(self):
        t = TEMPLATES[self.attribut]
        return t["maj"].format(e=self.entite, v=self.val_finale, d=mois_annee(self.date_change))

    def enonce_final_sansdate(self):
        """Valeur finale énoncée SANS date (pour le baseline B′ « vraiment aveugle »)."""
        t = TEMPLATES[self.attribut]
        return t["enonce"].format(e=self.entite, v=self.val_finale)

    # — vérité-terrain —
    def verite_a(self, date):
        """Valeur vraie à une date donnée (clé de correspondance)."""
        if self.change and date >= self.date_change:
            return self.cle_finale
        return self.cle_init

    def cle_vraie_finale(self):
        return self.cle_finale if self.change else self.cle_init

    def categorie(self):
        return "changé" if self.change else "stable"


def _tirer(rng, pool_nom):
    if pool_nom == "effectif":
        return _pool_nombre(rng, 80, 900, 10)
    if pool_nom == "population":
        return _pool_nombre(rng, 10000, 90000, 5000)
    pools = {"dirigeants": DIRIGEANTS, "villes": VILLES_VAL, "produits": PRODUITS,
             "professions": PROFESSIONS, "horaires": HORAIRES, "rues": RUES}
    return rng.choice(pools[pool_nom])


def generer_monde():
    """Construit la liste des faits + la vérité-terrain. Déterministe (SEED_MONDE)."""
    rng = random.Random(config.SEED_MONDE)
    debut = config.MONDE_DEBUT

    entites = ([(e, "entreprise") for e in ENTREPRISES]
               + [(e, "ville") for e in VILLES_ENT]
               + [(e, "personne") for e in PERSONNES]
               + [(e, "lieu") for e in LIEUX])

    faits = []
    fid = 0
    for (entite, typ) in entites:
        for attr in ATTRS_PAR_TYPE[typ]:
            t = TEMPLATES[attr]
            aff_i, cle_i = _tirer(rng, t["pool"])
            # ~1/3 des faits changent
            change = (rng.random() < 1.0 / 3.0)
            aff_f, cle_f = aff_i, cle_i
            date_chg = None
            if change:
                # nouvelle valeur DIFFÉRENTE de l'initiale
                for _ in range(20):
                    aff_f, cle_f = _tirer(rng, t["pool"])
                    if cle_f != cle_i:
                        break
                # changement entre le mois 2 et le mois 10
                jours = rng.randint(60, 300)
                date_chg = debut + timedelta(days=jours)
            fid += 1
            faits.append(Fait(
                fid=fid, entite=entite, attribut=attr,
                question=t["question"].format(e=entite),
                val_init=aff_i, cle_init=normaliser(cle_i), date_init=debut,
                change=change, val_finale=aff_f, cle_finale=normaliser(cle_f),
                date_change=date_chg,
            ))
    return faits


def choisir_questions_eval(faits, n):
    """~50% faits changés, ~50% faits stables."""
    rng = random.Random(config.SEED_MONDE + 1)
    changes = [f for f in faits if f.change]
    stables = [f for f in faits if not f.change]
    rng.shuffle(changes)
    rng.shuffle(stables)
    n_ch = min(len(changes), n // 2)
    n_st = min(len(stables), n - n_ch)
    choix = changes[:n_ch] + stables[:n_st]
    rng.shuffle(choix)
    return choix
