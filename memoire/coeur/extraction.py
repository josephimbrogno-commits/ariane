# -*- coding: utf-8 -*-
"""
memoire/coeur/extraction.py — LECTEUR DIMENSIONNEL (V2).

V1 (déprécié) faisait tout en un coup : phrase → triplet (+ rustines). V2 résout SIX axes
INDÉPENDAMMENT puis DÉRIVE le fait, son statut et ses dates — comme la mémoire est passée du score
unique aux axes. Le LLM remplit une GRILLE structurée (conception de données, pas empilement de
consignes) ; des planchers DÉTERMINISTES restent sous la décision LLM comme garde-fous de sécurité.

Axes :
  1-4 structurels  : POLARITÉ · MODALITÉ · TEMPORALITÉ · RÔLE/DIRECTION
  5   vocabulaire  : COUVERTURE D'ONTOLOGIE (predicat ∈ liste blanche, sinon rejet)
  6   sémantique   : IDENTIFICATION/INFÉRENCE (borné : désambiguïser si possible, sinon rater proprement)

La DÉRIVATION (deriver) est déterministe : c'est elle qui rend le comportement prévisible.
Règle d'or : en cas de doute sur un axe, RIEN plutôt que le fait risqué.
"""

import re
import unicodedata

from .. import config
from .ontologie import PREDICATS, CANON_PREDICATS, CANON_VERBES_BRUTS, vocabulaire_pour_extraction


