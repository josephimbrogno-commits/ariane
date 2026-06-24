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

# ── DORMANCE GRADUELLE en LECTURE : un dormant n'est plus MUET, il arrive en rang BAISSÉ ───
# Malus de rang appliqué aux dormants dans l'entrée vectorielle, ATTÉNUÉ par la corroboration
# (n_sources) mais JAMAIS annulé (plancher). On adoucit la pente, on ne supprime pas l'oubli.
#   malus = max(MIN, BASE / (1 + BETA·(n_sources−1)))    # 1 src→BASE · 2 src→BASE/(1+BETA) · plancher MIN
DORMANCE_RANG_MALUS_BASE = 0.30   # malus d'un dormant MONO-source (fragile) : reste tout en bas
DORMANCE_RANG_CORRO_BETA = 3.00   # pente RAIDE : 2 sources atténuent fortement (0.075), pas 1 (0.30)
DORMANCE_RANG_MALUS_MIN  = 0.05   # plancher : un dormant corroboré reste pénalisé (la dormance garde son rôle)

# ── RÉUNION DES FRAGMENTS (MSFT/Microsoft) : structure pondérée par rareté, GATE même famille ──
# Score d'un couple = Σ 1/df(voisin commun)  (un voisin partagé par df entités pèse 1/df : Genève banal
# pèse peu, un PDG précis pèse fort) + petit bonus embedding (ne déclenche JAMAIS seul). Réunir si ≥ seuil.
# ── ACRONYMES COURTS : l'embedding d'un libellé court est PEU FIABLE → malus gradué par la BRIÈVETÉ ──
# Appliqué à la fusion par embedding de resoudre : sim_effective = sim − malus(L_court). Franc à 2-3
# lettres (UE/ONU 0.902 → sous 0.85, séparés), quasi nul pour les longs (Microsoft Corporation intact).
# malus(L) = MAX · (LREF / max(L,LREF))²   (raide à L=2, s'efface vite). Réglé sur le mini-banc.
ACRONYME_MALUS_MAX = 0.12     # malus à L=2 lettres : casse UE/ONU (0.902−0.12=0.78) sans toucher États-Unis/USA (L=3)
ACRONYME_L_REF = 2

REUNION_SEUIL = 0.30          # réglé sur le banc : voisin rare (df=2 → 0.5) passe ; banal (Genève df=5 → 0.2) non
# ── BARRE DE CONFIRMATION MODULÉE PAR LE TYPE : l'identité forte exige PLUS de preuve structurelle ──
# Une PERSONNE a une identité unique : deux personnes partageant UN voisin = coïncidence (elles
# connaissent la même personne), pas un doublon → barre HAUTE (plusieurs voisins RARES requis). Une
# ORGANISATION/objet/lieu a une identité RELATIONNELLE (Microsoft = ce qu'elle produit/dirige/où elle
# siège) → la structure partagée EST un signal d'identité → barre INCHANGÉE. Réglé sur les DEUX bancs :
# tue Pierre/Hélène & Camille/Tessier (1 voisin) sans toucher Microsoft/MSFT, ONU, SNCF (org, 1 voisin).
REUNION_FAMILLES_IDENTITE_FORTE = ("personne",)  # familles à barre haute (identité NON relationnelle)
REUNION_RARE_MIN = 0.25       # un voisin commun est « rare » si 1/df ≥ 0.25 (partagé par ≤ 4 entités)
REUNION_PERSONNE_MIN_VOISINS = 2  # personne : ≥2 voisins RARES partagés (un seul = coïncidence → jamais fusion)
REUNION_SEUIL_PERSONNE_FORT = 0.75  # OU un score structurel TRÈS haut (porte non binaire : un vrai doublon fort passe)
REUNION_EMBED_BONUS = 0.0     # appoint embedding MESURÉ NUISIBLE sur le banc (il fait basculer les paires
#                               partageant un hub banal : Paris/Marseille via France, OMS/OMM via Genève) → 0.
#                               La structure pondérée par la rareté sépare déjà parfaitement (0.5 vs 0.2). Le
#                               quasi-identique (≥0.85) reste géré au write-time par resoudre. Précision d'abord.

