# -*- coding: utf-8 -*-
"""
memoire/config.py — TOUS les interrupteurs et paramètres de la bibliothèque, défauts SÛRS.

Défaut global à l'installation : V2 nu + reconnaissance/rappel + typologie en lecture.
Importance et dormance-modulée restent OFF (l'hôte les active selon son usage).
Défaut sûr = ne jamais perdre un fait, ne jamais introduire de bruit non sollicité.
"""

# ── CŒUR (non optionnel) — deux axes Force / Certitude, provenance, statuts ──
TOP_K = 5
V2_FORCE_INIT = 0.5
V2_FORCE_GAIN_ACCES = 0.05
V2_FORCE_PLAFOND = 0.99
V2_FORCE_DEMIVIE = 240.0
V2_FORCE_SEUIL_DORMANT = 0.15
V2_CERT_INIT_1SOURCE = 0.55
V2_CERT_GAIN_CORRO = 0.20
V2_CERT_PLAFOND = 0.95
V2_CERT_PLAFOND_MENTEUR = 0.60          # règle du menteur : 1 source → plafond 0.60
V2_CERT_MALUS_DISPUTE = 0.10
V2_CERT_PLANCHER_CORROBORE = 0.55       # fix menteur : ≥2 sources ne descend pas sous ce plancher
V2_RESOL_SEUIL = 0.85
V2_RESOL_AMBIGU_BAS = 0.75
V2_DORMANCE_SOURCES_PROTEGE = 3         # ≥3 sources → jamais de dormance (garde-fou indépendant)
V2_NOYAU_SOURCES = 3
V2_NOYAU_ACCES = 5
V2_NOYAU_FACTEUR = 2.0
V2_FUSION_SEUIL = 0.95
V2_TOP_K_LECTURE = 8
V2_BONUS_ENTITE = 0.30

# ── OPTIONS (interrupteurs, défauts prudents) ────────────────────────────
OPT_RECONNAISSANCE = True       # entrée par nœud nommé (lit les dormants). Le vrai fix des faits muets.
OPT_TYPOLOGIE = True            # typologie durable/éphémère en LECTURE de structure (informe la dormance)
OPT_IMPORTANCE = False          # calcule l'importance (PageRank). OFF par défaut (l'hôte l'active).
OPT_IMPORTANCE_RETRIEVAL = False  # importance dans le score de retrieval. OFF : le run V3 y a vu du bruit.
OPT_DORMANCE_MODULEE = False    # dormance abaissée pour les faits importants. OFF (vindiquée en rappel libre).

# ── Importance (option) — PageRank pondéré + croisement entité × relation ──
IMP_DAMPING = 0.85
IMP_ALPHA = 0.7
IMP_BETA = 0.9                  # modulation dormance ; n'agit que si importance > 0 (donc option ON)
IMP_SEED_DEGRE = 0.3
IMP_SEED_SOURCES = 0.4
IMP_SEED_CATEGORIE = 0.3
IMP_BONUS_CATEGORIE = {"personne": 1.0, "organisation": 0.8, "lieu": 0.5,
                       "objet": 0.2, "valeur": 0.0, None: 0.3}
IMP_W_SIM = 1.0
IMP_W_FORCE = 0.5
IMP_W_IMPORTANCE = 0.6
IMP_W_ENTITE = 0.3

# ── Typologie des liens (option) — durable / éphémère par la structure ───
TYPO_ASYMETRIQUES_DURABLES = {"dirige", "appartient_a", "possede", "travaille_pour", "pdg_de",
                              "maire_de", "siege_de", "profession_de"}
