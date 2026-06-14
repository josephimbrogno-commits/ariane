# -*- coding: utf-8 -*-
"""
memoire/adaptateurs/ollama_qwen.py — adaptateur d'EXEMPLE (Ollama + sentence-transformers).

Découplé du cœur : la bibliothèque ne fabrique pas son modèle, on lui injecte cet objet. Tout hôte
(OpenClaw ou autre) peut fournir le sien, du moment qu'il offre la même petite interface :
  llm.texte(prompt, systeme=None, temperature=0.0) -> str
  llm.json(prompt, systeme=None) -> dict
  embed(texte) -> vecteur numpy normalisé
"""

import json
import os


def _sans_pensee(txt):
    """qwen3 émet parfois un monologue de raisonnement terminé par </think> (la balise ouvrante
    peut manquer) : on ne garde que ce qui suit la dernière </think>."""
    if "</think>" in txt:
        txt = txt.rsplit("</think>", 1)[1]
    return txt.strip()


class OllamaLLM:
    def __init__(self, modele="qwen3:30b-a3b", url="http://localhost:11434", think=False, timeout=180):
        self.modele, self.url, self.think, self.timeout = modele, url, think, timeout

    def _appel(self, prompt, systeme, format_json, temperature):
        import requests
        payload = {"model": self.modele, "prompt": prompt, "stream": False,
                   "options": {"temperature": temperature}}
        if systeme:
            payload["system"] = systeme
        if format_json:
            payload["format"] = "json"
        if self.think is not None:
            payload["think"] = self.think
        r = requests.post(f"{self.url}/api/generate", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return _sans_pensee(r.json()["response"])

    def texte(self, prompt, systeme=None, temperature=0.0):
        return self._appel(prompt, systeme, False, temperature)

    def json(self, prompt, systeme=None):
        for tentative in range(3):
            brut = self._appel(prompt, systeme, True, 0.0 + 0.3 * tentative)
            if brut and brut.strip():
                try:
                    return json.loads(brut)
                except json.JSONDecodeError:
                    d, f = brut.find("{"), brut.rfind("}")
                    if d != -1 and f != -1:
                        try:
                            return json.loads(brut[d:f + 1])
                        except json.JSONDecodeError:
                            pass
        return {}


def faire_embed(modele="paraphrase-multilingual-MiniLM-L12-v2"):
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_TORCH", "1")
    import numpy as np
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(modele)

    def embed(texte):
        return np.asarray(m.encode(texte, normalize_embeddings=True, show_progress_bar=False),
                          dtype=np.float32)
    return embed
