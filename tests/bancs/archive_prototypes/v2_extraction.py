# -*- coding: utf-8 -*-
"""
v2_extraction.py — extraction de TRIPLETS depuis un énoncé (mission V2, §2.1).

Appel LLM (qwen, JSON strict) : énoncé → (sujet, predicat, objet, date_validite).
La SOURCE n'est pas extraite du texte : elle est fournie séparément (qui rapporte l'info).

C'est la nouvelle SURFACE D'ERREUR principale du V2 — on mesure sa fiabilité honnêtement
(étape v2.1 : comparaison à une vérité-terrain de triplets).
"""

import config
import modele
from v2_ontologie import PREDICATS, vocabulaire_pour_extraction

SYS_EXTRACTION = (
    "Tu extrais UN fait structuré d'un énoncé en français, sous forme de triplet "
    "(sujet, prédicat, objet). Le prédicat DOIT appartenir à cette liste :\n"
    + vocabulaire_pour_extraction()
    + "\n\nRègles :\n"
    "- sujet = l'entité dont on parle (entreprise, personne, lieu).\n"
    "- objet = la valeur ou l'entité reliée.\n"
    "- Pour pdg_de/maire_de : sujet = l'organisation, objet = la personne.\n"
    "- date_validite = la date À PARTIR DE LAQUELLE le fait est vrai SI elle est explicitement "
    "énoncée (« depuis mai 2026 », « en 1998 »), au format AAAA-MM ou AAAA ; sinon null.\n"
    "Réponds UNIQUEMENT en JSON strict : "
    '{"sujet":"...","predicat":"...","objet":"...","date_validite":"AAAA-MM ou AAAA ou null"}'
)


def extraire(texte):
    """Renvoie un dict {sujet, predicat, objet, date_validite} ou None si invalide."""
    brut = modele.juger(  # réutilise l'appel JSON robuste (retries) ; ce n'est pas un « jugement »
        f"Énoncé : « {texte} »\n\nExtrais le triplet en JSON strict.",
        systeme=SYS_EXTRACTION, model=config.MODELE_JUGE, think=config.JUGE_THINK,
    )
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
