# -*- coding: utf-8 -*-
"""
connecteur/test_reel/verite_terrain.py — LE BANC GELÉ (vérité réelle, vérifiée à la main au 14/06/2026).

Sources publiques : Euronext / Café de la Bourse (CAC 40), Wikipédia / FIFA (Coupe du monde 2026).
RIEN ici n'est produit par un LLM. C'est la référence absolue de notation.

Mapping ontologie (synthétique) → faits réels, choix assumés :
  • appartenance à un indice / liste de qualifiés → predicat `appartient_a` (objet = entité-groupe)
  • cours d'un indice (dérive continue, volatil)   → predicat `prix_de`  (volatilité « volatil »)
Les membres SORTIS sont écrits puis CLOS à leur date de sortie → rendu « était… jusqu'à [date] ».
"""

DATE_TEST = "2026-06"   # « aujourd'hui » du test = 14 juin 2026

# ── 1.1 CAC 40 : membres ACTUELS (entrés, courants) et SORTIS (clos à leur date) ──────────
# (sujet, predicat, objet, source, valide_de, clore_a)   clore_a=None → reste courant
CAC = [
    # — entrés, restent DANS le CAC 40 au 14/06/2026 —
    ("Accor",         "appartient_a", "CAC 40", "Euronext", "2024-03", None),
    ("Bureau Veritas","appartient_a", "CAC 40", "Euronext", "2024-12", None),
    ("Euronext SA",   "appartient_a", "CAC 40", "Euronext", "2025-09", None),
    ("Eiffage",       "appartient_a", "CAC 40", "Euronext", "2025-12", None),
    # — sortis, NE SONT PLUS dans le CAC 40 (clôture datée = « était… jusqu'à ») —
    ("Alstom",          "appartient_a", "CAC 40", "Euronext", "2018-01", "2024-03"),
    ("Vivendi",         "appartient_a", "CAC 40", "Euronext", "2018-01", "2024-12"),
    ("Teleperformance", "appartient_a", "CAC 40", "Euronext", "2020-01", "2025-09"),
    ("Edenred",         "appartient_a", "CAC 40", "Euronext", "2020-01", "2025-12"),
]

# ── 1.2 Le COURS (piège : volatil, pas de date de validité, dérive en continu) ────────────
COURS = [
    ("CAC 40", "prix_de", "8020", "Euronext", "2025-11", None),   # ~8020 le 24/11/2025 UNIQUEMENT
]

# ── 1.3 Coupe du monde 2026 : qualifiés (courants) ────────────────────────────────────────
CDM = [
    (e, "appartient_a", "Coupe du monde 2026", src, date, None) for (e, src, date) in [
        ("Canada", "FIFA", "2022-06"), ("Etats-Unis", "FIFA", "2022-06"),
        ("Mexique", "FIFA", "2022-06"),                                   # hôtes d'office
        ("Japon", "FIFA", "2025-03"),                                     # 1er qualifié (Asie)
        ("Nouvelle-Zelande", "FIFA", "2025-03"),                          # Océanie
        ("Autriche", "FIFA", "2025-11"), ("Belgique", "FIFA", "2025-11"),
        ("Ecosse", "FIFA", "2025-11"), ("Espagne", "FIFA", "2025-11"),
        ("Suisse", "FIFA", "2025-11"), ("France", "FIFA", "2025-11"),
        ("Allemagne", "FIFA", "2025-11"), ("Croatie", "FIFA", "2025-11"),
        ("Angleterre", "FIFA", "2025-11"), ("Portugal", "FIFA", "2025-11"),
    ]
]

# ── 1.4 FAITS-MENTEURS (faux, source unique « BlogX », injectés APRÈS coup à l'étage 3) ────
#   chacun contredit une vérité ci-dessus ; la mémoire doit RÉSISTER (ne pas détrôner le vrai)
MENTEURS = [
    ("Teleperformance", "appartient_a", "CAC 40", "BlogX", "2026-01"),    # vs sortie datée 2025-09
    ("Alstom",          "appartient_a", "CAC 40", "BlogX", "2026-01"),    # vs sortie datée 2024-03
    ("Italie",          "appartient_a", "Coupe du monde 2026", "BlogX", "2026-01"),  # faux : non qualifiée
]

FAITS = CAC + COURS + CDM   # tout ce qui s'injecte à l'ingestion initiale (chronologique)

