# -*- coding: utf-8 -*-
"""
etape0_check.py — vérifie que tout est prêt.

Teste : Ollama répond, le modèle de langage répond, les embeddings se chargent.
Lance simplement :  python etape0_check.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # se placer dans le dossier du projet
try:
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows en UTF-8 (accents, ✓, …)
except Exception:
    pass

import config


def main():
    print("=" * 70)
    print(" ÉTAPE 0 — Vérification de l'environnement")
    print("=" * 70)

    ok = True

    # 1) Ollama + modèle de langage
    print(f"\n[1/2] Modèle de langage « {config.MODELE_LLM} » via Ollama…")
    try:
        import modele
        if not modele.disponible():
            print("  ✗ Ollama ne répond pas ou le modèle est absent.")
            print(f"    → Vérifie qu'Ollama tourne, puis : ollama pull {config.MODELE_LLM}")
            ok = False
        else:
            r = modele.repondre("Réponds en un seul mot : capitale de la France ?")
            print(f"  ✓ Le modèle répond : « {r} »")
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        ok = False

    # 2) Embeddings
    print(f"\n[2/2] Embeddings « {config.MODELE_EMBEDDINGS} »…")
    try:
        from embeddings import encoder
        import numpy as np
        v = encoder(["bonjour le monde", "salut tout le monde", "le chat dort"])
        sim = float(v[0] @ v[1])
        print(f"  ✓ Embeddings chargés. Dimension = {v.shape[1]}.")
        print(f"    (similarité 'bonjour le monde' ~ 'salut tout le monde' = {sim:.2f})")
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        ok = False

    print("\n" + "=" * 70)
    if ok:
        print(" ✅ ENVIRONNEMENT PRÊT — tu peux lancer l'étape 1 :")
        print("    python etape1_micro.py")
    else:
        print(" ❌ Des éléments manquent (voir ci-dessus).")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
