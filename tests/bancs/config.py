# -*- coding: utf-8 -*-
"""
config.py — TOUS les réglages du projet « La mémoire qui trie » sont ici.

Un non-développeur peut modifier ces valeurs sans toucher au reste du code.
Chaque paramètre est commenté. Les trois mécanismes du projet
(surprise, péremption, renforcement) se règlent principalement via :
  - GAIN_CONFIRMATION  (renforcement)
  - PERTE_CONTRADICTION (surprise)
  - DEMI_VIE_JOURS      (péremption / érosion)
"""

from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────
#  MODÈLES (servis localement par Ollama, déjà installé sur la machine)
# ─────────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"

# Modèle de langage qui RÉPOND aux questions (instruct 7–8B, comme demandé).
MODELE_LLM = "llama3.1:8b"

# Modèle qui JUGE (vérificateur). Config CHAMPIONNE retenue après l'étape 1 :
# qwen3:30b-a3b s'est montré bien plus fiable sur la récence (1 catastrophe/60 vs 9).
MODELE_JUGE = "qwen3:30b-a3b"
JUGE_THINK = False  # couper le raisonnement verbeux de qwen3 (sortie JSON directe)

# Modèle d'embeddings (multilingue léger). Téléchargé automatiquement au 1er usage.
MODELE_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"

# Délai max d'attente d'une réponse du modèle (secondes).
TIMEOUT_LLM = 180

# Températures : basse pour des réponses stables, 0 pour le juge (déterministe).
TEMPERATURE_REPONSE = 0.2
TEMPERATURE_JUGE = 0.0

# ─────────────────────────────────────────────────────────────────────────
#  RECHERCHE EN MÉMOIRE
# ─────────────────────────────────────────────────────────────────────────
TOP_K = 5  # nombre de souvenirs récupérés par question

# ─────────────────────────────────────────────────────────────────────────
#  DYNAMIQUE DE LA CONFIANCE  (le cœur des 3 mécanismes)
# ─────────────────────────────────────────────────────────────────────────
CONFIANCE_DEPART = 0.6     # confiance d'un souvenir neuf
PLAFOND_CONFIANCE = 0.99   # on ne dépasse jamais ça
GAIN_CONFIRMATION = 0.10   # +confiance quand un souvenir est CONFIRMÉ  (renforcement)
PERTE_CONTRADICTION = 0.25 # -confiance quand un souvenir est CONTREDIT (surprise)
MALUS_INCERTAIN = 0.0      # -confiance quand verdict INCERTAIN (0 = neutre par défaut)

# ─────────────────────────────────────────────────────────────────────────
#  ÉROSION TEMPORELLE  (péremption)
#  Décroissance exponentielle : confiance *= 0.5 ** (jours_écoulés / DEMI_VIE_JOURS)
#  Demi-vie = nombre de jours (simulés) au bout desquels la confiance est divisée
#  par 2 si le souvenir n'est ni consulté ni confirmé.
# ─────────────────────────────────────────────────────────────────────────
DEMI_VIE_JOURS = 30.0

# Rendu VERBAL de la confiance au répondeur (au lieu du nombre brut qui le rendait timide).
# En-dessous de ce seuil, le souvenir est marqué « à confirmer » ; au-dessus, rien de spécial.
SEUIL_VERBAL = 0.25

# ─────────────────────────────────────────────────────────────────────────
#  CONSOLIDATION (« sommeil ») — toutes les N interactions
# ─────────────────────────────────────────────────────────────────────────
N_CONSOLIDATION = 20       # fréquence du « sommeil »
SEUIL_FUSION = 0.95        # similarité au-dessus de laquelle 2 souvenirs sont des doublons
SEUIL_ARCHIVAGE = 0.15     # en-dessous de cette confiance, le souvenir est archivé (jamais supprimé)

# ─────────────────────────────────────────────────────────────────────────
#  HORLOGE VIRTUELLE — le temps de l'expérience est SIMULÉ
# ─────────────────────────────────────────────────────────────────────────
DATE_DEBUT = datetime(2026, 6, 1)  # début de la chronologie simulée (étape 1)

# ─────────────────────────────────────────────────────────────────────────
#  ÉTAPE 2 — MONDE SYNTHÉTIQUE & EXPÉRIENCE
# ─────────────────────────────────────────────────────────────────────────
SEED_MONDE = 42                       # graine aléatoire (reproductibilité)
MONDE_DEBUT = datetime(2026, 1, 1)    # début de la chronologie de 12 mois
MONDE_FIN = datetime(2026, 12, 15)    # date d'évaluation (fin de chronologie)
CONSULT_CIBLE_PAR_MOIS = 16           # intensité des balayages mensuels (config C) :
                                      # les faits populaires sont reconsultés presque chaque mois
                                      # (donc vivants à l'évaluation), les rares meurent (faux oublis)
