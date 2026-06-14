# -*- coding: utf-8 -*-
"""
memoire_store.py — LA MÉMOIRE elle-même.

Contient :
  - la classe Souvenir   : un fait + ses métadonnées (dates, confiance, compteurs)
  - la classe Memoire    : le magasin (ajout, recherche, verdicts, érosion, sommeil)

Les 3 mécanismes du projet vivent ici :
  • SURPRISE      : appliquer_verdict(...) → CONTREDIT fait chuter la confiance
  • PÉREMPTION    : eroder()              → la confiance décroît avec le temps
  • RENFORCEMENT  : appliquer_verdict(...) → CONFIRME remonte la confiance + rafraîchit
"""

from dataclasses import dataclass, field
import json

import numpy as np

import config
from embeddings import encoder_un


def _jours(delta):
    """timedelta -> nombre de jours en flottant."""
    return delta.total_seconds() / 86400.0


@dataclass
class Souvenir:
    id: int
    contenu: str
    vecteur: np.ndarray
    date_creation: object             # datetime (temps SIMULÉ)
    date_dernier_acces: object
    date_derniere_confirmation: object
    date_derniere_erosion: object
    confiance: float
    compteur_confirmations: int = 0
    compteur_contradictions: int = 0
    statut: str = "actif"             # "actif" ou "archive"
    origine: str = ""                 # libellé libre (traçabilité / debug)

    def to_dict(self):
        """Version sérialisable (pour sauvegarde JSON inspectable)."""
        return {
            "id": self.id,
            "contenu": self.contenu,
            "date_creation": self.date_creation.strftime("%Y-%m-%d"),
            "date_dernier_acces": self.date_dernier_acces.strftime("%Y-%m-%d"),
            "date_derniere_confirmation": self.date_derniere_confirmation.strftime("%Y-%m-%d"),
            "confiance": round(float(self.confiance), 4),
            "compteur_confirmations": self.compteur_confirmations,
            "compteur_contradictions": self.compteur_contradictions,
            "statut": self.statut,
            "origine": self.origine,
        }


