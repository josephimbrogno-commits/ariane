# -*- coding: utf-8 -*-
"""memoire — bibliothèque de mémoire à graphe daté (V2 consolidée + options).

Geste minimal :
    from memoire import Memoire
    from memoire.adaptateurs.ollama_qwen import OllamaLLM, faire_embed
    mem = Memoire(llm=OllamaLLM(), embed=faire_embed())
    mem.ecrire("Le PDG de Nexora est Mme Karel.", source_id="Gazette")
    print(mem.lire("Qui dirige Nexora ?")["reponse"])
"""

from .api import Memoire

__all__ = ["Memoire"]