N_QUESTIONS_EVAL = 60                 # nb de questions d'évaluation finale (≈ 50% stables / 50% changées)
N_QUESTIONS_EVAL_V2 = 40              # idem pour le grand run V2 (étape 4)

# ─────────────────────────────────────────────────────────────────────────
#  DOSSIERS
# ─────────────────────────────────────────────────────────────────────────
DOSSIER_LOGS = "logs"
DOSSIER_RESULTATS = "resultats"

# ─────────────────────────────────────────────────────────────────────────
#  V2 — mémoire à DEUX AXES (Force / Certitude), graphe daté, provenance
# ─────────────────────────────────────────────────────────────────────────
# FORCE = vivacité / retrouvabilité (nourrie par l'ACCÈS)
V2_FORCE_INIT = 0.5
V2_FORCE_GAIN_ACCES = 0.05
V2_FORCE_PLAFOND = 0.99
V2_FORCE_DEMIVIE = 240.0          # A2 (amendement V2.1) : recalibré 90 → 240 j
V2_FORCE_SEUIL_DORMANT = 0.15
# CERTITUDE = validité actuelle (nourrie SEULEMENT par corroboration indépendante)
V2_CERT_INIT_1SOURCE = 0.55
V2_CERT_GAIN_CORRO = 0.20
V2_CERT_PLAFOND = 0.95
V2_CERT_PLAFOND_MENTEUR = 0.60    # 1 seule source → Certitude plafonnée à 0.60
V2_CERT_MALUS_DISPUTE = 0.10
# Résolution d'entités
V2_RESOL_SEUIL = 0.85
V2_RESOL_AMBIGU_BAS = 0.75
# Sommeil : dormance bidimensionnelle, promotion « noyau »
V2_DORMANCE_SOURCES_PROTEGE = 3   # ≥ N sources indépendantes → JAMAIS de dormance (le monde l'ancre)
V2_NOYAU_SOURCES = 3              # promotion noyau : ≥ N sources indépendantes ET…
V2_NOYAU_ACCES = 5               # … ≥ N accès utiles
V2_NOYAU_FACTEUR = 2.0           # demi-vies (Force ET Certitude) doublées pour un noyau
V2_FUSION_SEUIL = 0.95           # similarité au-dessus de laquelle deux entités sont fusionnées
# Durcissement (étape 5)
V2_CERT_PLANCHER_CORROBORE = 0.55  # un fait ≥2 sources ne descend pas sous ce plancher de Certitude
                                   # (assez haut pour battre un mensonge à source unique qui décline,
                                   #  assez bas pour rester < 0.6 → « à revérifier » si jamais reconfirmé : cas Dupont)
V2_TOP_K_LECTURE = 8             # entrée vectorielle élargie (vs 5) pour le grand graphe
V2_BONUS_ENTITE = 0.30           # bonus de score si l'entité du fait est NOMMÉE dans la question

# ─────────────────────────────────────────────────────────────────────────
#  V3 — troisième axe : IMPORTANCE (protéger ce qui COMPTE, pas ce qui est récent)
#  Orthogonal à Force et Certitude. NE décroît PAS avec le temps ; dérivé de la STRUCTURE.
# ─────────────────────────────────────────────────────────────────────────
IMP_DAMPING = 0.85               # amortissement PageRank
IMP_ALPHA = 0.7                  # importance_fait = poids_relation × max(imp_sujet, imp_objet)^α
IMP_BETA = 0.9                   # modulation de la dormance : seuil = base × (1 − β·importance)
# Amorçage (seeds) du PageRank : 3 contributions par entité
IMP_SEED_DEGRE = 0.3             # degré brut (nb de faits rattachés)
IMP_SEED_SOURCES = 0.4           # nb de sources INDÉPENDANTES distinctes parlant de l'entité
IMP_SEED_CATEGORIE = 0.3         # bonus de type (mettre à 0 pour tester l'importance pure structure)
IMP_BONUS_CATEGORIE = {"personne": 1.0, "organisation": 0.8, "lieu": 0.5,
                       "objet": 0.2, "valeur": 0.0, None: 0.3}
# Pondérations du score de retrieval V3 (étape 3) : sim, Force, importance, correspondance entité
IMP_W_SIM = 1.0
IMP_W_FORCE = 0.5
IMP_W_IMPORTANCE = 0.6
IMP_W_ENTITE = 0.3
