# -*- coding: utf-8 -*-
"""
v2_modele.py — LA MÉMOIRE V2 : graphe daté à deux axes (Force / Certitude) + provenance.

Contient :
  - Entite, Fait        (les nœuds et arêtes datés)
  - GrapheMemoire       : résolution d'entités + procédure d'ÉCRITURE (mission V2, §2)

C'est ici que vivent désormais les conflits : FAIT contre FAIT, DATES contre DATES, sans
aucune réponse de modèle dans la boucle (leçon de l'échec du juge scindé : bon principe,
mauvais moment). Le juge ne contredit plus rien — la contradiction appartient à l'écriture.

ON NE SUPPRIME JAMAIS : un fait remplacé est CLOS (reste vrai comme histoire), un fait faible
devient DORMANT (toujours navigable par le graphe).
"""

import unicodedata
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

import config
from embeddings import encoder_un
from v2_ontologie import PREDICATS, demivie_certitude, phrase as phrase_fait

_TITRES = {"m", "mme", "mlle", "dr", "pr", "le", "la", "les", "l",
           "entreprise", "ville", "societe", "monsieur", "madame"}


def _norm(txt):
    txt = unicodedata.normalize("NFD", str(txt).lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return "".join(c if c.isalnum() or c.isspace() else " " for c in txt)


def norm_nom(nom):
    """Normalise un nom d'entité : minuscule, sans accents, sans titres."""
    mots = [m for m in _norm(nom).split() if m and m not in _TITRES]
    return " ".join(mots)


def norm_valeur(v):
    return " ".join(_norm(v).split())


def parse_date(s):
    if isinstance(s, datetime):
        return s
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@dataclass
class Entite:
    id: int
    nom: str
    alias: list
    embedding: object
    date_creation: object
    type: object = None          # personne / organisation / lieu / objet / valeur (V3 : bonus catégorie)
    importance: float = 0.0      # V3 : importance structurelle [0,1] (recalculée au sommeil)


@dataclass
class Fait:
    id: int
    sujet_id: int
    predicat: str
    objet: str
    objet_id: object              # id entité si objet_entite, sinon None
    texte_source: str
    embedding: object
    force: float
    certitude: float
    provenance: list              # [{"source_id","date","type"}]
    valide_de: object
    valide_jusqua: object         # None = courant
    date_creation: object
    dernier_acces: object
    derniere_confirmation: object
    derniere_contradiction: object
    statut: str                   # courant / clos / disputé / dormant
    statut_avant_dormance: object = None
    compteur_acces: int = 0       # nb d'accès UTILES (pour la promotion noyau)
    noyau: bool = False           # étage lent : demi-vies doublées
    importance: float = 0.0       # V3 : importance structurelle du fait [0,1]

    def n_sources(self):
        return len({p["source_id"] for p in self.provenance})

    def cle_objet(self):
        return self.objet_id if self.objet_id is not None else norm_valeur(self.objet)


class GrapheMemoire:
    def __init__(self):
        self.entites = {}
        self.faits = {}
        self._eid = 0
        self._fid = 0
        self.journal_resolution = []   # résolutions ambiguës (audit)

    # ── RÉSOLUTION D'ENTITÉS ─────────────────────────────────────────────
    def resoudre(self, nom, date):
        cible = norm_nom(nom)
        # 1) correspondance exacte nom / alias (après normalisation)
        for e in self.entites.values():
            noms = [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]
            if cible in noms:
                return e, "exact"
        # 2) sous-ensemble de tokens (« Nexora Corp » ⊇ « Nexora »)
        tok = set(cible.split())
        for e in self.entites.values():
            for n in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
                tn = set(n.split())
                if tn and tok and (tn <= tok or tok <= tn):
                    if nom not in e.alias and norm_nom(nom) != norm_nom(e.nom):
                        e.alias.append(nom)
                    return e, "alias/tokens"
        # 3) embedding
        v = encoder_un(nom)
        best, score = None, -1.0
        for e in self.entites.values():
            s = float(v @ e.embedding)
            if s > score:
                score, best = s, e
        if best is not None and score >= config.V2_RESOL_SEUIL:
            if nom not in best.alias:
                best.alias.append(nom)
            return best, f"embedding {score:.2f}"
        if best is not None and score >= config.V2_RESOL_AMBIGU_BAS:
            self.journal_resolution.append(
                {"nom": nom, "proche": best.nom, "score": round(score, 3),
                 "decision": "créée comme NOUVELLE (à auditer)"})
        # 4) création
        self._eid += 1
        e = Entite(self._eid, nom, [], v, date)
        self.entites[e.id] = e
        return e, "création"

    def trouver_entite(self, nom):
        """Recherche SANS création (pour l'audit / la décomposition d'erreurs)."""
        cible = norm_nom(nom)
        for e in self.entites.values():
            if cible in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
                return e
        return None

    # ── création d'un fait ───────────────────────────────────────────────
    def _creer_fait(self, sujet_id, predicat, objet, objet_id, texte, source_id,
                    date_obs, valide_de, statut):
        self._fid += 1
        f = Fait(
            id=self._fid, sujet_id=sujet_id, predicat=predicat, objet=objet, objet_id=objet_id,
            texte_source=texte, embedding=encoder_un(texte),
            force=config.V2_FORCE_INIT, certitude=config.V2_CERT_INIT_1SOURCE,
            provenance=[{"source_id": source_id, "date": date_obs, "type": "rapport"}],
            valide_de=valide_de, valide_jusqua=None, date_creation=date_obs,
            dernier_acces=date_obs, derniere_confirmation=date_obs,
            derniere_contradiction=None, statut=statut,
        )
        self._plafond_menteur(f)
        self.faits[f.id] = f
        return f

    def _plafond_menteur(self, f):
        """1 seule source → Certitude plafonnée à 0.60 (règle du menteur, §1.4)."""
        if f.n_sources() < 2:
            f.certitude = min(f.certitude, config.V2_CERT_PLAFOND_MENTEUR)

    def faits_de(self, sujet_id, predicat):
        return [f for f in self.faits.values()
                if f.sujet_id == sujet_id and f.predicat == predicat]

    # ── PROCÉDURE D'ÉCRITURE (§2.3) ──────────────────────────────────────
    def ingerer(self, sujet, predicat, objet, source_id, date_obs, date_validite=None):
        spec = PREDICATS[predicat]
        sujet_e, _ = self.resoudre(sujet, date_obs)
        objet_id = None
        objet_aff = objet
        if spec["objet_entite"]:
            objet_e, _ = self.resoudre(objet, date_obs)
            objet_id, objet_aff = objet_e.id, objet_e.nom

        cle_new = objet_id if objet_id is not None else norm_valeur(objet_aff)
        existants = self.faits_de(sujet_e.id, predicat)
        memes = [f for f in existants if f.cle_objet() == cle_new]
        valide_exp = parse_date(date_validite)
        valide_de = valide_exp or date_obs
        texte = phrase_fait(predicat, sujet_e.nom, objet_aff, "present")

        # (a) MÊME VALEUR → corroboration / répétition
        if memes:
            f = memes[0]
            srcs = {p["source_id"] for p in f.provenance}
            if source_id not in srcs:                       # corroboration INDÉPENDANTE
                f.certitude = min(config.V2_CERT_PLAFOND, f.certitude + config.V2_CERT_GAIN_CORRO)
                f.provenance.append({"source_id": source_id, "date": date_obs, "type": "rapport"})
                f.derniere_confirmation = date_obs
                self._plafond_menteur(f)
                action = "CORROBORATION indépendante (Certitude ↑)"
                # une vérité disputée qui redevient dominante repasse courant
                if f.statut == "disputé" and f.certitude >= 0.6 and f.n_sources() >= 2:
                    f.statut = "courant"
                    action += " → redevient COURANT"
            else:                                            # même source : pas une preuve
                f.force = min(config.V2_FORCE_PLAFOND, f.force + config.V2_FORCE_GAIN_ACCES)
                f.derniere_confirmation = date_obs
                action = "RÉPÉTITION même source (Certitude INCHANGÉE — anti-rumeur)"
            return {"action": action, "touches": [f], "sujet": sujet_e}

        # (c) prédicat MULTI-VALUÉ → simple ajout
        if not spec["fonctionnel"]:
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "courant")
            return {"action": "AJOUT (prédicat multi-valué, pas un conflit)",
                    "touches": [f], "sujet": sujet_e}

        # (b) prédicat FONCTIONNEL, valeur différente → CONFLIT
        courants = [f for f in existants if f.statut in ("courant", "disputé")]
        en_place = max(courants, key=lambda x: x.valide_de) if courants else None

        if en_place is None:
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "courant")
            return {"action": "CRÉATION (aucune valeur courante)", "touches": [f], "sujet": sujet_e}

        ep_srcs = {p["source_id"] for p in en_place.provenance}
        indep = source_id not in ep_srcs
        ep_corrobore = en_place.certitude >= 0.6 and len(ep_srcs) >= 2
        plus_recent = (valide_exp is not None) and (valide_exp > en_place.valide_de)

        if plus_recent and (indep or en_place.certitude < 0.6):
            # CLÔTURE : l'ancien reste VRAI comme histoire
            en_place.valide_jusqua = valide_de
            en_place.statut = "clos"
            en_place.derniere_contradiction = date_obs
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "courant")
            return {"action": f"CONFLIT → CLÔTURE de #{en_place.id} (clos), nouveau COURANT",
                    "touches": [en_place, f], "sujet": sujet_e}

        if ep_corrobore:
            # la vérité corroborée RÉSISTE au menteur à source unique
            en_place.statut = "disputé"
            en_place.certitude = max(0.0, en_place.certitude - config.V2_CERT_MALUS_DISPUTE)
            en_place.derniere_contradiction = date_obs
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "disputé")
            return {"action": "CONFLIT → DISPUTÉ (vérité corroborée résiste à la source unique)",
                    "touches": [en_place, f], "sujet": sujet_e}

        # ni clôture nette ni vérité à protéger → mise en concurrence prudente
        en_place.statut = "disputé"
        en_place.derniere_contradiction = date_obs
        f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                              source_id, date_obs, valide_de, "disputé")
        return {"action": "CONFLIT → DISPUTÉ (récence non établie)",
                "touches": [en_place, f], "sujet": sujet_e}

    # ── décroissances (érosion à deux axes) + accès/réveil ───────────────
    def _decroitre(self, date):
        """Force décroît depuis le dernier ACCÈS ; Certitude depuis la dernière CONFIRMATION
        (vitesse = volatilité ; immuable = jamais). Pour un noyau, les deux demi-vies sont doublées."""
        for f in self.faits.values():
            fac = config.V2_NOYAU_FACTEUR if f.noyau else 1.0
            dj = (date - f.dernier_acces).total_seconds() / 86400.0
            if dj > 0:
                f.force *= 0.5 ** (dj / (config.V2_FORCE_DEMIVIE * fac))
            dv = demivie_certitude(f.predicat)
            if dv is not None:
                dc = (date - f.derniere_confirmation).total_seconds() / 86400.0
                if dc > 0:
                    f.certitude *= 0.5 ** (dc / (dv * fac))
                self._plafond_menteur(f)

    def _protege_de_dormance(self, f):
        """Politique BIDIMENSIONNELLE : un fait bien attesté par le monde (≥ N sources) ou
        promu noyau ne dort jamais, MÊME à Force basse (la Certitude ne touche pas la Force,
        mais la décision de dormance lit les deux axes)."""
        return f.noyau or f.n_sources() >= config.V2_DORMANCE_SOURCES_PROTEGE

    def _seuil_dormance(self, f):
        """V3 : seuil MODULÉ par l'importance. Un fait capital ne s'endort quasiment jamais.
        seuil = base × (1 − β·importance). importance 0 → base (comportement V2)."""
        return config.V2_FORCE_SEUIL_DORMANT * (1.0 - config.IMP_BETA * f.importance)

    def _appliquer_dormance(self):
        for f in self.faits.values():
            if (f.force < self._seuil_dormance(f) and f.statut != "dormant"
                    and not self._protege_de_dormance(f)):
                f.statut_avant_dormance = f.statut
                f.statut = "dormant"

    def appliquer_decroissances(self, date):
        self._decroitre(date)
        self._appliquer_dormance()

    def recalculer_dormance(self, beta=None):
        """V3 / ablation : réveille tous les dormants puis ré-applique la dormance avec un β donné
        (β=0 → comportement V2 ; β=0.9 → importance protège). Ne touche ni Force ni Certitude."""
        for f in self.faits.values():
            if f.statut == "dormant":
                f.statut = f.statut_avant_dormance or "courant"
                f.statut_avant_dormance = None
        if beta is None:
            self._appliquer_dormance()
        else:
            anc = config.IMP_BETA
            config.IMP_BETA = beta
            try:
                self._appliquer_dormance()
            finally:
                config.IMP_BETA = anc

    def acceder(self, f, date):
        """Un accès nourrit la FORCE, compte pour la promotion, et peut RÉVEILLER un dormant.
        La Certitude n'est JAMAIS touchée par un accès (l'accès n'est pas une preuve)."""
        f.dernier_acces = date
        f.force = min(config.V2_FORCE_PLAFOND, f.force + config.V2_FORCE_GAIN_ACCES)
        f.compteur_acces += 1
        reveille = False
        if f.statut == "dormant" and f.force >= config.V2_FORCE_SEUIL_DORMANT:
            f.statut = f.statut_avant_dormance or "courant"
            f.statut_avant_dormance = None
            reveille = True
        return reveille

    def appliquer_plancher_certitude(self):
        """Fix menteur (étape 5) : un fait corroboré (≥2 sources) ne descend pas sous un plancher
        de Certitude → une vérité corroborée ancienne reste plus certaine qu'un mensonge récent à
        source unique. Reste < 0.6 pour ne pas casser le cas Dupont (réserve)."""
        for f in self.faits.values():
            if f.n_sources() >= 2:
                f.certitude = max(f.certitude, config.V2_CERT_PLANCHER_CORROBORE)

    # ── SOMMEIL (consolidation périodique, §4) ───────────────────────────
    def promouvoir(self):
        """≥ N sources indépendantes ET ≥ N accès utiles → statut NOYAU (demi-vies doublées)."""
        promus = []
        for f in self.faits.values():
            if (not f.noyau and f.n_sources() >= config.V2_NOYAU_SOURCES
                    and f.compteur_acces >= config.V2_NOYAU_ACCES):
                f.noyau = True
                promus.append(f.id)
        return promus

    def fusionner_entites(self):
        """Fusion des entités doublonnes (similarité > seuil) — filet de sécurité du sommeil.
        Les faits du doublon sont recâblés vers l'entité gardée. Journalisé."""
        fusions = []
        ids = list(self.entites)
        supprimees = set()
        for i in range(len(ids)):
            if ids[i] in supprimees:
                continue
            for j in range(i + 1, len(ids)):
                if ids[j] in supprimees:
                    continue
                e1, e2 = self.entites[ids[i]], self.entites[ids[j]]
                if float(e1.embedding @ e2.embedding) > config.V2_FUSION_SEUIL:
                    garde, perd = e1, e2
                    for f in self.faits.values():
                        if f.sujet_id == perd.id:
                            f.sujet_id = garde.id
                        if f.objet_id == perd.id:
                            f.objet_id = garde.id
                    if perd.nom not in garde.alias:
                        garde.alias.append(perd.nom)
                    supprimees.add(perd.id)
                    fusions.append({"garde": garde.id, "perd": perd.id})
        for pid in supprimees:
            del self.entites[pid]
        return fusions

    def sommeil(self, date):
        """Toutes les N interactions : décroissances → promotion → fusion → IMPORTANCE → dormance."""
        self._decroitre(date)
        promus = self.promouvoir()              # promu AVANT la dormance → protégé
        fusions = self.fusionner_entites()
        try:                                    # V3 : recalcul de l'importance (photo stable)
            import v3_importance
            v3_importance.calculer(self)
        except Exception:
            pass
        self._appliquer_dormance()
        dormis = [f.id for f in self.faits.values() if f.statut == "dormant"]
        return {"promus": promus, "fusions": fusions, "dormis": dormis}

    # ── affichage ────────────────────────────────────────────────────────

    # ── affichage ────────────────────────────────────────────────────────
    def nom_entite(self, eid):
        return self.entites[eid].nom if eid in self.entites else "?"

    def fait_court(self, f):
        vol = PREDICATS[f.predicat]["volatilite"]
        de = f.valide_de.strftime("%Y-%m") if f.valide_de else "?"
        jus = f.valide_jusqua.strftime("%Y-%m") if f.valide_jusqua else "…"
        noy = " ★noyau" if f.noyau else ""
        return (f"#{f.id} {f.predicat}({self.nom_entite(f.sujet_id)})={f.objet} "
                f"| F={f.force:.2f} C={f.certitude:.2f} [{f.statut}]{noy} "
                f"| {f.n_sources()} src · {f.compteur_acces} accès | {de}→{jus} | {vol}")