# ── OPTIONS (interrupteurs, défauts prudents) ────────────────────────────
OPT_RECONNAISSANCE = True       # entrée par nœud nommé (lit les dormants). Le vrai fix des faits muets.
OPT_TYPOLOGIE = True            # typologie durable/éphémère en LECTURE de structure (informe la dormance)
OPT_IMPORTANCE = False          # calcule l'importance (PageRank). OFF par défaut (l'hôte l'active).
OPT_IMPORTANCE_RETRIEVAL = False  # importance dans le score de retrieval. OFF : le run V3 y a vu du bruit.
OPT_DORMANCE_MODULEE = False    # dormance abaissée pour les faits importants. OFF (vindiquée en rappel libre).
OPT_DORMANCE_RANG_GRADUEL = True  # dormant = rang baissé (pas muet), malus modulé par corroboration. ON (fix stress-test).
OPT_REUNION_FRAGMENTS = True      # réunir les fragments (MSFT/Microsoft) par structure+famille en consolidation. ON.

# ── FENÊTRE DE CORÉFÉRENCE (brique 2) : résoudre un PRONOM à son antécédent NOMMÉ proche, AVANT d'écrire ──
# Compose avec l'anti-pronom (brique 1) : si l'extraction d'une phrase donne un sujet/objet PRONOM, on
# élargit le contexte aux phrases précédentes et on tente de rattacher le pronom à une entité NOMMÉE.
# Résolu sans ambiguïté → on écrit au nom résolu (le vrai levier des faits-clés) ; non résolu / AMBIGU →
# la brique 1 reprend : abstention. Jamais de devinette (une fausse résolution = collision déguisée).
# LOCAL seulement : l'antécédent doit être PRÉSENT dans le contexte proche. Le distant (« le commandant »
# résolu par ce que la mémoire sait) = brique 3 (appel mémoire), HORS périmètre ici.
OPT_FENETRE_COREF = True          # tenter la résolution de coréférence locale avant d'abstenir. ON.
FENETRE_COREF_MAX_PHRASES = 3     # limite DURE d'élargissement en arrière (au-delà : abstention, pas tout le paragraphe)

# ── APPEL MÉMOIRE (brique 3) : résoudre une référence DISTANTE à une entité CONNUE, AVANT d'écrire ──
# Quand une référence n'est pas résoluble localement (« M. Vasseur », « le commandant », « papa » sans
# Pierre proche), on INTERROGE la toile pour la rattacher à une entité déjà connue. RÈGLE D'OR : la
# mémoire répond QUI (identité de la référence), JAMAIS QUOI (le contenu, qui vient du texte). Match
# UNIQUE et confiant seulement ; sinon nœud distinct / abstention. Le texte prime sur la toile pour le
# contenu (droit de douter de la mémoire). Conservateur d'abord : mieux vaut une référence non résolue
# (fragment) qu'une référence mal résolue (collision + risque de BOUCLE auto-confirmante).
OPT_APPEL_MEMOIRE = True          # rattacher une référence distante à une entité connue (qui, pas quoi). ON.
APPEL_MEMOIRE_MAX_CANDIDATS = 12  # nb max d'entités présentées au résolveur LLM (borne le coût + le prompt)

# ── RECONNAISSANCE SOUPLE (chantier LECTURE) : retrouver le nœud malgré des tokens EN PLUS ────────
# Diagnostic long run : 36 % des abstentions = le fait EST stocké mais l'entité n'est pas reconnue, car
# le nom stocké a des tokens que la question (titre) n'a pas (« Pierre HENRI Canivet », « … VICOMTE de
# Biolley », « Kimura (木村) »). Le match strict (tokens entité ⊆ question) échoue. Souple : on reconnaît
# si les tokens PREMIER et DERNIER (latin, ≥3 car) de l'entité sont dans la question — on tolère les
# tokens du milieu (prénoms composés, titres, scripts non-latins) MAIS on exige les deux bouts → rejette
# les homonymes (« Alfonso … de Mendoza » n'accroche pas « JUAN … y Mendoza » : 1er token « juan » absent).
# Recall-sûr et conflit-sûr (n'injecte que des faits ; le disputé reste rendu disputé). OFF = strict historique.
OPT_RECONNAISSANCE_SOUPLE = True   # ON : +6 pts rappel (34→40 %) recall-sûr & 0-CW conflit tenu (mesuré). Local, non committé.