def _norm(texte):
    s = unicodedata.normalize("NFD", str(texte).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("’", "'").replace("`", "'")


# ── PROPRETÉ À LA SOURCE : un PRONOM/INDÉFINI ne devient JAMAIS un nœud (brique 1) ────────────
# Ressource FR GÉNÉRALE (linguistique, pas tirée d'un texte). Un libellé d'entité qui n'est QU'un
# pronom ou un indéfini ne désigne aucune entité résolue → on refuse de créer le nœud et, faute
# d'entité nommée pour porter le fait, on s'abstient. On NE RÉSOUT PAS le pronom ici (« il » → Pierre) :
# c'est l'affaire de la fenêtre (brique 2) et de l'appel mémoire (brique 3). Précision d'abord :
# mieux vaut un fait abstenu qu'un nœud-poubelle. La comparaison est EXACTE (libellé entier normalisé),
# jamais en sous-chaîne — « La Poste », « Personne Morale SA », « Cela Inc. » ne sont PAS touchés.
_PRONOMS_INDEFINIS = frozenset({
    # personnels (sujet + disjoints) et réfléchis emphatiques
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "moi", "toi", "lui", "soi", "eux",
    "moi-meme", "toi-meme", "lui-meme", "elle-meme", "soi-meme",
    "nous-memes", "vous-memes", "eux-memes", "elles-memes",
    # démonstratifs pronoms (PAS « ce/cette » déterminants, ni « ce + nom »)
    "celui", "celle", "ceux", "celles",
    "celui-ci", "celui-la", "celle-ci", "celle-la",
    "ceux-ci", "ceux-la", "celles-ci", "celles-la",
    "ceci", "cela", "ca",
    # relatifs/interrogatifs composés (les pronoms, pas « qui/que/quoi » nus, trop ambigus)
    "lequel", "laquelle", "lesquels", "lesquelles", "quiconque",
    # indéfinis
    "personne", "quelqu'un", "quelque chose", "rien", "nul", "nulle",
    "aucun", "aucune", "chacun", "chacune", "certains", "certaines",
    "plusieurs", "autrui", "untel", "d'aucuns",
    "l'un", "l'autre", "les uns", "les autres", "un autre", "une autre", "d'autres",
    "tout le monde", "n'importe qui", "n'importe quoi",
})


def _est_pronom(libelle):
    """True si le libellé, normalisé et débarrassé de la ponctuation de bord, EST exactement un
    pronom/indéfini (et donc ne désigne aucune entité résolue). Comparaison sur le mot ENTIER."""
    t = _norm(libelle).strip(" \t.,;:!?\"«»()[]…")
    return t in _PRONOMS_INDEFINIS


# ── FENÊTRE DE CORÉFÉRENCE (brique 2) : rattacher un pronom à un antécédent NOMMÉ PROCHE ──────
SYS_COREF = (
    "Tu fais de la RÉSOLUTION DE CORÉFÉRENCE, rien d'autre. On te donne un CONTEXTE (phrases "
    "précédentes) et une PHRASE cible contenant un PRONOM. Tu dois dire à quelle entité NOMMÉE "
    "(nom propre : personne, organisation, lieu…) ce pronom renvoie.\n"
    "RÈGLES STRICTES :\n"
    "- L'entité doit être PRÉSENTE telle quelle dans le contexte ou la phrase. N'invente JAMAIS un "
    "nom absent du texte.\n"
    "- Si DEUX entités nommées ou plus pourraient convenir → statut « ambigu » (on ne devine pas).\n"
    "- Si AUCUNE entité nommée ne convient (antécédent absent / trop loin) → statut « aucun ».\n"
    "- Dans le moindre doute : « ambigu » ou « aucun ». Mieux vaut ne pas résoudre que mal résoudre.\n"
    'Réponds UNIQUEMENT en JSON strict : {"entite":"<nom propre exact ou null>",'
    '"statut":"resolu|ambigu|aucun"}'
)


def _resoudre_coref(llm, pronom, role, phrase, contexte):
    """Tente de rattacher `pronom` (en position `role`) à une entité NOMMÉE du contexte proche.
    Renvoie le nom résolu, ou None si non résolu / ambigu / hallucination détectée (→ brique 1
    reprend : abstention). Précision d'abord : on n'accepte qu'un antécédent RÉELLEMENT présent."""
    d = llm.json(f"CONTEXTE :\n{contexte}\n\nPHRASE : « {phrase} »\n\n"
                 f"Le pronom « {pronom} » (position {role}) renvoie à quelle entité nommée ?",
                 systeme=SYS_COREF)
    if not isinstance(d, dict):
        return None
    if _norm(d.get("statut", "")).strip() != "resolu":
        return None                                   # ambigu / aucun → on n'attache pas
    ent = str(d.get("entite") or "").strip()
    if not ent or _est_pronom(ent):
        return None                                   # vide ou encore un pronom → échec
    # ANTI-HALLUCINATION : chaque jeton significatif du nom résolu doit apparaître dans le contexte
    # ou la phrase. Le LLM ne peut pas inventer un antécédent absent du texte (précision d'abord).
    foin = _norm(contexte + " " + phrase)
    toks = [t for t in re.findall(r"\w+", _norm(ent)) if len(t) >= 3]
    if not toks or not all(t in foin for t in toks):
        return None
    return ent


def _date(v):
    if not isinstance(v, str):
        return None
    v = v.strip()
    return None if v.lower() in ("", "null", "none") else v


# ── PLANCHER POLARITÉ : négation/fin EXPLICITE, mais qui DÉFÈRE au LLM sur les litotes ───────
_GARDES_LITOTE = [          # tournures où une négation AFFIRME (ne pas forcer « niée », laisser le LLM)
    r"n'a\s+pas\s+manqu", r"n'a\s+(?:jamais\s+)?cess", r"ne\s+cesse", r"n'a\s+pas\s+perdu",
    r"faux\s+de\s+dire", r"loin\s+d'?", r"\bdement\b", r"\bdementi", r"ne\s+saurait",
]
_RE_GARDE = re.compile("|".join(_GARDES_LITOTE))
_MARQUEURS_FIN = [
    r"\bne\s+\w+\s+plus\b", r"\bn'\w+\s+plus\b", r"\bne\s+\w+\s+pas\b", r"\bn'\w+\s+pas\b",
    r"\bplus\s+(?:partie|membre|dans|en\s+poste)\b", r"\bquitt\w*", r"\bsort\w*\s+(?:de|du|des|d')",
    r"\bse\s+retire\w*", r"\bs'est\s+retir\w*", r"\bretir[ée]\w*\s+d[eu']", r"\bd[ée]missionn\w*",
    r"\bd[ée]mis\w*\s+de\b", r"\bperd\w*\s+son\s+poste", r"\b[ée]limin[ée]\w*",
    r"\bexclus?e?\w*\s+d[eu']", r"\b[ée]cart[ée]\w*\s+d[eu']", r"\bpas\s+[ée]t[ée]\s+retenu\w*",
    r"\babandonn\w*", r"\bdestitu\w*", r"\bremplac[ée]\w*\s+(?:par|a\s+la\s+tete)",
    r"\b(?:a\s+ete|est|fut|ont\s+ete|sont|a\s+ete)\s+remplac[ée]\w*",  # PASSIF : le sujet est remplacé → il part
]
_RE_FIN = re.compile("|".join(_MARQUEURS_FIN))
# Continuité : la relation se POURSUIT (ne pas la lire comme une fin temporelle)
_RE_CONTINUITE = re.compile(r"n'a\s+(?:jamais\s+)?cess|ne\s+cesse|continue\s+(?:de|a)|\btoujours\b")


def _polarite_plancher(texte):
    """« niee » seulement sur une fin/négation EXPLICITE et SANS garde de litote ; sinon None (défère)."""
    t = _norm(texte)
    if _RE_GARDE.search(t):
        return None                                  # litote/double-négation → c'est au LLM de trancher
    return "niee" if _RE_FIN.search(t) else None


# ── PLANCHER MODALITÉ : irréel / rumeur clairs → non accompli ────────────────────────────────
_RE_NON_ACCOMPLI = re.compile(
    r"\benvisage\s+de\b|\bprojette\s+de\b|\bcompte\s+\w+er\b|\bpourrait\b|\bdevrait\b|"
    r"\bselon\s+(?:des\s+rumeurs|certaines\s+sources|des\s+sources)\b|\bserait\s+en\s+passe\b|"
    r"\bprepar\w*rait\b|\benvisagerait\b|\brachterait\b|\w+erait\b\s")


def _modalite_plancher(texte):
    return "projete" if _RE_NON_ACCOMPLI.search(_norm(texte)) else None


# ── PLANCHER TEMPORALITÉ : les MOTIFS DE DATE sont fiables → ils priment sur le LLM ──────────
_AN = r"(1[5-9]\d\d|20\d\d)"
_RE_INTERVALLE = re.compile(r"\bde\s+" + _AN + r"\s+(?:a|à)\s+" + _AN + r"\b|\bentre\s+" + _AN + r"\s+et\s+" + _AN + r"\b")
_RE_FIN_SEULE = re.compile(r"\bjusqu'?\s*(?:en|a|à|au)\s+" + _AN + r"\b")
_RE_DEBUT = re.compile(r"\bdepuis\s+" + _AN + r"\b|\ba\s+partir\s+de\s+" + _AN + r"\b")
_MOIS = r"(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)"
_RE_OCC = re.compile(r"\ble\s+\d{1,2}(?:er)?\s+" + _MOIS + r"\s+" + _AN + r"\b")


def _temporalite_plancher(texte):
    """Renvoie (forme, date_debut, date_fin) si un motif de date tranche, sinon None."""
    t = _norm(texte)
    m = _RE_INTERVALLE.search(t)
    if m:
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        return ("intervalle_ferme", a, b)
    m = _RE_FIN_SEULE.search(t)
    if m:
        return ("fin_seule", None, m.group(1))
    m = _RE_DEBUT.search(t)
    if m:
        return ("debut_seul", m.group(1) or m.group(2), None)
    m = _RE_OCC.search(t)
    if m:
        return ("occurrence", m.group(2), None)
    return None


SYS_EXTRACTION = (
    "Tu lis UN énoncé en français et tu remplis une GRILLE d'analyse, axe par axe. Tu n'inventes "
    "jamais un fait : tu décris seulement ce que la phrase dit.\n\n"
    "1) TRIPLET (sujet, predicat, objet). Le predicat DOIT venir de cette liste :\n"
    + vocabulaire_pour_extraction()
    + "\n   DIRECTION : sujet = l'entité qui PORTE la relation, objet = l'entité/valeur reliée. "
    "Respecte les types attendus (siege_de : sujet=organisation, objet=ville ; pdg_de/dirige : "
    "sujet=organisation, objet=personne).\n"
    "   INDICE boursier (CAC 40, SBF 120…) : entrer/rejoindre/intégrer/faire son entrée → "
    "predicat appartient_a (objet=l'indice) ; sortir/quitter/être retiré → appartient_a (la polarité "
    "« niee » exprimera la sortie). La VALEUR/le cours d'un indice (« vaut/cote/clôture à … points ») "
    "reste prix_de. SPORT : se qualifier/décrocher son billet → qualifie_pour.\n"
    "1bis) TYPE de CHAQUE entité (pas du prédicat), le plus PRÉCIS possible, parmi {personne, "
    "organisation, entreprise, pays, ville, lieu, date, valeur, oeuvre, film, livre, album, evenement, "
    "competition, distinction, groupe, equipe, espece, substance}. Sois SPÉCIFIQUE : un PAYS = pays "
    "(pas « lieu ») ; une VILLE = ville ; un FLEUVE/une MONTAGNE/une RÉGION = lieu ; une "
    "ENTREPRISE/INSTITUTION = organisation ; un PRIX/une MÉDAILLE/un TROPHÉE = distinction ; un "
    "FILM/LIVRE/ALBUM/TABLEAU = oeuvre. (Ces types FIXENT la direction de la relation.)\n"
    "2) POLARITÉ (porte sur le SENS, pas les mots) : "
    "affirmee = le fait tient · niee = nié ou prend fin (« ne… plus », « quitte », « démissionne ») · "
    "litote = négation qui affirme (« n'a pas manqué de nommer » = a nommé) · "
    "double_negation = « il serait faux de dire qu'il est parti » = il est resté.\n"
    "3) MODALITÉ : accompli = c'est le cas/arrivé · projete = hypothétique (« envisage de », "
    "« pourrait ») · rapporte = rumeur/conditionnel (« selon des rumeurs », « préparerait ») · "
    "nie_rapporte = « dément avoir ».\n"
    "4) TEMPORALITÉ (forme, INDÉPENDANTE de la polarité) : courant · debut_seul (« depuis X ») · "
    "fin_seule (« jusqu'en Y ») · intervalle_ferme (« de X à Y », début ET fin) · occurrence "
    "(événement ponctuel daté) · sans_date. date_debut/date_fin en AAAA-MM ou AAAA, sinon null.\n"
    "Réponds UNIQUEMENT en JSON strict :\n"
    '{"sujet":"…","predicat":"…","objet":"…","type_e_sujet":"…","type_e_objet":"…",'
    '"polarite":"affirmee|niee|litote|double_negation",'
    '"modalite":"accompli|projete|rapporte|nie_rapporte",'
    '"temporalite":"courant|debut_seul|fin_seule|intervalle_ferme|occurrence|sans_date",'
    '"date_debut":"AAAA-MM|AAAA|null","date_fin":"AAAA-MM|AAAA|null"}'
)

_MODALITES = ("accompli", "projete", "rapporte", "nie_rapporte")
_TEMPORALITES = ("courant", "debut_seul", "fin_seule", "intervalle_ferme", "occurrence", "sans_date")

# ── DROIT À L'ABSTENTION DE PRÉDICAT (option) : garder le VERBE BRUT plutôt que forcer une case ──
# Diagnostic : forcer la phrase dans une des 107 cases produit des absurdités (a_pour_capitale(mosquée)).
# La clause donne au greffier une SORTIE : si aucune case ne colle, garder le verbe du texte (préfixe ~).
# Précision INVERSÉE : ~ est le DERNIER recours (sinon on fragmenterait des relations canonisables).
# N'est ajoutée au prompt QUE si l'option est active → quand OFF, prompt et sorties INCHANGÉS (iso-résultat).
_ABSTENTION_CLAUSE = (
    "\n1ter) ABSTENTION DE PRÉDICAT (RÈGLE FORTE). Le prédicat que tu choisis DOIT vouloir dire la MÊME "
    "chose que le verbe de la phrase. Si le verbe de la phrase n'a PAS d'équivalent exact dans la liste, "
    "il est INTERDIT d'en détourner un au sens proche : tu DOIS alors écrire predicat = « ~ » suivi du "
    "verbe de la phrase à l'infinitif.\n"
    "   Exemples OBLIGATOIRES : « sont exfiltrés » → predicat=« ~exfiltrer » (PAS se_retire_de) ; "
    "« sont rapatriés » → « ~rapatrier » ; « bat en retraite » → « ~battre_en_retraite ». "
    "Au moindre doute « est-ce vraiment le même sens ? » → utilise « ~verbe ». Mieux vaut le verbe brut "
    "fidèle qu'une case au sens différent."
)


def _sys(base):
    """Prompt système, augmenté de la clause d'abstention SEULEMENT si l'option est active."""
    return base + _ABSTENTION_CLAUSE if config.OPT_ABSTENTION_PREDICAT else base


# ── REROUTAGE DATE ÉVÉNEMENTIEL : prédicat-agent + objet ANNÉE → le prédicat de DATE adéquat ──────
_REROUTE_DATE = {"a_fonde": "date_fondation_de", "a_publie": "date_sortie_de",
                 "a_cree": "date_sortie_de", "a_lance": "date_sortie_de"}
_RE_DATE_OBJ = re.compile(r"^\s*(en\s+|vers\s+)?\d{4}(-\d{2}){0,2}\s*$", re.IGNORECASE)


def _est_date_obj(o):
    """True si l'objet est une PURE date (année AAAA, ou AAAA-MM(-JJ)) — pas une entité."""
    return bool(_RE_DATE_OBJ.match(str(o)))

# ── AXE RÔLE/DIRECTION : la direction se DÉRIVE des TYPES, pas de la grammaire ────────────────
# Un type d'entité (tel que nommé par le LLM) → l'ensemble des « cases » de signature qu'il peut remplir.
# Un PAYS remplit lieu ET organisation (acteur) → tolérance pour les prédicats géo/politiques.
_TAGS_TYPE = {
    "personne": {"personne"}, "individu": {"personne"}, "scientifique": {"personne"},
    "artiste": {"personne"}, "athlete": {"personne"}, "joueur": {"personne"}, "acteur": {"personne"},
    "ecrivain": {"personne"}, "dirigeant": {"personne"}, "homme": {"personne"}, "femme": {"personne"},
    "organisation": {"organisation"}, "entreprise": {"organisation"}, "societe": {"organisation"},
    "institution": {"organisation"}, "club": {"organisation", "groupe"}, "parti": {"organisation"},
    "federation": {"organisation"}, "comite": {"organisation"}, "banque": {"organisation"},
    "pays": {"lieu", "organisation"}, "etat": {"lieu", "organisation"}, "nation": {"lieu", "organisation", "groupe"},
    "lieu": {"lieu"}, "ville": {"lieu"}, "capitale": {"lieu"}, "region": {"lieu"}, "continent": {"lieu"},
    "fleuve": {"lieu"}, "riviere": {"lieu"}, "montagne": {"lieu"}, "mer": {"lieu"}, "ocean": {"lieu"},
    "desert": {"lieu"}, "commune": {"lieu"},
    "oeuvre": {"oeuvre"}, "film": {"oeuvre"}, "livre": {"oeuvre"}, "roman": {"oeuvre"},
    "album": {"oeuvre"}, "tableau": {"oeuvre"}, "chanson": {"oeuvre"}, "produit": {"oeuvre"}, "texte": {"oeuvre"},
    "date": {"date"}, "annee": {"date"}, "periode": {"date"},
    "valeur": {"valeur"}, "nombre": {"valeur"}, "quantite": {"valeur"}, "mesure": {"valeur"},
    "record": {"valeur"}, "prix": {"valeur", "distinction"},
    "distinction": {"distinction"}, "recompense": {"distinction"}, "medaille": {"distinction"},
    "trophee": {"distinction"}, "titre": {"distinction"},
    "groupe": {"groupe"}, "equipe": {"groupe", "organisation"}, "selection": {"groupe"},
    "evenement": {"evenement"}, "competition": {"evenement", "competition"}, "match": {"evenement"},
    "tournoi": {"evenement"}, "sommet": {"evenement"}, "ceremonie": {"evenement"}, "festival": {"evenement"},
    "espece": {"espece"}, "animal": {"espece"}, "plante": {"espece"},
    "substance": {"substance"}, "molecule": {"substance"}, "element": {"substance"}, "gaz": {"substance"},
}


def _tags(type_brut):
    """Ensemble des cases de signature qu'une entité de ce type peut remplir (vide si type inconnu)."""
    t = _norm(type_brut).strip()
    return _TAGS_TYPE.get(t, set())


def _assigner_role(predicat, sujet, objet, type_s, type_o):
    """Oriente (sujet, objet) selon la SIGNATURE de type du prédicat. Ne swappe QUE sur un croisement
    de types NET ; sinon garde l'ordre grammatical (règle d'or : pas d'inversion silencieuse).
    Renvoie (sujet, objet, type_sujet, type_objet) — les types suivent l'entité (swappés ensemble)."""
    sig = PREDICATS.get(predicat, {})
    sig_ts, sig_to = sig.get("type_sujet"), sig.get("type_objet")
    if not sig_ts or not sig_to or sig_ts == sig_to:
        return sujet, objet, type_s, type_o      # signature symétrique → ordre grammatical (secours)
    ts, to = _tags(type_s), _tags(type_o)
    if not ts and not to:
        return sujet, objet, type_s, type_o      # types inconnus → prudence, on ne touche pas
    garde_ok = (sig_ts in ts) and (sig_to in to)
    swap_ok = (sig_ts in to) and (sig_to in ts)
    if swap_ok and not garde_ok:                 # surface inversée → on swappe entités ET types
        return objet, sujet, type_o, type_s
    return sujet, objet, type_s, type_o          # match propre, ambigu, ou non concluant → on garde


def _finaliser(brut, texte, contexte, llm):
    """Grille LLM brute d'UN fait → dict d'axes finalisé (planchers déterministes, couverture,
    canonisation, axe rôle, cascade b1 anti-pronom + b2 coréférence, types), ou None si invalide.
    Logique PARTAGÉE par l'extraction SINGLE et MULTI : tout fait extrait — d'une phrase mono-fait ou
    multi-fait — reçoit EXACTEMENT les mêmes garde-fous (0 FP polarité, anti-pronom, coréférence)."""
    if not isinstance(brut, dict):
        return None
    sujet = str(brut.get("sujet", "")).strip()
    predicat = str(brut.get("predicat", "")).strip()
    objet = str(brut.get("objet", "")).strip()

    # POLARITÉ : litote/double_negation → affirmée ; plancher déterministe force « niee » (sauf garde)
    pol = "niee" if _norm(brut.get("polarite", "")) == "niee" else "affirmee"
    if _polarite_plancher(texte) == "niee":
        pol = "niee"

    # MODALITÉ : LLM, avec plancher pour l'irréel clair
    mod = _norm(brut.get("modalite", "")) or "accompli"
    if mod not in _MODALITES:
        mod = "accompli"
    if _modalite_plancher(texte):
        mod = "projete"

    # TEMPORALITÉ + dates : le motif de date (déterministe) PRIME sur le LLM
    temp = _norm(brut.get("temporalite", "")) or "sans_date"
    if temp not in _TEMPORALITES:
        temp = "sans_date"
    deb, fin = _date(brut.get("date_debut")), _date(brut.get("date_fin"))
    plancher_t = _temporalite_plancher(texte)
    if plancher_t:
        temp, d2, f2 = plancher_t
        deb, fin = (d2 or deb), (f2 or fin)
    if _RE_CONTINUITE.search(_norm(texte)):     # « n'a jamais cessé de », « continue de » → courant
        temp, fin = "courant", None

    # ABSTENTION DE PRÉDICAT (option) : un prédicat préfixé « ~ » = le greffier a renoncé à forcer une
    # case et garde le VERBE BRUT du texte. Reconnu → gardé HORS-ontologie (ni canonisation ni axe rôle,
    # faute de signature) MAIS soumis à TOUS les autres garde-fous (pronom, coréférence, polarité…).
    brut_verbe = False
    if config.OPT_ABSTENTION_PREDICAT and predicat.startswith("~"):
        cand = _norm(predicat[1:]).strip()
        cano = CANON_VERBES_BRUTS.get(cand) if config.OPT_CANON_VERBES_BRUTS else None
        if cand in PREDICATS:
            predicat = cand                       # « ~ » apposé à un VRAI prédicat → traiter normalement
        elif cano:
            predicat = cano                       # Temps A : verbe brut rabattu sur sa case canonique
        else:
            predicat, brut_verbe = cand, True     # vrai verbe brut hors-ontologie → abstention

    if brut_verbe:
        if not predicat or not sujet or not objet:
            return None
    elif predicat not in PREDICATS or not sujet or not objet:   # 5e axe : couverture d'ontologie
        return None

    if brut_verbe:
        t_s, t_o = brut.get("type_e_sujet"), brut.get("type_e_objet")   # pas de signature → ordre gardé
    else:
        # CANONISATION DES PRÉDICATS (chantier 1) : une forme synonyme (pdg_de, a_dirige) → le prédicat
        # canonique (dirige), AVANT l'axe rôle — pour que les sources s'accumulent et les conflits
        # s'enregistrent. La direction sera (r)établie juste après par _assigner_role via les signatures.
        predicat = CANON_PREDICATS.get(predicat, predicat)
        # REROUTAGE DATE ÉVÉNEMENTIEL : un prédicat-AGENT (a_fonde/a_publie/a_cree/a_lance, qui attend
        # une personne/entité en objet) avec un objet = pure DATE est TOUJOURS faux (« créé en 1944 » →
        # a_fonde(org→1944)). On reroute vers la date_*_de adéquate → la date atterrit au bon prédicat.
        if config.OPT_REROUTE_DATE and predicat in _REROUTE_DATE and _est_date_obj(objet):
            predicat = _REROUTE_DATE[predicat]
        # AXE RÔLE/DIRECTION : oriente par les TYPES des entités (swap si la surface est inversée)
        sujet, objet, t_s, t_o = _assigner_role(predicat, sujet, objet,
                                                brut.get("type_e_sujet"), brut.get("type_e_objet"))

    # FENÊTRE DE CORÉFÉRENCE (brique 2) : un pronom-sujet/objet n'ancre aucun fait. AVANT d'abstenir,
    # on tente de le rattacher à un antécédent NOMMÉ proche (contexte glissant). Résolu → on écrit au
    # nom résolu (le vrai levier des faits-clés) ; non résolu / ambigu → la brique 1 reprend ci-dessous.
    if contexte:
        if _est_pronom(sujet):
            sujet = _resoudre_coref(llm, sujet, "sujet", texte, contexte) or sujet
        if _est_pronom(objet):
            objet = _resoudre_coref(llm, objet, "objet", texte, contexte) or objet

    # PROPRETÉ À LA SOURCE (brique 1) : si une extrémité reste un pronom/indéfini (non résolu), il n'y
    # a pas d'entité nommée pour ancrer le fait → ABSTENTION COMPLÈTE (pas de nœud-pronom, pas de fait
    # orphelin). C'est le FILET sous la fenêtre : on ne devine jamais un antécédent.
    if _est_pronom(sujet) or _est_pronom(objet):
        return None
    # SOCLE TYPE : le type extrait par le greffier VOYAGE jusqu'au nœud (grain fin : pays/ville/…)
    type_sujet = (_norm(t_s) or None) if t_s else None
    type_objet = (_norm(t_o) or None) if t_o else None

    return {"sujet": sujet, "predicat": predicat, "objet": objet,
            "type_sujet": type_sujet, "type_objet": type_objet,
            "polarite": pol, "modalite": mod, "temporalite": temp,
            "date_debut": deb, "date_fin": fin}


SYS_EXTRACTION_MULTI = SYS_EXTRACTION.split("Réponds UNIQUEMENT")[0] + (
    "Une phrase peut contenir PLUSIEURS faits DISTINCTS (ex. « né en 1973 à Toulouse, joueur de rugby » "
    "= date de naissance + lieu de naissance + profession). EXTRAIS-LES TOUS, chacun comme une entrée "
    "COMPLÈTE de la grille (avec SES propres axes). N'invente RIEN ; n'éclate pas un fait unique en "
    "morceaux artificiels. Si la phrase ne porte qu'un fait, renvoie une seule entrée.\n"
    "Un ADJECTIF DE NATIONALITÉ attaché à une personne (« joueur FRANÇAIS », « philologue AMÉRICAIN », "
    "« cycliste BELGE ») est un fait SÉPARÉ : a_nationalite(personne)=la nationalité — ne le fonds PAS "
    "dans la profession (profession_de garde le métier seul : « joueur de rugby », « philologue »).\n"
    "Réponds UNIQUEMENT en JSON strict :\n"
    '{"faits":[{"sujet":"…","predicat":"…","objet":"…","type_e_sujet":"…","type_e_objet":"…",'
    '"polarite":"affirmee|niee|litote|double_negation",'
    '"modalite":"accompli|projete|rapporte|nie_rapporte",'
    '"temporalite":"courant|debut_seul|fin_seule|intervalle_ferme|occurrence|sans_date",'
    '"date_debut":"AAAA-MM|AAAA|null","date_fin":"AAAA-MM|AAAA|null"}]}'
)


# ── COMPLÉTUDE (option) : forcer le multi-triplets à ne lâcher AUCUN fait d'une phrase dense ─────
_COMPLETUDE_CLAUSE = (
    "\nEXHAUSTIVITÉ — ne lâche AUCUN fait. Une phrase biographique condensée porte PLUSIEURS faits : "
    "sors-les TOUS, séparément. Pour une PERSONNE, passe systématiquement en revue et extrais CHACUN "
    "s'il est présent : date de naissance · LIEU de naissance · profession · nationalité · date/lieu de "
    "décès. Dans une apposition « né le DATE à LIEU » il y a DEUX faits — ne lâche JAMAIS le LIEU quand "
    "la date est donnée. Pour une ORGANISATION/ŒUVRE : date de fondation/sortie, siège, fondateur. "
    "Exemple : « Colin Gaston, né le 22 avril 1973 à Toulouse, est un joueur français de rugby » → "
    "QUATRE faits : date_naissance_de=1973 · lieu_naissance_de=Toulouse · profession_de=joueur de rugby "
    "· a_nationalite=français."
)


def _multi_sys():
    """Prompt multi, augmenté de la clause de complétude SEULEMENT si l'option est active."""
    return SYS_EXTRACTION_MULTI + _COMPLETUDE_CLAUSE if config.OPT_EXTRACTION_COMPLETE else SYS_EXTRACTION_MULTI


def extraire(llm, texte, contexte=None):
    """SINGLE (inchangé) : la grille d'UN fait. Conserve le comportement historique (barometre, bancs).
    `contexte` active la coréférence (brique 2) ; sans contexte → comportement brique 1."""
    brut = llm.json(f"Énoncé : « {texte} »\n\nRemplis la grille en JSON strict.", systeme=_sys(SYS_EXTRACTION))
    return _finaliser(brut, texte, contexte, llm)


def extraire_liste(llm, texte, contexte=None):
    """MULTI-TRIPLETS : extrait TOUS les faits distincts d'une phrase (1..N). Chaque fait passe par la
    MÊME `_finaliser` que le single → mêmes garde-fous (0 FP, anti-pronom, coréférence). Dé-doublonné."""
    d = llm.json(f"Énoncé : « {texte} »\n\nExtrais TOUS les faits distincts, en JSON strict.",
                 systeme=_sys(_multi_sys()))
    faits = d.get("faits") if isinstance(d, dict) else None
    if not isinstance(faits, list):
        return []
    out, vus = [], set()
    for b in faits:
        f = _finaliser(b, texte, contexte, llm)
        if f:
            cle = (_norm(f["sujet"]), f["predicat"], _norm(f["objet"]))
            if cle not in vus:
                vus.add(cle); out.append(f)
    return out


def deriver(axes):
    """DÉRIVATION DÉTERMINISTE : des axes → l'intention {action, dates}. Le cœur prévisible de V2.
    action ∈ {RIEN, CLOTURE_NIEE, FAIT_CLOS, COURANT}. Règle d'or : le doute → RIEN."""
    mod, pol, temp = axes["modalite"], axes["polarite"], axes["temporalite"]
    deb, fin = axes["date_debut"], axes["date_fin"]
    if mod != "accompli":
        return {"action": "RIEN", "raison": f"modalité={mod} (non accompli) → aucun fait affirmé"}
    if pol == "niee":
        return {"action": "CLOTURE_NIEE", "fin": fin}          # clore l'existant, sinon rien
    if temp in ("intervalle_ferme", "fin_seule"):
        return {"action": "FAIT_CLOS", "debut": deb, "fin": fin}   # histoire bornée DÉCLARÉE → clos
    return {"action": "COURANT", "debut": deb}                 # courant / debut_seul / occurrence / sans_date