# ── 2. QUESTIONS GELÉES (réponse-vérité mécanique + statut attendu) ───────────────────────
#   statut_attendu : "absent" (plus membre/clos) | "present" (courant) | "reserve" (volatil périmé)
#                    | "historique" (imparfait daté correct) | "incertain" (menteur mono-source)
#   cles_correct / cles_faux : mots qui, dans la réponse, signent le bon / le mauvais verdict
QUESTIONS = [
    # — Étage 1 : bascules datées —
    dict(id=1, etage=1, q="Teleperformance fait-elle partie du CAC 40 aujourd'hui ?",
         attendu="NON — sortie le 22/09/2025", statut="absent",
         cles_correct=["non", "plus", "sortie", "était", "quitté", "retiré", "ne fait plus"],
         cles_faux=["oui, teleperformance fait", "fait partie", "en fait partie", "est membre"]),
    dict(id=2, etage=1, q="Edenred est-elle dans le CAC 40 actuellement ?",
         attendu="NON — sortie le 22/12/2025", statut="absent",
         cles_correct=["non", "plus", "sortie", "était", "quitté", "retiré"],
         cles_faux=["oui", "fait partie", "est membre", "en fait partie"]),
    dict(id=3, etage=1, q="Accor est-elle dans le CAC 40 ?",
         attendu="OUI — depuis le 15/03/2024", statut="present",
         cles_correct=["oui", "fait partie", "est membre", "depuis", "intégré", "en fait partie"],
         cles_faux=["non", "ne fait plus", "sortie"]),
    dict(id=4, etage=1, q="Quelles sociétés sont entrées au CAC 40 en 2025 ?",
         attendu="Euronext (22/09) et Eiffage (22/12)", statut="present",
         cles_correct=["euronext", "eiffage"],
         cles_faux=[]),
    dict(id=5, etage=1, q="Le Japon est-il qualifié pour la Coupe du monde 2026 ?",
         attendu="OUI", statut="present",
         cles_correct=["oui", "qualifi", "fait partie", "participe"],
         cles_faux=["non", "pas qualifi", "n'est pas"]),
    dict(id=6, etage=1, q="La Nouvelle-Zelande est-elle qualifiée pour la Coupe du monde 2026 ?",
         attendu="OUI", statut="present",
         cles_correct=["oui", "qualifi", "fait partie", "participe"],
         cles_faux=["non", "pas qualifi", "n'est pas"]),
    dict(id=7, etage=1, q="Alstom est-elle dans le CAC 40 aujourd'hui ?",
         attendu="NON — sortie le 15/03/2024", statut="absent",
         cles_correct=["non", "plus", "sortie", "était", "quitté", "retiré"],
         cles_faux=["oui", "fait partie", "est membre", "en fait partie"]),
    # — Étage 2 : le piège du cours continu —
    dict(id=8, etage=2, q="Combien vaut l'indice CAC 40 aujourd'hui ?",
         attendu="INCONNU à jour — ne PAS affirmer 8020 au présent ; réserve / daté + à revérifier",
         statut="reserve",
         cles_correct=["revérifier", "reverifier", "ne sais pas", "ne dispose", "pas de valeur",
                       "novembre", "2025", "valait", "à jour", "incertain", "actualis"],
         cles_faux=["vaut 8020", "vaut environ 8020", "est de 8020", "cote 8020", "8 020 points aujourd"]),
    dict(id=9, etage=2, q="Combien valait le CAC 40 fin novembre 2025 ?",
         attendu="~8020 (imparfait daté CORRECT ici)", statut="historique",
         cles_correct=["8020", "8 020", "novembre", "valait"],
         cles_faux=[]),
    # — Étage 3 : le menteur (provenance) — posées APRÈS injection des menteurs —
    dict(id=10, etage=3, q="Teleperformance est-elle dans le CAC 40 ?",
         attendu="NON (sortie 2025-09) ; le faux 'revenue 2026' ne détrône pas la sortie datée",
         statut="absent",
         cles_correct=["non", "plus", "sortie", "était", "2025", "quitté"],
         cles_faux=["oui, elle fait partie", "est de nouveau membre", "revenue", "réintégré"]),
    dict(id=11, etage=3, q="Alstom fait-elle partie du CAC 40 ?",
         attendu="NON (sortie 2024-03) ; le faux 'toujours au CAC' ne tient pas",
         statut="absent",
         cles_correct=["non", "plus", "sortie", "était", "2024", "quitté"],
         cles_faux=["oui, alstom fait", "toujours", "fait partie", "est membre"]),
    dict(id=12, etage=3, q="L'Italie est-elle qualifiée pour la Coupe du monde 2026 ?",
         attendu="Source unique non corroborée → incertain / à revérifier, JAMAIS affirmé comme sûr",
         statut="incertain",
         cles_correct=["revérifier", "reverifier", "incertain", "non confirm", "une seule source",
                       "pas sûr", "conditionnel", "il s'agirait", "non", "pas qualifi"],
         cles_faux=["oui, l'italie est qualifiée", "l'italie est qualifiée pour", "certainement qualifiée"]),
]
