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

from .ontologie import PREDICATS, vocabulaire_pour_extraction


def _norm(texte):
    s = unicodedata.normalize("NFD", str(texte).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("’", "'").replace("`", "'")


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
    de types NET ; sinon garde l'ordre grammatical (règle d'or : pas d'inversion silencieuse)."""
    sig = PREDICATS.get(predicat, {})
    sig_ts, sig_to = sig.get("type_sujet"), sig.get("type_objet")
    if not sig_ts or not sig_to or sig_ts == sig_to:
        return sujet, objet                      # signature symétrique → ordre grammatical (secours)
    ts, to = _tags(type_s), _tags(type_o)
    if not ts and not to:
        return sujet, objet                      # types inconnus → prudence, on ne touche pas
    garde_ok = (sig_ts in ts) and (sig_to in to)
    swap_ok = (sig_ts in to) and (sig_to in ts)
    if swap_ok and not garde_ok:                 # la surface est inversée par rapport à la signature
        return objet, sujet
    return sujet, objet                          # match propre, ambigu, ou non concluant → on garde


def extraire(llm, texte):
    """Résout les axes (grille LLM + planchers déterministes) → dict d'axes, ou None si invalide."""
    brut = llm.json(f"Énoncé : « {texte} »\n\nRemplis la grille en JSON strict.", systeme=SYS_EXTRACTION)
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

    if predicat not in PREDICATS or not sujet or not objet:   # 5e axe : couverture d'ontologie
        return None

    # AXE RÔLE/DIRECTION : oriente par les TYPES des entités (swap si la surface est inversée)
    sujet, objet = _assigner_role(predicat, sujet, objet,
                                  brut.get("type_e_sujet"), brut.get("type_e_objet"))

    return {"sujet": sujet, "predicat": predicat, "objet": objet,
            "polarite": pol, "modalite": mod, "temporalite": temp,
            "date_debut": deb, "date_fin": fin}


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
