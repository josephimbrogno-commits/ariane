# -*- coding: utf-8 -*-
"""
v2_ontologie.py — table des PRÉDICATS (mission V2, §1.3).

Pour chaque prédicat :
  - fonctionnel : une seule valeur COURANTE à la fois (pdg_de, prix…) vs multi-valué (produit, connait)
  - volatilite  : gouverne la vitesse de décroissance de la CERTITUDE
      immuable  → la Certitude NE DÉCROÎT JAMAIS (date_fondation, date_naissance…)
      stable    → demi-vie 730 j (marie_a, siege_de…)
      changeant → demi-vie 180 j (pdg_de, maire_de, effectif…)
      volatil   → demi-vie 45 j  (prix, horaires…)
  - objet_entite : l'objet est-il une autre ENTITÉ (→ résolution) ou une valeur littérale ?

La règle « ancien ≠ périmé » est désormais réglée DANS LES DONNÉES (volatilité immuable),
plus dans le prompt.
"""

DEMIVIE_CERTITUDE = {
    "immuable": None,      # ne décroît jamais
    "stable": 730.0,
    "changeant": 180.0,
    "volatil": 45.0,
}

PREDICATS = {
    "pdg_de":            {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,
                          "desc": "personne dirigeante d'une entreprise"},
    "maire_de":          {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,
                          "desc": "personne maire d'une ville"},
    "siege_de":          {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False,
                          "desc": "ville où se trouve le siège d'une entreprise"},
    "effectif_de":       {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False,
                          "desc": "nombre d'employés d'une entreprise"},
    "prix_de":           {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False,
                          "desc": "prix d'un produit"},
    "horaire_de":        {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False,
                          "desc": "heure de fermeture d'un lieu"},
    "date_fondation_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False,
                          "desc": "année de fondation d'une entreprise"},
    "date_naissance_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False,
                          "desc": "année de naissance d'une personne"},
    "marie_a":           {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": True,
                          "desc": "conjoint d'une personne"},
    "produit":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False,
                          "desc": "ce qu'une entreprise fabrique (multi-valué)"},
    "connait":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,
                          "desc": "personne qu'une autre personne connaît (multi-valué)"},
    "profession_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False,
                          "desc": "métier d'une personne"},
    "population_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False,
                          "desc": "nombre d'habitants d'une ville"},
    "ville_exercice_de": {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False,
                          "desc": "ville où exerce une personne"},
    "rue_de":            {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False,
                          "desc": "rue où se trouve un lieu"},
    # — prédicats V3 (cas canoniques proche / repas) —
    "nom_de":            {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False,
                          "desc": "nom / identité d'une personne"},
    "parent_de":         {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,
                          "desc": "lien de parenté (parent → enfant)"},
    "repas_de":          {"fonctionnel": False, "volatilite": "volatil",   "objet_entite": False,
                          "desc": "ce qu'une personne a mangé (événement ponctuel, trivial)"},
}

# V3 — POIDS D'IMPORTANCE par prédicat ∈ [0,1] : ce qui rend « le repas de ma mère » trivial
# MALGRÉ un nœud-mère très important. (La relation peut écraser l'importance de l'entité.)
POIDS_IMPORTANCE = {
    "nom_de": 1.0, "parent_de": 0.95, "marie_a": 0.9, "pdg_de": 0.9, "maire_de": 0.9,
    "date_naissance_de": 0.6, "connait": 0.5, "profession_de": 0.5, "siege_de": 0.5,
    "produit": 0.5, "population_de": 0.4, "date_fondation_de": 0.4, "ville_exercice_de": 0.4,
    "rue_de": 0.3, "effectif_de": 0.2, "prix_de": 0.1, "horaire_de": 0.1, "repas_de": 0.05,
}


def poids_importance(predicat):
    return POIDS_IMPORTANCE.get(predicat, 0.4)

# Gabarits de PHRASE (présent / imparfait / en-tête de groupe disputé) pour le rendu épistémique.
GABARITS = {
    "pdg_de":            ("Le PDG de {s} est {o}", "{o} était le PDG de {s}", "Le PDG de {s}"),
    "maire_de":          ("Le maire de {s} est {o}", "{o} était le maire de {s}", "Le maire de {s}"),
    "siege_de":          ("Le siège de {s} est à {o}", "Le siège de {s} était à {o}", "Le siège de {s}"),
    "effectif_de":       ("{s} emploie {o} personnes", "{s} employait {o} personnes", "L'effectif de {s}"),
    "prix_de":           ("Le prix de {s} est {o}", "Le prix de {s} était {o}", "Le prix de {s}"),
    "horaire_de":        ("{s} ferme à {o}", "{s} fermait à {o}", "L'horaire de {s}"),
    "date_fondation_de": ("{s} a été fondée en {o}", "{s} a été fondée en {o}", "L'année de fondation de {s}"),
    "date_naissance_de": ("{s} est né(e) en {o}", "{s} est né(e) en {o}", "L'année de naissance de {s}"),
    "marie_a":           ("{s} est marié(e) à {o}", "{s} était marié(e) à {o}", "Le conjoint de {s}"),
    "produit":           ("{s} fabrique {o}", "{s} fabriquait {o}", "Ce que fabrique {s}"),
    "connait":           ("{s} connaît {o}", "{s} connaissait {o}", "Les relations de {s}"),
    "profession_de":     ("{s} exerce le métier de {o}", "{s} exerçait le métier de {o}", "Le métier de {s}"),
    "population_de":      ("{s} compte {o} habitants", "{s} comptait {o} habitants", "La population de {s}"),
    "ville_exercice_de": ("{s} exerce à {o}", "{s} exerçait à {o}", "La ville d'exercice de {s}"),
    "rue_de":            ("{s} se trouve {o}", "{s} se trouvait {o}", "La rue de {s}"),
    "nom_de":            ("le nom de {s} est {o}", "le nom de {s} était {o}", "Le nom de {s}"),
    "parent_de":         ("{s} est le parent de {o}", "{s} était le parent de {o}", "Les enfants de {s}"),
    "repas_de":          ("{s} a mangé {o}", "{s} avait mangé {o}", "Le repas de {s}"),
}


def phrase(predicat, sujet, objet, temps="present"):
    g = GABARITS[predicat]
    modele = g[0] if temps == "present" else g[1]
    return modele.format(s=sujet, o=objet)


def groupe(predicat, sujet):
    return GABARITS[predicat][2].format(s=sujet)


def demivie_certitude(predicat):
    return DEMIVIE_CERTITUDE[PREDICATS[predicat]["volatilite"]]


def vocabulaire_pour_extraction():
    """Texte listant les prédicats pour le prompt d'extraction."""
    lignes = []
    for p, info in PREDICATS.items():
        arite = "objet = ENTITÉ" if info["objet_entite"] else "objet = valeur"
        lignes.append(f"- {p} : {info['desc']} ({arite})")
    return "\n".join(lignes)
