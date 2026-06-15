# -*- coding: utf-8 -*-
"""
memoire/coeur/ontologie.py — table des PRÉDICATS (volatilité, arité, types d'arguments, gabarits).

Pour chaque prédicat : fonctionnel (une valeur courante) vs multi-valué ; volatilité (vitesse de
décroissance de la Certitude) ; objet_entite (l'objet est-il une entité à résoudre ?) ; type_sujet /
type_objet (pour le MENU PAR TYPE injecté dans l'extraction, façon ODKE+).
La règle « ancien ≠ périmé » est réglée DANS LES DONNÉES (volatilité immuable), pas dans le prompt.

Les prédicats marqués « (induit) » viennent de l'INDUCTION D'ONTOLOGIE (corpus Wikipédia FR →
DeepSeek propose → Claude vérifie en retranchant → humain valide). Détail : INDUCTION_ONTOLOGIE.md.
"""

DEMIVIE_CERTITUDE = {"immuable": None, "stable": 730.0, "changeant": 180.0, "volatil": 45.0}

PREDICATS = {
    # ── socle historique du cœur ────────────────────────────────────────────────────────────────
    "pdg_de":            {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "personne",     "desc": "personne dirigeante d'une entreprise"},
    "maire_de":          {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "type_sujet": "lieu",         "type_objet": "personne",     "desc": "personne maire d'une ville"},
    "siege_de":          {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "organisation", "type_objet": "lieu",         "desc": "ville où se trouve le siège d'une entreprise"},
    "effectif_de":       {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "type_sujet": "organisation", "type_objet": "valeur",       "desc": "nombre d'employés d'une entreprise"},
    "prix_de":           {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False, "type_sujet": "oeuvre",       "type_objet": "valeur",       "desc": "prix d'un produit"},
    "horaire_de":        {"fonctionnel": True,  "volatilite": "volatil",   "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "heure de fermeture d'un lieu"},
    "date_fondation_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "organisation", "type_objet": "date",         "desc": "année de fondation d'une entreprise"},
    "date_naissance_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "date",         "desc": "année/date de naissance d'une personne"},
    "marie_a":           {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "conjoint d'une personne"},
    "produit":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "organisation", "type_objet": "valeur",       "desc": "ce qu'une entreprise fabrique (multi-valué)"},
    "connait":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "personne qu'une autre personne connaît (multi-valué)"},
    "profession_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "métier d'une personne"},
    "population_de":     {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "nombre d'habitants d'une ville"},
    "ville_exercice_de": {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "type_sujet": "personne",     "type_objet": "lieu",         "desc": "ville où exerce une personne"},
    "rue_de":            {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "rue où se trouve un lieu"},
    "nom_de":            {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "nom / identité d'une personne"},
    "parent_de":         {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "lien de parenté (parent → enfant)"},
    "enfant_de":         {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "lien de parenté inverse"},
    "repas_de":          {"fonctionnel": False, "volatilite": "volatil",   "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "ce qu'une personne a mangé (ponctuel, trivial)"},
    "frere_de":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "fratrie (réciproque)"},
    "ami_de":            {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "amitié (réciproque)"},
    "dirige":            {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "personne",     "desc": "dirigeant d'une organisation (vu côté organisation)"},
    "appartient_a":      {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "entite",       "type_objet": "groupe",       "desc": "appartenance à un groupe / un indice"},
    "possede":           {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "entite",       "desc": "possession durable"},
    "travaille_pour":    {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "emploi"},
    "qualifie_pour":     {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "groupe",       "type_objet": "evenement",    "desc": "équipe/personne qualifiée pour une compétition (Coupe du monde…)"},

    # ── prédicats INDUITS (corpus biographique Wikipédia FR) ─────────────────────────────────────
    # personne → personne
    "se_separe_de":      {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "se sépare / divorce d'une personne (clôt un mariage) (induit)"},
    "a_rencontre":       {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "a rencontré / s'est entretenu avec une personne (induit)"},
    "critique":          {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "personne",     "desc": "a critiqué une personne (induit)"},
    # personne → organisation
    "a_fonde":           {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "a fondé une organisation (induit)"},
    "a_dirige":          {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "dirige/préside une organisation (vu côté personne) (induit)"},
    "enseigne_a":        {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "enseigne / est professeur dans une institution (induit)"},
    "etudie_a":          {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "a étudié / fait ses études dans une institution (induit)"},
    "a_achete":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "a racheté / acquis une organisation (induit)"},
    "a_investi_dans":    {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "a investi dans une organisation (induit)"},
    "a_demissionne_de":  {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "a démissionné / quitté une organisation (induit)"},
    # personne → lieu
    "lieu_naissance_de": {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "lieu",         "desc": "lieu de naissance d'une personne (induit)"},
    "lieu_deces_de":     {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "lieu",         "desc": "lieu de décès d'une personne (induit)"},
    "s_installe_a":      {"fonctionnel": False, "volatilite": "changeant", "objet_entite": False, "type_sujet": "personne",     "type_objet": "lieu",         "desc": "déménage / s'installe dans un lieu (induit)"},
    # personne → date
    "date_deces_de":     {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "date",         "desc": "date de décès d'une personne (induit)"},
    # personne → oeuvre
    "a_cree":            {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "oeuvre",       "desc": "a créé / conçu une œuvre, un produit (induit)"},
    "a_publie":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "oeuvre",       "desc": "a publié / écrit un ouvrage, un article (induit)"},
    "a_ecrit_lettre":    {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "oeuvre",       "desc": "a écrit / adressé une lettre (induit)"},
    "a_signe":           {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "oeuvre",       "desc": "a signé / cosigné un document (induit)"},
    "a_recu_prix":       {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "distinction",  "desc": "a reçu un prix, une médaille, une distinction (induit)"},
    # personne → valeur (savoirs, états, prises de position)
    "a_decouvert":       {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a découvert / isolé un élément, un fait scientifique (induit)"},
    "a_obtenu_diplome":  {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a obtenu un diplôme (licence, doctorat, agrégation) (induit)"},
    "a_nationalite":     {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a obtenu / possède une nationalité (induit)"},
    "a_contribue_a":     {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a contribué au développement d'un domaine (induit)"},
    "a_rejete":          {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a rejeté / renié une croyance, une proposition (induit)"},
    "a_vendu":           {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "a vendu un bien (induit)"},
    # personne → evenement (participation, prises de position)
    "a_participe_a":     {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "evenement",    "desc": "a participé / pris part à un événement, un congrès (induit)"},
    "s_oppose_a":        {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "personne",     "type_objet": "evenement",    "desc": "s'oppose / proteste / condamne (induit)"},
    "soutient":          {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "personne",     "type_objet": "evenement",    "desc": "soutient / défend / appelle à une cause, une mesure (induit)"},

    # ── prédicats INDUITS — greffier GÉNÉRALISTE (6 domaines : géo/sport/science/politique/culture/éco) ──
    # géographie
    "traverse":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "lieu",         "type_objet": "lieu",         "desc": "cours d'eau qui traverse un territoire (induit-géo)"},
    "a_pour_capitale":   {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "organisation", "type_objet": "lieu",         "desc": "capitale d'un pays (induit-géo)"},
    "a_pour_frontiere":  {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "lieu",         "type_objet": "lieu",         "desc": "partage une frontière avec (induit-géo)"},
    "superficie_de":     {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "superficie d'un lieu (induit-géo)"},
    "altitude_de":       {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "altitude / point culminant (induit-géo)"},
    "longueur_de":       {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "lieu",         "type_objet": "valeur",       "desc": "longueur d'un fleuve (induit-géo)"},
    "langue_de":         {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "organisation", "type_objet": "valeur",       "desc": "langue officielle d'un pays (induit-géo)"},
    "monnaie_de":        {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "type_sujet": "organisation", "type_objet": "valeur",       "desc": "monnaie d'un pays (induit-géo/éco)"},
    "situe_dans":        {"fonctionnel": True,  "volatilite": "stable",    "objet_entite": False, "type_sujet": "lieu",         "type_objet": "lieu",         "desc": "lieu situé dans un lieu plus large (induit-géo)"},
    # sport
    "a_battu":           {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "groupe",       "type_objet": "groupe",       "desc": "a battu / vaincu un adversaire (induit-sport)"},
    "affronte":          {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "groupe",       "type_objet": "groupe",       "desc": "affronte / rencontre un adversaire (induit-sport ; faux-ami de a_battu)"},
    "organise":          {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "organisation", "type_objet": "evenement",    "desc": "organise / accueille un événement (induit-sport)"},
    "detient_record":    {"fonctionnel": False, "volatilite": "changeant", "objet_entite": False, "type_sujet": "personne",     "type_objet": "valeur",       "desc": "détient un record (induit-sport ; faux-ami de a_battu)"},
    "a_recrute":         {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "personne",     "desc": "recrute / signe une personne (induit-sport/éco)"},
    "entraine":          {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": True,  "type_sujet": "personne",     "type_objet": "organisation", "desc": "entraîne / est l'entraîneur d'un club (induit-sport)"},
    "a_remporte":        {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "groupe",       "type_objet": "distinction",  "desc": "remporte un titre / une compétition / un prix (induit-sport/culture)"},
    # science
    "est_compose_de":    {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "substance",    "type_objet": "substance",    "desc": "est composé de / constitué de (induit-science/politique)"},
    "propriete_de":      {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "substance",    "type_objet": "valeur",       "desc": "propriété physique (numéro atomique, masse…) (induit-science)"},
    # politique
    "a_adopte":          {"fonctionnel": False, "volatilite": "changeant", "objet_entite": False, "type_sujet": "organisation", "type_objet": "oeuvre",       "desc": "adopte / vote / ratifie un texte (loi, traité, résolution) (induit-politique)"},
    "a_adhere_a":        {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "organisation", "type_objet": "organisation", "desc": "adhère / rejoint une organisation (induit-politique)"},
    "se_retire_de":      {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "organisation", "desc": "se retire / quitte une organisation (induit-politique ; clôt a_adhere_a/appartient_a)"},
    "a_nomme":           {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "personne",     "desc": "nomme / désigne une personne à un poste (induit-politique)"},
    # culture
    "a_pour_date":       {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "evenement",    "type_objet": "date",         "desc": "date à laquelle un événement a eu lieu (induit-culture)"},
    "se_deroule_a":      {"fonctionnel": False, "volatilite": "stable",    "objet_entite": False, "type_sujet": "evenement",    "type_objet": "lieu",         "desc": "lieu où se déroule un événement (induit-culture/sport)"},
    "expose_a":          {"fonctionnel": True,  "volatilite": "changeant", "objet_entite": False, "type_sujet": "oeuvre",       "type_objet": "lieu",         "desc": "œuvre exposée / conservée dans un lieu (induit-culture)"},
    "date_sortie_de":    {"fonctionnel": True,  "volatilite": "immuable",  "objet_entite": False, "type_sujet": "oeuvre",       "type_objet": "date",         "desc": "date de sortie d'une œuvre (induit-culture)"},
    "a_interprete":      {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "personne",     "type_objet": "oeuvre",       "desc": "interprète / incarne un rôle, une œuvre (induit-culture)"},
    # économie
    "a_acquis":          {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": True,  "type_sujet": "organisation", "type_objet": "organisation", "desc": "acquiert / rachète une organisation (induit-éco ; a_achete côté entreprise)"},
    "chiffre_affaires_de": {"fonctionnel": True, "volatilite": "changeant", "objet_entite": False, "type_sujet": "organisation", "type_objet": "valeur",      "desc": "chiffre d'affaires d'une entreprise (induit-éco)"},
    "concurrent_de":     {"fonctionnel": False, "volatilite": "stable",    "objet_entite": True,  "type_sujet": "organisation", "type_objet": "organisation", "desc": "concurrent / rival d'une entreprise (induit-éco)"},
    "a_lance":           {"fonctionnel": False, "volatilite": "immuable",  "objet_entite": False, "type_sujet": "organisation", "type_objet": "oeuvre",       "desc": "lance / dévoile un produit (induit-éco)"},
    "partenaire_de":     {"fonctionnel": False, "volatilite": "changeant", "objet_entite": True,  "type_sujet": "organisation", "type_objet": "organisation", "desc": "partenaire / s'associe avec (induit-éco)"},
}

POIDS_IMPORTANCE = {
    # socle
    "nom_de": 1.0, "parent_de": 0.95, "enfant_de": 0.95, "frere_de": 0.9, "marie_a": 0.9,
    "pdg_de": 0.9, "maire_de": 0.9, "dirige": 0.9, "date_naissance_de": 0.6, "connait": 0.5,
    "ami_de": 0.5, "profession_de": 0.5, "siege_de": 0.5, "produit": 0.5, "appartient_a": 0.5,
    "possede": 0.5, "travaille_pour": 0.5, "population_de": 0.4, "date_fondation_de": 0.4,
    "ville_exercice_de": 0.4, "rue_de": 0.3, "effectif_de": 0.2, "prix_de": 0.1,
    "horaire_de": 0.1, "repas_de": 0.05, "qualifie_pour": 0.5,
    # induits
    "se_separe_de": 0.6, "a_rencontre": 0.4, "critique": 0.3,
    "a_fonde": 0.7, "a_dirige": 0.7, "enseigne_a": 0.5, "etudie_a": 0.4, "a_achete": 0.5,
    "a_investi_dans": 0.4, "a_demissionne_de": 0.5,
    "lieu_naissance_de": 0.6, "lieu_deces_de": 0.5, "s_installe_a": 0.4, "date_deces_de": 0.6,
    "a_cree": 0.6, "a_publie": 0.5, "a_ecrit_lettre": 0.3, "a_signe": 0.4, "a_recu_prix": 0.6,
    "a_decouvert": 0.7, "a_obtenu_diplome": 0.5, "a_nationalite": 0.6, "a_contribue_a": 0.5,
    "a_rejete": 0.3, "a_vendu": 0.3, "a_participe_a": 0.4, "s_oppose_a": 0.4, "soutient": 0.4,
    # généralistes
    "traverse": 0.3, "a_pour_capitale": 0.5, "a_pour_frontiere": 0.3, "superficie_de": 0.3,
    "altitude_de": 0.3, "longueur_de": 0.3, "langue_de": 0.4, "monnaie_de": 0.4, "situe_dans": 0.4,
    "a_battu": 0.3, "affronte": 0.2, "organise": 0.5, "detient_record": 0.5, "a_recrute": 0.4,
    "entraine": 0.5, "a_remporte": 0.6, "est_compose_de": 0.4, "propriete_de": 0.3,
    "a_adopte": 0.5, "a_adhere_a": 0.5, "se_retire_de": 0.5, "a_nomme": 0.5,
    "a_pour_date": 0.4, "se_deroule_a": 0.4, "expose_a": 0.3, "date_sortie_de": 0.4, "a_interprete": 0.3,
    "a_acquis": 0.5, "chiffre_affaires_de": 0.3, "concurrent_de": 0.3, "a_lance": 0.4, "partenaire_de": 0.3,
}

GABARITS = {
    # socle
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
    "qualifie_pour":     ("{s} est qualifié(e) pour {o}", "{s} était qualifié(e) pour {o}", "Les qualifications de {s}"),
    # induits
    "se_separe_de":      ("{s} se sépare de {o}", "{s} s'est séparé(e) de {o}", "Les séparations de {s}"),
    "a_rencontre":       ("{s} rencontre {o}", "{s} a rencontré {o}", "Les rencontres de {s}"),
    "critique":          ("{s} critique {o}", "{s} a critiqué {o}", "Les critiques de {s}"),
    "a_fonde":           ("{s} fonde {o}", "{s} a fondé {o}", "Ce que {s} a fondé"),
    "a_dirige":          ("{s} dirige {o}", "{s} dirigeait {o}", "Ce que dirige {s}"),
    "enseigne_a":        ("{s} enseigne à {o}", "{s} enseignait à {o}", "Où enseigne {s}"),
    "etudie_a":          ("{s} étudie à {o}", "{s} a étudié à {o}", "Où a étudié {s}"),
    "a_achete":          ("{s} rachète {o}", "{s} a racheté {o}", "Ce que {s} a racheté"),
    "a_investi_dans":    ("{s} investit dans {o}", "{s} a investi dans {o}", "Les investissements de {s}"),
    "a_demissionne_de":  ("{s} démissionne de {o}", "{s} a démissionné de {o}", "Les démissions de {s}"),
    "lieu_naissance_de": ("{s} est né(e) à {o}", "{s} est né(e) à {o}", "Le lieu de naissance de {s}"),
    "lieu_deces_de":     ("{s} est mort(e) à {o}", "{s} est mort(e) à {o}", "Le lieu de décès de {s}"),
    "s_installe_a":      ("{s} s'installe à {o}", "{s} s'était installé(e) à {o}", "Où s'installe {s}"),
    "date_deces_de":     ("{s} est mort(e) en {o}", "{s} est mort(e) en {o}", "La date de décès de {s}"),
    "a_cree":            ("{s} crée {o}", "{s} a créé {o}", "Ce que {s} a créé"),
    "a_publie":          ("{s} publie {o}", "{s} a publié {o}", "Ce que {s} a publié"),
    "a_ecrit_lettre":    ("{s} écrit une lettre à {o}", "{s} a écrit une lettre à {o}", "Les lettres de {s}"),
    "a_signe":           ("{s} signe {o}", "{s} a signé {o}", "Ce que {s} a signé"),
    "a_recu_prix":       ("{s} reçoit {o}", "{s} a reçu {o}", "Les distinctions de {s}"),
    "a_decouvert":       ("{s} découvre {o}", "{s} a découvert {o}", "Les découvertes de {s}"),
    "a_obtenu_diplome":  ("{s} obtient {o}", "{s} a obtenu {o}", "Les diplômes de {s}"),
    "a_nationalite":     ("{s} a la nationalité {o}", "{s} avait la nationalité {o}", "La nationalité de {s}"),
    "a_contribue_a":     ("{s} contribue à {o}", "{s} a contribué à {o}", "Les contributions de {s}"),
    "a_rejete":          ("{s} rejette {o}", "{s} a rejeté {o}", "Ce que {s} a rejeté"),
    "a_vendu":           ("{s} vend {o}", "{s} a vendu {o}", "Ce que {s} a vendu"),
    "a_participe_a":     ("{s} participe à {o}", "{s} a participé à {o}", "La participation de {s}"),
    "s_oppose_a":        ("{s} s'oppose à {o}", "{s} s'est opposé(e) à {o}", "Les oppositions de {s}"),
    "soutient":          ("{s} soutient {o}", "{s} a soutenu {o}", "Ce que soutient {s}"),
    # généralistes
    "traverse":          ("{s} traverse {o}", "{s} traversait {o}", "Ce que traverse {s}"),
    "a_pour_capitale":   ("la capitale de {s} est {o}", "la capitale de {s} était {o}", "La capitale de {s}"),
    "a_pour_frontiere":  ("{s} a une frontière avec {o}", "{s} avait une frontière avec {o}", "Les frontières de {s}"),
    "superficie_de":     ("la superficie de {s} est {o}", "la superficie de {s} était {o}", "La superficie de {s}"),
    "altitude_de":       ("{s} culmine à {o}", "{s} culminait à {o}", "L'altitude de {s}"),
    "longueur_de":       ("{s} mesure {o}", "{s} mesurait {o}", "La longueur de {s}"),
    "langue_de":         ("{s} a pour langue {o}", "{s} avait pour langue {o}", "La langue de {s}"),
    "monnaie_de":        ("{s} a pour monnaie {o}", "{s} avait pour monnaie {o}", "La monnaie de {s}"),
    "situe_dans":        ("{s} se situe dans {o}", "{s} se situait dans {o}", "Où se situe {s}"),
    "a_battu":           ("{s} a battu {o}", "{s} avait battu {o}", "Qui {s} a battu"),
    "affronte":          ("{s} affronte {o}", "{s} affrontait {o}", "Qui affronte {s}"),
    "organise":          ("{s} organise {o}", "{s} a organisé {o}", "Ce qu'organise {s}"),
    "detient_record":    ("{s} détient {o}", "{s} détenait {o}", "Les records de {s}"),
    "a_recrute":         ("{s} recrute {o}", "{s} a recruté {o}", "Qui {s} a recruté"),
    "entraine":          ("{s} entraîne {o}", "{s} entraînait {o}", "Ce qu'entraîne {s}"),
    "a_remporte":        ("{s} remporte {o}", "{s} a remporté {o}", "Ce que {s} a remporté"),
    "est_compose_de":    ("{s} est composé de {o}", "{s} était composé de {o}", "La composition de {s}"),
    "propriete_de":      ("{s} a pour propriété {o}", "{s} avait pour propriété {o}", "Les propriétés de {s}"),
    "a_adopte":          ("{s} adopte {o}", "{s} a adopté {o}", "Ce que {s} a adopté"),
    "a_adhere_a":        ("{s} adhère à {o}", "{s} a adhéré à {o}", "Les adhésions de {s}"),
    "se_retire_de":      ("{s} se retire de {o}", "{s} s'est retiré de {o}", "Les retraits de {s}"),
    "a_nomme":           ("{s} nomme {o}", "{s} a nommé {o}", "Qui {s} a nommé"),
    "a_pour_date":       ("{s} a lieu en {o}", "{s} a eu lieu en {o}", "La date de {s}"),
    "se_deroule_a":      ("{s} se déroule à {o}", "{s} s'est déroulé à {o}", "Où se déroule {s}"),
    "expose_a":          ("{s} est exposé à {o}", "{s} était exposé à {o}", "Où est exposé {s}"),
    "date_sortie_de":    ("{s} sort en {o}", "{s} est sorti en {o}", "La date de sortie de {s}"),
    "a_interprete":      ("{s} interprète {o}", "{s} a interprété {o}", "Ce qu'interprète {s}"),
    "a_acquis":          ("{s} acquiert {o}", "{s} a acquis {o}", "Ce que {s} a acquis"),
    "chiffre_affaires_de": ("le chiffre d'affaires de {s} est {o}", "le chiffre d'affaires de {s} était {o}", "Le chiffre d'affaires de {s}"),
    "concurrent_de":     ("{s} est concurrent de {o}", "{s} était concurrent de {o}", "Les concurrents de {s}"),
    "a_lance":           ("{s} lance {o}", "{s} a lancé {o}", "Ce que {s} a lancé"),
    "partenaire_de":     ("{s} est partenaire de {o}", "{s} était partenaire de {o}", "Les partenaires de {s}"),
}

_ORDRE_TYPES = ["personne", "organisation", "lieu", "date", "oeuvre", "distinction",
                "valeur", "evenement", "groupe", "entite"]


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
    """MENU PAR TYPE D'OBJET (façon ODKE+) : les prédicats regroupés par le type de l'entité-objet,
    pour que le lecteur choisisse dans le bon rayon selon ce que désigne l'objet."""
    par_type = {}
    for p, info in PREDICATS.items():
        par_type.setdefault(info.get("type_objet", "valeur"), []).append((p, info))
    cles = [t for t in _ORDRE_TYPES if t in par_type] + [t for t in par_type if t not in _ORDRE_TYPES]
    lignes = []
    for t in cles:
        lignes.append(f"  • objet = {t} :")
        for p, info in sorted(par_type[t]):
            arite = "ENTITÉ" if info["objet_entite"] else "valeur"
            lignes.append(f"      - {p} ({info['type_sujet']}→{t}, objet={arite}) : {info['desc']}")
    return "\n".join(lignes)
