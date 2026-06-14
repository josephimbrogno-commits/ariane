# -*- coding: utf-8 -*-
"""
memoire/options/ — les capacités OPTIONNELLES, branchées par interrupteurs de config.

  • importance        (OPT_IMPORTANCE)         — 3ᵉ axe PageRank ; calculé au sommeil via le hook.
  • dormance modulée  (OPT_DORMANCE_MODULEE)   — seuil de dormance abaissé par l'importance (graphe).
  • reconnaissance    (OPT_RECONNAISSANCE)     — entrée par nœud nommé (lit les dormants) — lecture.
  • typologie liens   (OPT_TYPOLOGIE)          — DURABLE/ÉPHÉMÈRE d'un lien — lecture.

Règle d'inertie : tant que l'interrupteur n'est pas basculé, l'option ne modifie RIEN. `importance`
et `dormance modulée` sont OFF par défaut : le hook ne calcule alors aucune importance, et le seuil
de dormance reste à sa valeur de base (β=0).

`hook_consolidation(g)` est branché par api.Memoire.consolider : il n'agit que si l'option est ON.
"""

from .. import config
from . import importance, typologie_liens   # noqa: F401  (réexport pour l'hôte)


def hook_consolidation(g):
    """Appelé pendant le sommeil, AVANT la dormance. N'agit que si l'option importance est ON
    (sinon inerte : aucune importance calculée, f.importance reste à sa valeur par défaut)."""
    if config.OPT_IMPORTANCE:
        importance.calculer(g)
