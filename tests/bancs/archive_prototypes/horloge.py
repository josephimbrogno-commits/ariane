# -*- coding: utf-8 -*-
"""
horloge.py — horloge VIRTUELLE.

Le temps de l'expérience est simulé : on peut « avancer » de plusieurs jours
ou mois d'un coup pour compresser une chronologie de 12 mois en quelques minutes.
"""

from datetime import timedelta


class HorlogeVirtuelle:
    def __init__(self, date_debut):
        self.date = date_debut

    def maintenant(self):
        return self.date

    def avancer(self, jours):
        """Avance l'horloge simulée de `jours` jours (peut être fractionnaire)."""
        self.date = self.date + timedelta(days=jours)

    def texte(self):
        return self.date.strftime("%Y-%m-%d")

    def __repr__(self):
        return f"<Horloge {self.texte()}>"
