# -*- coding: utf-8 -*-
"""
memoire/api.py — l'API publique : les gestes de la bibliothèque.

Registre CONTENU (nourrir la mémoire par le monde) : ecrire / lire / consolider.
Registre STRUCTURE (parcourir la toile, tisser des liens) : parcourir / lier / retoucher.
Inspection : inspecter.

Règle d'or : on LIT la toile librement ; on ne TISSE jamais un fil sans dire d'où il vient.
Le LLM et l'embedding sont INJECTÉS (bibliothèque agnostique du modèle).
"""

from datetime import datetime

from . import config
from .coeur.graphe import GrapheMemoire, parse_date
from .coeur.ontologie import PREDICATS
from .coeur import extraction, lecture


class Memoire:
    def __init__(self, llm, embed):
        """llm : objet avec .texte(prompt, systeme, temperature) et .json(prompt, systeme).
        embed : fonction texte -> vecteur numpy normalisé."""
        self.llm = llm
        self.embed = embed
        self.g = GrapheMemoire(embed)
        self.horloge = None        # date « maintenant » simulée optionnelle (sinon datetime.now())

    def _date(self, date):
        return parse_date(date) or self.horloge or datetime.now()

    def _hook_consolidation(self):
        try:                       # branché par le paquet d'options (étape 3) ; absent → cœur nu
            from .options import hook_consolidation
            return hook_consolidation
        except Exception:
            return None

    # ── REGISTRE CONTENU ─────────────────────────────────────────────────
    def ecrire(self, enonce, source_id, date=None):
        """Ingère un énoncé : extraction (LLM) → résolution → conflit/corroboration/clôture.
        Retourne un compte rendu auditable des faits touchés."""
        tri = extraction.extraire(self.llm, enonce)
        if not tri:
            return {"erreur": "extraction échouée", "enonce": enonce}
        return self.g.ingerer(tri["sujet"], tri["predicat"], tri["objet"], source_id=source_id,
                              date_obs=self._date(date), date_validite=tri["date_validite"])

    def ecrire_triplet(self, sujet, predicat, objet, source_id, date=None, validite=None):
        """Ingère un triplet déjà structuré (sans LLM). Utile aux tests et au geste `lier`."""
        return self.g.ingerer(sujet, predicat, objet, source_id=source_id,
                              date_obs=self._date(date), date_validite=validite)

    def lire(self, question, date=None):
        """Entrée vectorielle (+ reconnaissance par nœud nommé) + marche de graphe ; rendu verbal."""
        return lecture.lire(self.g, self.llm, question, self._date(date))

    def consolider(self, date=None):
        """Le « sommeil » : érosions, dormance, fusion, promotion noyau (+ options branchées)."""
        return self.g.consolider(self._date(date), avant_dormance=self._hook_consolidation())

    # ── REGISTRE STRUCTURE ───────────────────────────────────────────────
    # Règle d'or : `parcourir` LIT la toile librement (aucune croyance engagée) ;
    # `lier` et `retoucher` TISSENT, donc passent TOUJOURS par un fait sourcé via le pipeline
    # normal (plafond du menteur, conflit, statut). Pas de porte dérobée.

    def parcourir(self, entite, profondeur=1):
        """LECTURE LIBRE de la toile : voisinage, degrés, statuts des liens. N'engage AUCUNE
        croyance, ne crée aucun fait. C'est la moitié « on lit librement » de la règle d'or."""
        e = self.g.trouver_entite(entite)
        if not e:
            return None

        def liens_de(eid):
            out = []
            for f in self.g.faits.values():
                if f.sujet_id == eid:
                    autre = self.g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet
                    out.append({"fait_id": f.id, "sens": "→", "predicat": f.predicat,
                                "vers": autre, "vers_id": f.objet_id, "statut": f.statut})
                elif f.objet_id == eid:
                    out.append({"fait_id": f.id, "sens": "←", "predicat": f.predicat,
                                "vers": self.g.nom_entite(f.sujet_id), "vers_id": f.sujet_id,
                                "statut": f.statut})
            return out

        liens = liens_de(e.id)
        voisins_ids = {l["vers_id"] for l in liens if l["vers_id"] is not None}
        res = {"entite": e.nom, "type": e.type, "importance": round(e.importance, 3),
               "degre": len(voisins_ids), "liens": liens}
        if profondeur >= 2:
            res["voisinage"] = {self.g.nom_entite(vid): liens_de(vid) for vid in voisins_ids}
        return res

    def lier(self, entite_a, relation, entite_b, source_id=None, date=None, validite=None):
        """TISSE un lien — mais jamais sans source. En dessous, fabrique un fait sourcé qui passe
        par le pipeline normal : il est donc soumis au plafond du menteur (0.60 mono-source), au
        conflit et au statut. `lier` N'EST PAS une porte dérobée vers une vérité non auditable."""
        if not source_id:
            raise ValueError("Règle d'or : on ne tisse jamais un fil sans dire d'où il vient "
                             "(source_id requis).")
        if relation not in PREDICATS:
            raise ValueError(f"relation inconnue : {relation!r}")
        return self.g.ingerer(entite_a, relation, entite_b, source_id=source_id,
                              date_obs=self._date(date), date_validite=validite)

    def retoucher(self, fait_id, action, source_id=None, date=None):
        """Retouche SOURCÉE d'un fait existant. action ∈ {clore, contester, corroborer}.
        Toute retouche est une affirmation sur le monde : elle exige une source."""
        if not source_id:
            raise ValueError("Règle d'or : retoucher exige une source "
                             "(toute affirmation sur le monde est sourcée).")
        f = self.g.faits.get(fait_id)
        if not f:
            raise ValueError(f"fait inconnu : {fait_id}")

        if action == "clore":
            # Clôturer, c'est affirmer « ce fait a cessé d'être vrai à telle date ».
            # Sourcé ET daté, comme toute affirmation. Le fait devient « était… jusqu'à [date] ».
            d = parse_date(date)
            if d is None:
                raise ValueError("Clôturer est une affirmation datée : une date de fin "
                                 "(date=…) est requise.")
            self.g.clore_fait(f, source_id, d)
            return {"action": "clôture", "fait": f.id, "statut": f.statut,
                    "valide_jusqua": f.valide_jusqua, "source": source_id}

        if action == "contester":
            self.g.contester_fait(f, source_id, self._date(date))
            return {"action": "contestation", "fait": f.id, "statut": f.statut,
                    "certitude": round(f.certitude, 3), "source": source_id}

        if action == "corroborer":
            # Une corroboration n'est qu'un nouveau rapport de la même valeur, par une autre source :
            # on repasse donc par `ingerer` (gain de Certitude si source indépendante, sinon rien).
            sujet = self.g.nom_entite(f.sujet_id)
            objet = self.g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet
            return self.g.ingerer(sujet, f.predicat, objet, source_id=source_id,
                                  date_obs=self._date(date))

        raise ValueError(f"action inconnue : {action!r} (clore / contester / corroborer)")

    # ── INSPECTION (transparence / débogage) ─────────────────────────────
    def inspecter(self, ref):
        """ref = id de fait (int) → état complet d'un fait ; nom d'entité (str) → ses faits."""
        if isinstance(ref, int):
            f = self.g.faits.get(ref)
            if not f:
                return None
            return {
                "id": f.id, "enonce": f.texte_source, "statut": f.statut,
                "force": round(f.force, 3), "certitude": round(f.certitude, 3),
                "importance": round(f.importance, 3), "noyau": f.noyau,
                "provenance": f.provenance, "n_sources": f.n_sources(),
                "valide_de": f.valide_de, "valide_jusqua": f.valide_jusqua,
                "derniere_confirmation": f.derniere_confirmation,
            }
        e = self.g.trouver_entite(ref)
        if not e:
            return None
        faits = [f for f in self.g.faits.values() if f.sujet_id == e.id or f.objet_id == e.id]
        return {"entite": e.nom, "type": e.type, "importance": round(e.importance, 3),
                "alias": e.alias, "faits": [self.g.fait_court(f) for f in faits]}
