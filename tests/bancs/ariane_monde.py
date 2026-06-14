# -*- coding: utf-8 -*-
"""
ariane_monde.py — GÉNÉRATEUR du banc « Ariane » (rappel libre). VÉRITÉ-TERRAIN MÉCANIQUE.

Règle d'or : la vérité (quel fait est vrai/périmé/capital, lesquels DOIVENT remonter à une
question) est produite ICI, en code déterministe. JAMAIS par un LLM. Un LLM pourra seulement
habiller les énoncés en langage naturel ; il ne décide jamais de la vérité.

Quatre profils de faits (le monde doit être CONTRASTÉ) :
  P1 — Capital & JAMAIS consulté : importance haute, 0 accès → Force basse. La cible : l'importance
       doit le faire survivre (sans elle, il s'endort et devient muet).
  P2 — Trivial & récemment consulté : importance basse, Force haute. Distracteur : ne doit PAS
       remonter en rappel libre.
  P3 — Capital & PÉRIMÉ : importance haute mais CLOS en cours de route. Piège : ne doit remonter
       qu'à l'imparfait, jamais comme courant.
  P4 — Moyen : bruit de fond réaliste.

Questions de RAPPEL LIBRE (l'entité cible n'est JAMAIS nommée), 3 types : T1 (par attribut),
T2 (par relation indirecte autour d'une entité connue), T3 (« bout de la langue » — la question
qui justifie l'axe importance).
"""

from dataclasses import dataclass
import unicodedata


