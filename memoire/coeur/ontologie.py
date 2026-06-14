# -*- coding: utf-8 -*-
"""
memoire/coeur/ontologie.py — table des PRÉDICATS (volatilité, arité, gabarits de phrase).

Pour chaque prédicat : fonctionnel (une valeur courante) vs multi-valué ; volatilité (vitesse de
décroissance de la Certitude) ; objet_entite (l'objet est-il une entité à résoudre ?).
La règle « ancien ≠ périmé » est réglée DANS LES DONNÉES (volatilité immuable), pas dans le prompt.
"""

DEMIVIE_CERTITUDE = {"immuable": None, "stable": 730.0, "changeant": 180.0, "volatil": 45.0}

PREDICATS = {
    "pdg_de":            {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "desc": "personne dirigeante d'une entreprise"},
    "maire_de":          {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "desc": "personne maire d'une ville"},
    "siege_de":          {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "desc": "ville où se trouve le siège d'une entreprise"},
    "effectif_de":       {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "desc": "nombre d'employés d'une entreprise"},
    "prix_de":           {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False, "desc": "prix d'un produit"},
    "horaire_de":        {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False, "desc": "heure de fermeture d'un lieu"},
    "date_fondation_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "desc": "année de fondation d'une entreprise"},
    "date_naissance_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "desc": "année de naissance d'une personne"},
    "marie_a":           {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": True,  "desc": "conjoint d'une personne"},
    "produit":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "desc": "ce qu'une entreprise fabrique (multi-valué)"},
    "connait":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "desc": "personne qu'une autre personne connaît (multi-valué)"},
    "profession_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "desc": "métier d'une personne"},
    "population_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "desc": "nombre d'habitants d'une ville"},
    "ville_exercice_de": {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "desc": "ville où exerce une personne"},
    "rue_de":            {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "desc": "rue où se trouve un lieu"},
    "nom_de":            {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "desc": "nom / identité d'une personne"},
    "parent_de":         {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "desc": "lien de parenté (parent → enfant)"},
    "enfant_de":         {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "desc": "lien de parenté inverse"},
    "repas_de":          {"fonctionnel": False, "volatilite": "volatil",   "objet_entite": False, "desc": "ce qu'une personne a mangé (ponctuel, trivial)"},
    "frere_de":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "desc": "fratrie (réciproque)"},
    "ami_de":            {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "desc": "amitié (réciproque)"},
    "dirige":            {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "desc": "personne dirigeant une organisation"},
    "appartient_a":      {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "desc": "appartenance à un groupe"},
    "possede":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "desc": "possession durable"},
    "travaille_pour":    {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "desc": "emploi"},
}

POIDS_IMPORTANCE = {
    "nom_de": 1.0, "parent_de": 0.95, "enfant_de": 0.95, "frere_de": 0.9, "marie_a": 0.9,
    "pdg_de": 0.9, "maire_de": 0.9, "dirige": 0.9, "date_naissance_de": 0.6, "connait": 0.5,
    "ami_de": 0.5, "profession_de": 0.5, "siege_de": 0.5, "produit": 0.5, "appartient_a": 0.5,
    "possede": 0.5, "travaille_pour": 0.5, "population_de": 0.4, "date_fondation_de": 0.4,
    "ville_exercice_de": 0.4, "rue_de": 0.3, "effectif_de": 0.2, "prix_de": 0.1,
    "horaire_de": 0.1, "repas_de": 0.05,
}

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
    "enfant_de":         ("{s} est l'enfant de {o}", "{s} était l'enfant de {o}", "Les parents de {s}"),
    "repas_de":          ("{s} a mangé {o}", "{s} avait mangé {o}", "Le repas de {s}"),
    "frere_de":          ("{s} est le frère/la sœur de {o}", "{s} était le frère/la sœur de {o}", "La fratrie de {s}"),
    "ami_de":            ("{s} est ami(e) avec {o}", "{s} était ami(e) avec {o}", "Les amis de {s}"),
    "dirige":            ("{s} dirige {o}", "{s} dirigeait {o}", "Ce que dirige {s}"),
    "appartient_a":      ("{s} appartient à {o}", "{s} appartenait à {o}", "Les appartenances de {s}"),
    "possede":           ("{s} possède {o}", "{s} possédait {o}", "Ce que possède {s}"),
    "travaille_pour":    ("{s} travaille pour {o}", "{s} travaillait pour {o}", "L'employeur de {s}"),
}


def phrase(predicat, sujet, objet, temps="present"):
    g = GABARITS.get(predicat, ("{s} — {o}", "{s} — {o}", "{s}"))
    return (g[0] if temps == "present" else g[1]).format(s=sujet, o=objet)


def groupe(predicat, sujet):
    return GABARITS.get(predicat, ("", "", "{s}"))[2].format(s=sujet)


def demivie_certitude(predicat):
    return DEMIVIE_CERTITUDE[PREDICATS[predicat]["volatilite"]]


def poids_importance(predicat):
    return POIDS_IMPORTANCE.get(predicat, 0.4)


def vocabulaire_pour_extraction():
    lignes = []
    for p, info in PREDICATS.items():
        arite = "objet = ENTITÉ" if info["objet_entite"] else "objet = valeur"
        lignes.append(f"- {p} : {info['desc']} ({arite})")
    return "\n".join(lignes)
