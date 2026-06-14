# -*- coding: utf-8 -*-
"""
exemples/vitrine.py — la mémoire branchée en quelques lignes.

Une histoire complète : un fait, un fait plus récent qui le contredit, le sommeil, puis la lecture.
Ce qu'une base de données ne ferait PAS et que cette mémoire fait :
  • elle DATE chaque fait ;
  • quand un fait nouveau et plus récent contredit l'ancien, elle CLÔT l'ancien sans le DÉTRUIRE ;
  • elle parle au BON TEMPS : présent pour ce qui est courant, « était… jusqu'à » pour le clos.

Pré-requis : Ollama qui tourne (qwen3:30b-a3b) + sentence-transformers.  Lance : python exemples/vitrine.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from memoire import Memoire
from memoire.adaptateurs.ollama_qwen import OllamaLLM, faire_embed

mem = Memoire(llm=OllamaLLM(), embed=faire_embed())          # on INJECTE le modèle ; la lib est agnostique

mem.ecrire("En janvier 2026, le PDG de Nexora est Mme Karel.", source_id="Gazette",   date=datetime(2026, 1, 1))
mem.ecrire("Depuis mai 2026, le PDG de Nexora est M. Doss.",   source_id="Officiel",  date=datetime(2026, 5, 1))
mem.consolider(date=datetime(2026, 6, 1))                    # le « sommeil » : érosions, clôtures, dormance

vue = mem.lire("Qui dirige Nexora aujourd'hui ?", date=datetime(2026, 6, 1))

print("\n— CE QUE LA MÉMOIRE SAIT (grammaire épistémique, brute) —")
print(vue["bloc"])                                           # [ACTUEL — sûr] présent · [CLOS] « était… jusqu'à »
print("\n— CE QU'ELLE RÉPOND (langue naturelle, au bon temps) —")
print(vue["reponse"])
print("\n— LA TRACE : l'ancien PDG n'est pas effacé, il est clos et daté —")
for f in mem.inspecter("Nexora")["faits"]:
    print("  ", f)