# ── EXTRACTION COMPLÈTE (chantier EXTRACTION) : ne pas lâcher de fait sur phrase dense ────────────
# Diagnostic long run : 53 % des faits « manquants » = l'entité a déjà plusieurs faits mais UNE relation
# de la phrase dense a été sautée (« né le X à Y » → garde la date, lâche le LIEU). Le multi-triplets
# n'est pas exhaustif. ON : clause de COMPLÉTUDE biographique au prompt multi (revue systématique des
# slots naissance/lieu/profession/nationalité/décès + exemple). N'ajoute QUE des faits fidèles (recall),
# chaque fait passe par les mêmes planchers 0-FP polarité. Multi seulement (single/barometre inchangés).
# OFF = prompt multi historique → iso-résultat.
OPT_EXTRACTION_COMPLETE = True    # ON : +5 pts recall extraction (50→55 %) recall-sûr, FP polarité tenu. Local, non committé.

# ── REROUTAGE DATE ÉVÉNEMENTIEL (chantier EXTRACTION org/œuvre) : la date au BON prédicat ─────────
# Diagnostic : le trou noir org/œuvre = la DATE routée au MAUVAIS prédicat. « CCM créé en 1944 » →
# a_fonde(CCM→1944), « roman publié en 2005 » → a_publie(roman→2005). Or a_fonde/a_publie/a_cree/a_lance
# attendent une PERSONNE/ENTITÉ en objet, JAMAIS une année → un objet ANNÉE y est TOUJOURS faux. On
# reroute alors vers date_fondation_de / date_sortie_de. Recall ET précision sûrs (le fait mal routé est
# soit perdu soit faux). Ne touche que ces prédicats-agents quand l'objet est une pure date. OFF = historique.
OPT_REROUTE_DATE = True            # ON : date au bon prédicat (date_fondation 0→3/15), précision-sûr. Local→commit.

# ── SUBCONSCIENT #1 : VOLATILITÉ APPRISE (premier motif distillé au-dessus des faits) ─────────────
# Ariane apprend la volatilité d'un prédicat de ses CLÔTURES DATÉES observées (clos / occurrences ;
# JAMAIS les disputés = signal pur) → alimente la demi-vie de certitude EN REMPLACEMENT PROGRESSIF du
# prior à la main. Mélange pondéré par l'ÉVIDENCE : peu d'obs → on reste sur le prior (« supposition ») ;
# beaucoup d'obs cohérentes → on glisse vers l'observé (« appris »). Le prior n'est jamais jeté (point de
# départ corrigé). AUCUN fait modifié — seulement un PARAMÈTRE dérivé (la demi-vie). Calculé à la
# consolidation, inspectable (g.dump_volatilite()). OFF = demi-vie = étiquette main exacte (iso-résultat).
# ⚠️ Ne doit JAMAIS dégrader la péremption (statut courant/clos fixé à l'écriture, indépendant de la demi-vie).
# ⚠️ POURQUOI DÉFAUT OFF (pas seulement « une option ») : la mesure clos/occ CONFOND « longue histoire » et
# « haute volatilité » — elle n'est PAS normalisée par le TEMPS. Sur des historiques profonds (24 coachs d'un
# club → 85 % de clôtures) elle sur-estime la volatilité (demi-vie apprise 41j alors que le prior 180j est plus
# juste : un coach dure ~2 ans). Le mécanisme est SAIN et SÛR (péremption strictement préservée, ON==OFF),
# mais NE PAS L'ACTIVER tant que la volatilité observée n'est pas mesurée en CHANGEMENTS PAR UNITÉ DE TEMPS.
OPT_SUBCONSCIENT_VOLATILITE = False
SUBCON_K_CONF = 30.0              # lissage de confiance : w = n_occ / (n_occ + K) (30 obs → confiance 0.5)
SUBCON_MIN_OCC = 12              # sous ce nb d'occurrences → reste sur le prior (« supposition »), pas de bascule
SUBCON_MIN_CLOS = 3              # et au moins ce nb de clôtures pour oser un signal de volatilité
SUBCON_DV_REF = 730.0           # demi-vie de référence (jours) pour taux=0 ; calibrée sur les labels main
SUBCON_DV_DEMI_TAUX = 0.10      # taux qui HALVE la demi-vie (taux 0.20 → ~180j = « changeant », concorde)
SUBCON_DV_PLANCHER = 20.0       # demi-vie minimale apprise (jours)
SUBCON_DV_IMMUABLE = 1.0e6      # représentation finie de « immuable » (None) pour le mélange

