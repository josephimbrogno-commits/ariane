# -*- coding: utf-8 -*-
"""
embeddings.py — transforme un texte en vecteur (pour la recherche par similarité).

Le modèle est chargé une seule fois (paresseusement) puis réutilisé.
Vecteurs normalisés : la similarité cosinus = simple produit scalaire.
"""

import os

# On force le backend PyTorch et on empêche transformers de charger TensorFlow/Keras
# (Keras 3 est incompatible et provoquait une erreur d'import).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import numpy as np
from sentence_transformers import SentenceTransformer

import config

_modele = None


def _charger():
    global _modele
    if _modele is None:
        print(f"   (chargement du modèle d'embeddings « {config.MODELE_EMBEDDINGS} »…)")
        _modele = SentenceTransformer(config.MODELE_EMBEDDINGS)
    return _modele


def encoder(textes):
    """Encode une liste de textes -> matrice numpy (n, d), vecteurs normalisés."""
    m = _charger()
    v = m.encode(list(textes), normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32)


def encoder_un(texte):
    """Encode un seul texte -> vecteur numpy (d,)."""
    return encoder([texte])[0]
