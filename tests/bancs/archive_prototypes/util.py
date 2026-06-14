# -*- coding: utf-8 -*-
"""util.py — petits outils transverses (journal, dossiers)."""

import os
from datetime import datetime

import config


def assurer_dossiers():
    os.makedirs(config.DOSSIER_LOGS, exist_ok=True)
    os.makedirs(config.DOSSIER_RESULTATS, exist_ok=True)


class Journal:
    """Affiche à l'écran ET enregistre dans un fichier logs/<nom>-<horodatage>.log."""

    def __init__(self, nom):
        assurer_dossiers()
        horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.chemin = os.path.join(config.DOSSIER_LOGS, f"{nom}-{horodatage}.log")
        self._f = open(self.chemin, "w", encoding="utf-8")

    def dire(self, texte=""):
        print(texte)
        self._f.write(texte + "\n")
        self._f.flush()

    def fermer(self):
        self._f.close()