# ── EXTRACTION MULTI-TRIPLETS (chantier AJOUTER) : N faits par phrase au lieu d'UN ────────────
# Une phrase dense (« né en 1973 à Toulouse, joueur de rugby ») porte plusieurs faits ; en extraire
# UN seul plafonne le rappel (mesuré : banc caché Wikidata 20 %). On extrait TOUS les faits distincts,
# chacun passant par la MÊME finalisation (planchers 0-FP, anti-pronom, coréférence) que le single.
OPT_MULTI_TRIPLETS = True         # ecrire() extrait plusieurs faits par phrase. OFF = comportement single historique.

# ── VITESSE (chantier C+B) : accélérer l'ingestion SANS rien changer aux sorties (iso-résultat) ──
# Le multi-triplets refait la brique 3 (appel mémoire) PAR triplet : une phrase à N faits qui partagent
# le même sujet (« le commandant ») résout N fois la MÊME référence. C = la résoudre UNE fois par phrase
# (mutualiser, mêmes calculs, moins d'appels). B = exécuter les résolutions distantes INDÉPENDANTES en
# parallèle (gain de temps mur). Les ÉCRITURES restent séquencées dans l'ordre (déterminisme préservé).
# Iso-résultat à prouver par record/replay : OFF = comportement historique exact (rollback immédiat).
OPT_GROUPER_MEMOIRE = False       # C : résoudre chaque réf distante UNE fois par phrase (au lieu d'1×/triplet)
OPT_PARALLELE_PHRASE = False      # B : paralléliser les résolutions distantes distinctes d'une phrase
PARALLELE_MAX_WORKERS = 6         # plafond de threads pour B (Ollama sert les requêtes concurrentes)

# ── DROIT À L'ABSTENTION DE PRÉDICAT : garder le VERBE BRUT plutôt que forcer une case absurde ──
# Diagnostic mis-picks : forcer la phrase dans l'une des 107 cases produit des absurdités de cause (c)
# (a_pour_capitale(mosquée), se_retire_de pour une exfiltration…). Sonde : garder le verbe brut du texte
# (hors-ontologie) quand AUCUNE case ne colle réduit ces absurdités SANS forcer. Un fait à verbe brut est
# faible par nature (objet littéral, non-fonctionnel, mono-source) → le tri AVAL de la mémoire l'encaisse.
# OFF = comportement historique EXACT (prompt et sorties inchangés ; un prédicat hors-liste → abstention totale).
OPT_ABSTENTION_PREDICAT = True    # autoriser un prédicat = verbe brut (~verbe) en DERNIER recours. Validé banc caché.

# ── CANONICALISATION DES VERBES BRUTS (Temps A) : rabattre un verbe brut INFINITIF sur sa case ────
# Quand le greffier abstient vers un verbe brut (ex. « diriger ») alors qu'une case CANONIQUE existe
# (« dirige »), on rabat dessus AVANT de figer l'abstention (table SÛRE CANON_VERBES_BRUTS). Gain :
# recall (faits perdus à l'infinitif récupérés) + ASSURANCE CARDINALE — un modèle qui abstiendrait
# « diriger » ne casserait plus la péremption (un verbe brut ne clôt JAMAIS ; rabattu sur « dirige »
# fonctionnel, il clôt). Cf. crash MoE qwen3.6 (abstenait dirige→diriger → CW péremption 25-30 %).
# Carte 2026-06-24 : sur qwen3:30b-a3b l'abstention est rare → gain recall marginal, c'est surtout une
# assurance. Validé ON : recall iso (51 %→51 %), cardinal IDENTIQUE (péremption 98 %/0 % CW, conflit
# 12/12·0), déterministe 13/7/17 + test dédié 13/13. ON par défaut = antidote cardinal actif (rabattage
# d'un verbe brut sur sa case avant abstention). OFF = le verbe brut reste hors-ontologie (iso historique).
OPT_CANON_VERBES_BRUTS = True

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
