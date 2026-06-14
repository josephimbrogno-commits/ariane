# -*- coding: utf-8 -*-
"""
modele.py — petite passerelle vers le modèle local servi par Ollama.

Deux usages :
  - repondre(...) : le modèle répond à une question (texte libre).
  - juger(...)    : le modèle vérifie (sortie JSON stricte forcée par Ollama).

On n'utilise que `requests` (pas de dépendance supplémentaire à installer).
"""

import json
import requests

import config


def _appel(model, prompt, systeme, format_json, temperature, think=None):
    """Appel bas-niveau à l'API /api/generate d'Ollama."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if systeme:
        payload["system"] = systeme
    if format_json:
        # Ollama garantit alors une sortie JSON syntaxiquement valide.
        payload["format"] = "json"
    if think is not None:
        # Pour les modèles « à raisonnement » (qwen3, deepseek-r1) : couper la
        # réflexion verbeuse et n'obtenir que le JSON final.
        payload["think"] = think

    r = requests.post(
        f"{config.OLLAMA_URL}/api/generate",
        json=payload,
        timeout=config.TIMEOUT_LLM,
    )
    r.raise_for_status()
    return r.json()["response"].strip()


def repondre(prompt, systeme=None, temperature=None, model=None):
    """Le modèle répond à une question en texte libre. `model` permet de choisir le répondeur."""
    if temperature is None:
        temperature = config.TEMPERATURE_REPONSE
    if model is None:
        model = config.MODELE_LLM
    return _appel(model, prompt, systeme, False, temperature)


def _parser_json(brut):
    """Parse du JSON, avec repli sur l'extraction du premier objet { … }."""
    if not brut or not brut.strip():
        raise json.JSONDecodeError("réponse vide", brut or "", 0)
    try:
        return json.loads(brut)
    except json.JSONDecodeError:
        debut = brut.find("{")
        fin = brut.rfind("}")
        if debut != -1 and fin != -1:
            return json.loads(brut[debut:fin + 1])
        raise


def juger(prompt, systeme=None, temperature=None, model=None, think=None):
    """Le modèle joue le vérificateur. Renvoie un dict Python (JSON parsé).

    model : permet de tester un autre juge (ex. 'qwen3:30b-a3b').
    think : False pour couper le raisonnement des modèles qwen3/deepseek-r1.

    Robuste : certains modèles renvoient parfois une réponse vide avec format=json.
    On réessaie alors quelques fois (en variant un peu la température pour casser le
    déterminisme), puis on se replie sur un résultat vide plutôt que de planter.
    """
    if temperature is None:
        temperature = config.TEMPERATURE_JUGE
    if model is None:
        model = config.MODELE_JUGE

    for tentative in range(3):
        temp = temperature + 0.3 * tentative  # 0.0, 0.3, 0.6 : débloque les réponses vides
        brut = _appel(model, prompt, systeme, True, temp, think=think)
        try:
            return _parser_json(brut)
        except json.JSONDecodeError:
            continue
    # Échec après plusieurs tentatives : on renvoie un résultat vide (verdicts INCERTAIN).
    return {"verdicts": []}


def disponible():
    """Vérifie qu'Ollama répond et que le modèle est présent."""
    try:
        r = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        noms = [m["name"] for m in r.json().get("models", [])]
        return config.MODELE_LLM in noms or any(
            n.startswith(config.MODELE_LLM.split(":")[0]) for n in noms
        )
    except Exception:
        return False