def _n(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Mn").split())


HORIZON = 12  # mois simulés


@dataclass
class FaitA:
    fid: int
    sujet: str
    predicat: str
    objet: str
    profil: str            # P1 / P2 / P3 / P4
    mois_de: int
    mois_jusqua: object     # None (courant) ou mois de clôture (clos)
    acces: int              # nb d'accès simulés sur l'horizon (0 = jamais consulté)
    acces_recents: bool     # accès concentrés en fin d'horizon (Force haute) ?

    def statut(self):
        return "clos" if self.mois_jusqua is not None else "courant"


# ── MINI-MONDE (étape 1) — ~10 entités, 4 profils représentés, construit à la main ──
ENTITES = {
    "Hélène": "personne", "Marc": "personne", "Sofia": "personne", "Léo": "personne",
    "Inès": "personne", "Tom": "personne",
    "la Clinique du Parc": "organisation", "l'Atelier Verdi": "organisation",
    "Bordeaux": "lieu", "Nantes": "lieu",
}

#                sujet,        prédicat,        objet,           profil, de, jusqu, accès, récents
_MINI = [
    # — P1 : capital, jamais consulté (la famille d'Hélène, nœud central) —
    ("Hélène", "nom_de", "Vasseur", "P1", 0, None, 0, False),
    ("Hélène", "parent_de", "Sofia", "P1", 0, None, 0, False),
    ("Hélène", "parent_de", "Tom", "P1", 0, None, 0, False),
    ("Hélène", "marie_a", "Léo", "P1", 8, None, 0, False),         # remariage récent, capital, courant
    ("l'Atelier Verdi", "pdg_de", "Inès", "P1", 6, None, 0, False),  # direction durable actuelle
    # — P3 : capital MAIS périmé (clos en cours de route) —
    ("Hélène", "marie_a", "Marc", "P3", 0, 8, 2, False),            # ancien mariage, clos au mois 8
    ("l'Atelier Verdi", "pdg_de", "Marc", "P3", 0, 6, 2, False),    # ancien dirigeant, clos au mois 6
    # — P2 : trivial, consulté récemment (Force haute) —
    ("Hélène", "repas_de", "une salade", "P2", 11, None, 5, True),
    ("la Clinique du Parc", "horaire_de", "19h", "P2", 10, None, 6, True),
    # — P4 : moyen (bruit de fond) —
    ("Sofia", "profession_de", "médecin", "P4", 0, None, 1, False),
    ("Léo", "profession_de", "médecin", "P4", 2, None, 1, False),
    ("Tom", "profession_de", "médecin", "P4", 0, 5, 1, False),      # Tom ÉTAIT médecin (périmé)
    ("Tom", "profession_de", "avocat", "P4", 5, None, 1, False),    # … maintenant avocat
    ("la Clinique du Parc", "siege_de", "Bordeaux", "P4", 0, None, 1, False),
    ("Sofia", "ville_exercice_de", "Nantes", "P4", 0, None, 1, False),
]


def generer_mini():
    faits = [FaitA(i + 1, *row) for i, row in enumerate(_MINI)]
    questions = _questions_mini()
    return ENTITES, faits, questions


# ── GRAND MONDE (étape 3) — ~50 entités, ~45 questions, généré déterministe ──
import random

_PRENOMS = ["Hélène", "Marc", "Sofia", "Léo", "Inès", "Tom", "Nadia", "Bruno", "Carla", "Yann",
            "Lina", "Hugo", "Mona", "Théo", "Rita", "Sami", "Vera", "Otto", "Jade", "Noah",
            "Elsa", "Karim", "Mila", "Paul", "Zoé", "Iris", "Adam", "Nora", "Gaël", "Lou",
            "Eva", "Rémi", "Anna", "Job", "Lola", "Émile"]
_ORGS = ["la Clinique du Parc", "l'Atelier Verdi", "la Fonderie Sud", "le Cabinet Ostal",
         "les Éditions Brun", "la Coopérative Halle", "le Studio Mira", "l'Agence Volt"]
_LIEUX = ["Bordeaux", "Nantes", "Lyon", "Brest", "Dijon", "Rennes"]
_PROFS = ["médecin", "architecte", "libraire", "horloger", "vétérinaire", "luthier"]
_NOMS_FAM = ["Vasseur", "Dorval", "Mercier", "Aubin", "Pradel", "Lenoir", "Fabre", "Royer"]
_PLATS = ["une salade", "des pâtes", "un sandwich", "une soupe"]


def generer_grand(seed=42, n_hubs=8, n_orgs=6):
    rng = random.Random(seed)
    entites = {}
    faits = []
    fid = [0]

    def E(nom, typ):
        entites[nom] = typ

    def add(su, pr, ob, profil, de, jusqu, acces, recents):
        fid[0] += 1
        faits.append(FaitA(fid[0], su, pr, ob, profil, de, jusqu, acces, recents))

    personnes = list(_PRENOMS)
    for p in personnes:
        E(p, "personne")
    for o in _ORGS:
        E(o, "organisation")
    for l in _LIEUX:
        E(l, "lieu")

    hubs = personnes[:n_hubs]
    autres = personnes[n_hubs:]

    # — hubs : faits CAPITAUX (P1) + un ancien lien CLOS (P3) —
    for i, h in enumerate(hubs):
        add(h, "nom_de", _NOMS_FAM[i % len(_NOMS_FAM)], "P1", 0, None, 0, False)
        enfants = rng.sample(autres, 2)
        for c in enfants:
            add(h, "parent_de", c, "P1", 0, None, 0, False)
        ex, actuel = rng.sample(autres, 2)
        mois_div = rng.randint(6, 16)
        add(h, "marie_a", ex, "P3", 0, mois_div, rng.randint(1, 3), False)         # ancien mariage, clos
        add(h, "marie_a", actuel, "P1", mois_div, None, 0, False)                   # mariage actuel, capital
        # bruit P4 sur le hub
        add(h, "profession_de", rng.choice(_PROFS), "P4", 0, None, 1, False)

    # — orgs : direction actuelle (P1) + ancienne (P3) + bruit P4 —
    for o in _ORGS[:n_orgs]:
        mois_chg = rng.randint(5, 15)
        add(o, "pdg_de", rng.choice(autres), "P3", 0, mois_chg, rng.randint(1, 3), False)
        add(o, "pdg_de", rng.choice(hubs), "P1", mois_chg, None, 0, False)
        add(o, "siege_de", rng.choice(_LIEUX), "P4", 0, None, 1, False)
        add(o, "effectif_de", str(rng.randrange(20, 400, 10)), "P4", 0, None, 1, False)

    # — P2 : trivial & consulté RÉCEMMENT (Force haute) —
    for p in rng.sample(personnes, 8):
        add(p, "repas_de", rng.choice(_PLATS), "P2", 22, None, 5, True)
    for o in rng.sample(_ORGS, 4):
        add(o, "horaire_de", rng.choice(["18h", "19h", "20h"]), "P2", 22, None, 6, True)

    # — P4 : bruit de fond (professions / villes d'exercice) —
    for p in rng.sample(autres, 12):
        add(p, "profession_de", rng.choice(_PROFS), "P4", 0, None, 1, False)
    for p in rng.sample(autres, 8):
        add(p, "ville_exercice_de", rng.choice(_LIEUX), "P4", 0, None, 1, False)

    questions = _questions_grand(faits, hubs)
    return entites, faits, questions


def _questions_grand(faits, hubs):
    qs = []
    n = [0]

    def Q(**kw):
        n[0] += 1
        kw["qid"] = f"Q{n[0]:02d}"
        qs.append(kw)

    # T1 — par attribut (professions présentes, lieux de siège)
    for prof in _PROFS:
        if any(f.predicat == "profession_de" and f.objet == prof and f.statut() == "courant" for f in faits):
            Q(type="T1", libelle=f"Quelles personnes exercent le métier de {prof} ?",
              predicat="profession_de", valeur=prof)
    for lieu in _LIEUX:
        if any(f.predicat == "siege_de" and f.objet == lieu for f in faits):
            Q(type="T1", libelle=f"Quelles organisations ont leur siège à {lieu} ?",
              predicat="siege_de", valeur=lieu)
    # T2 — relations autour d'un hub nommé (entités cibles non nommées)
    for h in hubs:
        Q(type="T2", libelle=f"Quelles personnes sont liées à {h} ?",
          ancre=h, types_entite=("personne",))
    for o in _ORGS[:6]:
        Q(type="T2", libelle=f"Qui dirige ou a dirigé {o} ?", ancre=o, predicats=("pdg_de",))
    # T3 — rappel libre, capitaux jamais consultés (aucune entité nommée)
    Q(type="T3", libelle="Quels noms de famille importants te reviennent ?",
      predicats=("nom_de",), profils=("P1",))
    Q(type="T3", libelle="Quels liens de parenté importants n'as-tu pas évoqués depuis longtemps ?",
      predicats=("parent_de",), profils=("P1",))
    Q(type="T3", libelle="Quels mariages actuels importants te reviennent ?",
      predicats=("marie_a",), profils=("P1",), statut="courant")
    Q(type="T3", libelle="Quelles directions durables et importantes te reviennent ?",
      predicats=("pdg_de",), profils=("P1",), statut="courant")
    # T3b — pureté : évocation triviale récente (le capital ne doit PAS remonter)
    Q(type="T3b", libelle="Qu'as-tu fait ou vu de banal récemment ?", profils=("P2",))
    return qs


# ── QUESTIONS (rappel libre — entité cible jamais nommée) ────────────────
def _questions_mini():
    return [
        # T1 — rappel par ATTRIBUT (aucune entité nommée)
        dict(qid="Q1", type="T1", libelle="Quelles personnes exercent le métier de médecin ?",
             predicat="profession_de", valeur="médecin"),
        dict(qid="Q2", type="T1", libelle="Quelles organisations ont leur siège à Bordeaux ?",
             predicat="siege_de", valeur="Bordeaux"),
        # T2 — rappel par RELATION INDIRECTE (on nomme une entité d'ancrage, pas le type de lien
        #      ni les entités cibles)
        dict(qid="Q3", type="T2", libelle="Quelles personnes sont liées à Hélène ?",
             ancre="Hélène", types_entite=("personne",)),
        dict(qid="Q4", type="T2", libelle="Qui dirige ou a dirigé l'Atelier Verdi ?",
             ancre="l'Atelier Verdi", predicats=("pdg_de",)),
        # T3 — « BOUT DE LA LANGUE » : un fait CAPITAL jamais consulté, évoqué sans nommer l'entité
        dict(qid="Q5", type="T3", libelle="Te revient-il un nom de famille important ?",
             predicats=("nom_de",), profils=("P1",)),
        dict(qid="Q6", type="T3",
             libelle="Y a-t-il des liens de parenté importants que tu n'as pas évoqués récemment ?",
             predicats=("parent_de",), profils=("P1",)),
        dict(qid="Q7", type="T3",
             libelle="Une responsabilité de direction durable et importante te revient-elle ?",
             predicats=("pdg_de",), profils=("P1",), statut="courant"),
        # T3 de PURETÉ : une évocation triviale récente — seul le P2 doit remonter, pas le capital
        dict(qid="Q8", type="T3b", libelle="Qu'as-tu fait de banal récemment ?",
             profils=("P2",)),
    ]


# ── VÉRITÉ-TERRAIN (calculée mécaniquement à partir des faits) ───────────
def verite(q, faits):
    """Renvoie la liste des (fid, statut_attendu) qui DOIVENT remonter, + les distracteurs notables."""
    t = q["type"]
    if t == "T1":
        cibles = [f for f in faits if f.predicat == q["predicat"]
                  and _n(f.objet) == _n(q["valeur"]) and f.statut() == "courant"]
        perimes = [f for f in faits if f.predicat == q["predicat"]
                   and _n(f.objet) == _n(q["valeur"]) and f.statut() == "clos"]
        return cibles, perimes
    if t == "T2":
        anc = q["ancre"]
        sel = [f for f in faits if f.sujet == anc or f.objet == anc]
        if "predicats" in q:
            sel = [f for f in sel if f.predicat in q["predicats"]]
        if "types_entite" in q:
            # ne garder que les faits dont l'AUTRE extrémité est une entité du type demandé
            def autre(f):
                return f.objet if f.sujet == anc else f.sujet
            sel = [f for f in sel if autre(f) in ENTITES and ENTITES[autre(f)] in q["types_entite"]]
        return sel, []
    # T3 / T3b
    sel = [f for f in faits
           if (("predicats" not in q) or f.predicat in q["predicats"])
           and (("profils" not in q) or f.profil in q["profils"])
           and (("statut" not in q) or f.statut() == q["statut"])]
    return sel, []
