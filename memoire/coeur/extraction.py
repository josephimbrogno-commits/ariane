# -*- coding: utf-8 -*-
"""
memoire/coeur/extraction.py — énoncé en langage naturel → triplet (le LLM est INJECTÉ).

Le LLM ne décide JAMAIS de la vérité : il habille/extrait seulement. Interface attendue :
`llm.json(prompt, systeme) -> dict`.
"""

from .ontologie import PREDICATS, vocabulaire_pour_extraction

SYS_EXTRACTION = (
    "Tu extrais UN fait structuré d'un énoncé en français, sous forme de triplet "
    "(sujet, prédicat, objet). Le prédicat DOIT appartenir à cette liste :\n"
    + vocabulaire_pour_extraction()
    + "\n\nRègles :\n"
    "- sujet = l'entité dont on parle ; objet = la valeur ou l'entité reliée.\n"
    "- Pour pdg_de/maire_de/dirige : sujet = l'organisation, objet = la personne.\n"
    "- date_validite = la date À PARTIR DE LAQUELLE le fait est vrai SI explicitement énoncée "
    "(« depuis mai 2026 », « en 1998 »), au format AAAA-MM ou AAAA ; sinon null.\n"
    "Réponds UNIQUEMENT en JSON strict : "
    '{"sujet":"...","predicat":"...","objet":"...","date_validite":"AAAA-MM ou AAAA ou null"}'
)


def extraire(llm, texte):
    """Renvoie {sujet, predicat, objet, date_validite} ou None si invalide."""
    brut = llm.json(f"Énoncé : « {texte} »\n\nExtrais le triplet en JSON strict.",
                    systeme=SYS_EXTRACTION)
    if not isinstance(brut, dict):
        return None
    sujet = str(brut.get("sujet", "")).strip()
    predicat = str(brut.get("predicat", "")).strip()
    objet = str(brut.get("objet", "")).strip()
    dv = brut.get("date_validite", None)
    if isinstance(dv, str) and dv.lower() in ("null", "none", ""):
        dv = None
    if predicat not in PREDICATS or not sujet or not objet:
        return None
    return {"sujet": sujet, "predicat": predicat, "objet": objet, "date_validite": dv}