class Memoire:
    def __init__(self, horloge):
        self.horloge = horloge
        self.souvenirs = []          # liste de Souvenir
        self._prochain_id = 1
        self.cycles = 0              # nombre de questions traitées (pour le « sommeil »)
        self.historique_confiance = []  # [(date, id, confiance)] pour les courbes

    # ── AJOUT ────────────────────────────────────────────────────────────
    def ajouter(self, contenu, confiance=None, origine="", date=None, date_erosion=None):
        """Crée un nouveau souvenir. On n'écrase JAMAIS un ancien : on ajoute à côté.

        date          : date du fait (création / dernière confirmation) — sert de signal
                        de récence au juge. Peut être historique (ex. un fait daté de 2024).
        date_erosion  : à partir de quand l'érosion compte (par défaut : maintenant). On la
                        garde au présent même pour un fait historique : un souvenir ne peut
                        pas s'être érodé AVANT d'être entré en mémoire.
        """
        if confiance is None:
            confiance = config.CONFIANCE_DEPART
        if date is None:
            date = self.horloge.maintenant()
        if date_erosion is None:
            date_erosion = self.horloge.maintenant()
        s = Souvenir(
            id=self._prochain_id,
            contenu=contenu,
            vecteur=encoder_un(contenu),
            date_creation=date,
            date_dernier_acces=date,
            date_derniere_confirmation=date,
            date_derniere_erosion=date_erosion,
            confiance=confiance,
            origine=origine,
        )
        self.souvenirs.append(s)
        self._prochain_id += 1
        return s

    # ── RECHERCHE (similarité cosinus, top-k souvenirs actifs) ───────────
    def actifs(self):
        return [s for s in self.souvenirs if s.statut == "actif"]

    def rechercher(self, question, k=None):
        if k is None:
            k = config.TOP_K
        actifs = self.actifs()
        if not actifs:
            return []
        q = encoder_un(question)
        mat = np.stack([s.vecteur for s in actifs])   # (n, d), déjà normalisés
        scores = mat @ q                               # cosinus = produit scalaire
        ordre = np.argsort(-scores)[:k]
        return [(actifs[i], float(scores[i])) for i in ordre]

    # ── INJECTION : transforme les souvenirs en texte daté + confiance ───
    def texte_injection(self, trouves, avec_meta=True):
        """
        avec_meta=True  -> Config C (avec date + confiance) : « la mémoire qui trie »
        avec_meta=False -> Config B (RAG classique inerte)  : sans date ni confiance
        `trouves` = liste de (souvenir, score).
        """
        lignes = []
        for s, _ in trouves:
            if avec_meta:
                lignes.append(
                    f"[#{s.id} | confiance {s.confiance:.2f} | "
                    f"màj {s.date_derniere_confirmation.strftime('%Y-%m-%d')}] {s.contenu}"
                )
            else:
                lignes.append(f"- {s.contenu}")
        return "\n".join(lignes)

    def texte_injection_verbale(self, trouves):
        """
        Variante pour le RÉPONDEUR : on garde la date, mais la confiance n'est PAS donnée
        en chiffre (ce qui rendait le modèle timide). À la place, deux niveaux verbaux :
          - confiance correcte  → rien de spécial ;
          - confiance basse      → « dernière confirmation ancienne, à confirmer ».
        """
        lignes = []
        for s, _ in trouves:
            date = s.date_derniere_confirmation.strftime("%Y-%m-%d")
            if s.confiance < config.SEUIL_VERBAL:
                tag = f"[màj {date} — dernière confirmation ancienne, à confirmer]"
            else:
                tag = f"[màj {date}]"
            lignes.append(f"{tag} {s.contenu}")
        return "\n".join(lignes)

    # ── MÉCANISMES SURPRISE / RENFORCEMENT : appliquer un verdict du juge ─
    def appliquer_verdict(self, souvenir, verdict):
        now = self.horloge.maintenant()
        souvenir.date_dernier_acces = now

        if verdict == "CONFIRME":
            # RENFORCEMENT : la flamme est nourrie.
            souvenir.confiance = min(
                config.PLAFOND_CONFIANCE,
                souvenir.confiance + config.GAIN_CONFIRMATION,
            )
            souvenir.compteur_confirmations += 1
            souvenir.date_derniere_confirmation = now
            souvenir.date_derniere_erosion = now   # le compteur d'érosion repart de zéro

        elif verdict == "CONTREDIT":
            # SURPRISE : seul le faux se réécrit → la confiance chute.
            souvenir.confiance = max(0.0, souvenir.confiance - config.PERTE_CONTRADICTION)
            souvenir.compteur_contradictions += 1

        elif verdict == "INCERTAIN":
            if config.MALUS_INCERTAIN:
                souvenir.confiance = max(0.0, souvenir.confiance - config.MALUS_INCERTAIN)

        # NON_UTILISE : on ne touche qu'à date_dernier_acces (déjà fait ci-dessus).

    # ── MÉCANISME PÉREMPTION : érosion temporelle ───────────────────────
    def eroder(self):
        """
        Chaque souvenir actif perd de la confiance selon le temps écoulé depuis
        sa dernière confirmation (décroissance exponentielle, demi-vie paramétrable).
        La simple consultation ne réinitialise PAS l'érosion : seule la confirmation
        nourrit la flamme.
        """
        now = self.horloge.maintenant()
        for s in self.actifs():
            d = _jours(now - s.date_derniere_erosion)
            if d > 0:
                s.confiance *= 0.5 ** (d / config.DEMI_VIE_JOURS)
                s.date_derniere_erosion = now

    # ── MÉCANISME CONSOLIDATION : le « sommeil » ────────────────────────
    def consolider(self):
        """
        Toutes les N interactions :
          1. fusion des doublons (similarité > SEUIL_FUSION) : on garde le plus
             confiant/récent, on archive l'autre ;
          2. archivage des souvenirs trop faibles (confiance < SEUIL_ARCHIVAGE).
        Retourne un petit rapport.
        """
        rapport = {"fusions": [], "archivages_faibles": []}
        actifs = self.actifs()

        # 1) Fusion des doublons
        for i in range(len(actifs)):
            a = actifs[i]
            if a.statut != "actif":
                continue
            for j in range(i + 1, len(actifs)):
                b = actifs[j]
                if b.statut != "actif":
                    continue
                sim = float(a.vecteur @ b.vecteur)
                if sim > config.SEUIL_FUSION:
                    # garder le plus confiant ; à égalité, le plus récemment confirmé
                    garde, perd = (a, b)
                    if (b.confiance, b.date_derniere_confirmation) > (
                        a.confiance, a.date_derniere_confirmation
                    ):
                        garde, perd = (b, a)
                    perd.statut = "archive"
                    rapport["fusions"].append(
                        {"garde": garde.id, "archive": perd.id, "similarite": round(sim, 3)}
                    )

        # 2) Archivage des trop faibles
        for s in self.actifs():
            if s.confiance < config.SEUIL_ARCHIVAGE:
                s.statut = "archive"
                rapport["archivages_faibles"].append({"id": s.id, "confiance": round(s.confiance, 3)})

        return rapport

    # ── Journalisation des confiances (pour les courbes de l'étape 2) ────
    def enregistrer_confiances(self):
        now = self.horloge.maintenant()
        for s in self.souvenirs:
            self.historique_confiance.append(
                (now.strftime("%Y-%m-%d"), s.id, round(float(s.confiance), 4))
            )

    # ── Sauvegarde inspectable ───────────────────────────────────────────
    def sauvegarder(self, chemin):
        data = [s.to_dict() for s in self.souvenirs]
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
