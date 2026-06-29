# -*- coding: utf-8 -*-
"""
memoire/coeur/graphe.py — LE CŒUR : graphe daté à deux axes (Force / Certitude) + provenance.

Entite, Fait, GrapheMemoire. La contradiction vit à l'ÉCRITURE (fait contre fait, dates contre
dates ; aucun verdict de lecture ne clôt un fait). ON NE SUPPRIME JAMAIS : remplacé → CLOS,
faible → DORMANT (toujours navigable). L'embedding est INJECTÉ (bibliothèque agnostique du modèle).
"""

import os
import unicodedata
from dataclasses import dataclass
from datetime import datetime

from .. import config

# ── INDEX PAR ENTITÉ (CHANTIER 2A) ────────────────────────────────────────────
# Interrupteur par variable d'env UNIQUEMENT (pas de config.py — évite toute collision).
#   NOYAU_INDEX=1  → lectures de voisinage via index O(voisinage).
#   défaut (absent/≠"1") → chemin historique : scan linéaire O(toile), byte-pour-byte iso-résultat.
# Lu UNE fois au chargement du module. L'index est TOUJOURS maintenu à l'écriture (coût négligeable,
# invisible) ; seul le CHEMIN DE LECTURE est commuté, pour garantir que ON ne diverge jamais de OFF.
_USE_INDEX = os.environ.get("NOYAU_INDEX") == "1"
from .ontologie import PREDICATS, spec_predicat, demivie_certitude, DEMIVIE_CERTITUDE, phrase as phrase_fait

_TITRES = {"m", "mme", "mlle", "dr", "pr", "le", "la", "les", "l",
           "entreprise", "ville", "societe", "monsieur", "madame"}


def _norm(txt):
    txt = unicodedata.normalize("NFD", str(txt).lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return "".join(c if c.isalnum() or c.isspace() else " " for c in txt)


def norm_nom(nom):
    toks = [m for m in _norm(nom).split() if m]
    # Retirer les TITRES seulement EN TÊTE (« M. Vasseur » → « vasseur », « Le Louvre » → « louvre »),
    # mais GARDER une initiale MÉDIANE : « William M. Calder » garde « m » → distinct de « William Calder »
    # (grand-père ≠ petit-fils homonymes). Sans ça, « M. » médian est pris pour le titre « Monsieur ».
    while toks and toks[0] in _TITRES:
        toks.pop(0)
    toks = toks or [m for m in _norm(nom).split() if m]   # secours : un nom 100% titres reste lui-même
    # ÉTAPE 2 (acronymes) : fusionner les suites de LETTRES UNIQUES issues de la ponctuation,
    # pour que « U.S.A. » (→ « u s a ») et « USA » (→ « usa ») se réduisent à la MÊME chaîne →
    # fusion par ÉGALITÉ DE TEXTE, hors embedding. (« Jean Pierre » : pas de lettres uniques, intact.)
    fused, buf = [], []
    for t in toks:
        if len(t) == 1:
            buf.append(t)
        else:
            if buf:
                fused.append("".join(buf)); buf = []
            fused.append(t)
    if buf:
        fused.append("".join(buf))
    return " ".join(fused)


# ── HOMONYMES : un marqueur GÉNÉRATIONNEL distingue deux personnes au même patronyme ──────────
# « William Calder III » (petit-fils) ≠ « William M. Calder » (grand-père) ; « Henri IV » ≠ « Henri II » ;
# « … Jr » ≠ « … Sr ». On retient les ordinaux NON ambigus (pas i/v/x, qui sont aussi des initiales).
_ORDINAUX = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "jr", "sr", "junior", "senior"}


def _marqueur_gen(nom):
    return frozenset(t for t in norm_nom(nom).split() if t in _ORDINAUX)


def _homonyme_distinct(n1, n2):
    """True si n1 et n2 sont deux NOMS COMPLETS (≥2 tokens) portant des marqueurs générationnels
    DIFFÉRENTS (III vs aucun/II/Jr…) → personnes distinctes, ne pas fusionner. Un patronyme NU (1 token)
    reste fusionnable (abréviation : « Calder » → « …Calder III »). Précision d'abord."""
    if len(norm_nom(n1).split()) < 2 or len(norm_nom(n2).split()) < 2:
        return False
    return _marqueur_gen(n1) != _marqueur_gen(n2)


def norm_valeur(v):
    return " ".join(_norm(v).split())


# ── COMPATIBILITÉ DE TYPE pour la FUSION (anti-collision, mission 2) ──────────────────────────
# On compare par FAMILLE de haut niveau (les grains fins pays/ville → famille « lieu »). On ne BLOQUE
# la fusion que si les DEUX types ont une famille CONNUE et DIFFÉRENTE. Type inconnu/ambigu d'un côté
# → fallback : fusion AUTORISÉE (comportement actuel) — on ne fragmente jamais sur le doute.
_FAMILLE = {
    "personne": "personne", "individu": "personne", "scientifique": "personne", "artiste": "personne",
    "athlete": "personne", "joueur": "personne", "acteur": "personne", "ecrivain": "personne",
    "dirigeant": "personne", "homme": "personne", "femme": "personne", "auteur": "personne",
    "realisateur": "personne",
    "organisation": "organisation", "entreprise": "organisation", "societe": "organisation",
    "institution": "organisation", "club": "organisation", "parti": "organisation",
    "federation": "organisation", "comite": "organisation", "banque": "organisation",
    "lieu": "lieu", "ville": "lieu", "capitale": "lieu", "region": "lieu", "continent": "lieu",
    "fleuve": "lieu", "riviere": "lieu", "montagne": "lieu", "mer": "lieu", "ocean": "lieu",
    "desert": "lieu", "commune": "lieu", "pays": "lieu", "etat": "lieu",
    "oeuvre": "oeuvre", "film": "oeuvre", "livre": "oeuvre", "roman": "oeuvre", "album": "oeuvre",
    "tableau": "oeuvre", "chanson": "oeuvre", "produit": "oeuvre", "texte": "oeuvre",
    "date": "date", "annee": "date", "periode": "date",
    "distinction": "distinction", "recompense": "distinction", "medaille": "distinction",
    "trophee": "distinction", "titre": "distinction",
    "evenement": "evenement", "competition": "evenement", "match": "evenement", "tournoi": "evenement",
    "sommet": "evenement", "ceremonie": "evenement", "festival": "evenement",
    "substance": "substance", "molecule": "substance", "element": "substance", "gaz": "substance",
    "espece": "espece", "animal": "espece", "plante": "espece",
    "valeur": "valeur", "nombre": "valeur", "quantite": "valeur", "mesure": "valeur", "record": "valeur",
    # AMBIGUS volontairement non mappés (→ famille None → jamais utilisés pour BLOQUER) :
    #   nation (lieu|org) · equipe/groupe/selection (groupe|org) · prix (valeur|distinction)
}


def _famille(t):
    return _FAMILLE.get(str(t).strip().lower()) if t else None


def types_compatibles(t1, t2):
    """True = fusion AUTORISÉE. On ne BLOQUE que si les deux familles sont CONNUES et DIFFÉRENTES."""
    f1, f2 = _famille(t1), _famille(t2)
    if f1 is None or f2 is None:
        return True            # inconnu/ambigu d'un côté → fallback (comportement actuel)
    return f1 == f2


def _malus_brievete(nom1, nom2):
    """Malus de fiabilité de l'embedding selon la BRIÈVETÉ du plus court libellé (sans espaces).
    Franc à 2 lettres, s'efface vite : un sigle court a un embedding peu discriminant."""
    L = min(len(norm_nom(nom1).replace(" ", "")), len(norm_nom(nom2).replace(" ", ""))) or 1
    return config.ACRONYME_MALUS_MAX * (config.ACRONYME_L_REF / max(L, config.ACRONYME_L_REF)) ** 2


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
    type: object = None
    importance: float = 0.0


@dataclass
class Fait:
    id: int
    sujet_id: int
    predicat: str
    objet: str
    objet_id: object
    texte_source: str
    embedding: object
    force: float
    certitude: float
    provenance: list
    valide_de: object
    valide_jusqua: object
    date_creation: object
    dernier_acces: object
    derniere_confirmation: object
    derniere_contradiction: object
    statut: str
    statut_avant_dormance: object = None
    compteur_acces: int = 0
    noyau: bool = False
    importance: float = 0.0

    def n_sources(self):
        # ne comptent que les AFFIRMATIONS du fait (type "rapport") ; les clôtures/contestations
        # sont tracées dans la provenance mais n'affirment pas le fait → pas comptées comme sources.
        return len({p["source_id"] for p in self.provenance if p.get("type", "rapport") == "rapport"})

    def cle_objet(self):
        return self.objet_id if self.objet_id is not None else norm_valeur(self.objet)


class GrapheMemoire:
    def __init__(self, embed):
        self.embed = embed                  # INJECTÉ : texte -> vecteur normalisé
        self.entites = {}
        self.faits = {}
        # ── INDEX PAR ENTITÉ (2A) : maintenus à CHAQUE écriture (insertion + réassignation de fusion).
        # Aucun fait n'est JAMAIS retiré de self.faits (« on ne supprime jamais » : clos/dormant restent),
        # donc il n'existe aucun point de suppression à intercepter. Invariant : _idx_n == len(self.faits).
        self._idx_sujet = {}                # sujet_id -> set(fait_id)
        self._idx_objet = {}                # objet_id -> set(fait_id)   (objet_id None → non indexé)
        self._idx_n = 0                     # nb de faits indexés par sujet (auto-contrôle de cohérence)
        self._eid = 0
        self._fid = 0
        self.journal_resolution = []
        self.journal_type_conflit = []      # SOCLE TYPE : un type différent arrive sur un nœud déjà typé
        self.journal_reunion = []           # RÉUNION : fragments réunis (garde/absorbe/score/voisins) — auditable
        self.volatilite_apprise = {}        # SUBCONSCIENT : par prédicat, ce qu'on a appris (cf. apprendre_volatilite)

    # ── RÉSOLUTION D'ENTITÉS ─────────────────────────────────────────────
    def _poser_type(self, e, type_attendu):
        """SOCLE TYPE (additif) : renseigne le type d'un nœud s'il manque ; si un type DIFFÉRENT
        arrive sur un nœud déjà typé → on JOURNALISE le désaccord, on n'écrase JAMAIS."""
        if not type_attendu:
            return
        if e.type is None:
            e.type = type_attendu
        elif e.type != type_attendu:
            if not hasattr(self, "journal_type_conflit"):
                self.journal_type_conflit = []
            self.journal_type_conflit.append(
                {"entite": e.nom, "type_garde": e.type, "type_recu": type_attendu})

    def resoudre(self, nom, date, type_attendu=None):
        cible = norm_nom(nom)
        for e in self.entites.values():
            if cible in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
                self._poser_type(e, type_attendu)
                return e, "exact"
        tok = set(cible.split())
        for e in self.entites.values():
            for n in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
                tn = set(n.split())
                if tn and tok and (tn <= tok or tok <= tn) and types_compatibles(e.type, type_attendu):
                    if nom not in e.alias and norm_nom(nom) != norm_nom(e.nom):
                        e.alias.append(nom)
                    self._poser_type(e, type_attendu)
                    return e, "alias/tokens"
        v = self.embed(nom)
        best, score = None, -1.0
        for e in self.entites.values():
            s = float(v @ e.embedding)
            if s > score:
                score, best = s, e
        if (best is not None and types_compatibles(best.type, type_attendu)
                and not _homonyme_distinct(nom, best.nom)           # HOMONYMES : grand-père ≠ petit-fils (III)
                and (score - _malus_brievete(nom, best.nom)) >= config.V2_RESOL_SEUIL):  # ÉTAPE 3 : sigles courts
            if nom not in best.alias:
                best.alias.append(nom)
            self._poser_type(best, type_attendu)
            return best, f"embedding {score:.2f}"
        if best is not None and score >= config.V2_RESOL_AMBIGU_BAS:
            self.journal_resolution.append(
                {"nom": nom, "proche": best.nom, "score": round(score, 3),
                 "decision": "créée comme NOUVELLE (à auditer)"})
        self._eid += 1
        e = Entite(self._eid, nom, [], v, date, type=type_attendu)   # le type voyage à la création
        self.entites[e.id] = e
        return e, "création"

    def trouver_entite(self, nom):
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
            texte_source=texte, embedding=self.embed(texte),
            force=config.V2_FORCE_INIT, certitude=config.V2_CERT_INIT_1SOURCE,
            provenance=[{"source_id": source_id, "date": date_obs, "type": "rapport"}],
            valide_de=valide_de, valide_jusqua=None, date_creation=date_obs,
            dernier_acces=date_obs, derniere_confirmation=date_obs,
            derniere_contradiction=None, statut=statut,
        )
        self._plafond_menteur(f)
        self.faits[f.id] = f
        self._idx_ajouter(f)
        return f

    # ── MAINTENANCE DE L'INDEX PAR ENTITÉ (2A) ───────────────────────────
    def _idx_ajouter(self, f):
        """Indexe un fait neuf. Appelé à CHAQUE insertion (toujours, flag indifférent)."""
        self._idx_sujet.setdefault(f.sujet_id, set()).add(f.id)
        if f.objet_id is not None:
            self._idx_objet.setdefault(f.objet_id, set()).add(f.id)
        self._idx_n += 1

    def _idx_deplacer_sujet(self, f, ancien, nouveau):
        s = self._idx_sujet.get(ancien)
        if s is not None:
            s.discard(f.id)
            if not s:
                del self._idx_sujet[ancien]
        self._idx_sujet.setdefault(nouveau, set()).add(f.id)

    def _idx_deplacer_objet(self, f, ancien, nouveau):
        if ancien is not None:
            s = self._idx_objet.get(ancien)
            if s is not None:
                s.discard(f.id)
                if not s:
                    del self._idx_objet[ancien]
        if nouveau is not None:
            self._idx_objet.setdefault(nouveau, set()).add(f.id)

    def reconstruire_index(self):
        """(Re)construit l'index depuis self.faits — pour un graphe CHARGÉ (faits insérés hors _creer_fait)."""
        self._idx_sujet, self._idx_objet, self._idx_n = {}, {}, 0
        for f in self.faits.values():
            self._idx_ajouter(f)

    def _idx_assurer(self):
        """Auto-guérison O(1) : reconstruit l'index si nécessaire, sinon no-op. Couvre deux cas de
        graphe CHARGÉ (réserve persistante = pickle, cf. connecteur/service.py) :
          • pickle ANTÉRIEUR à 2A → les attributs d'index manquent (unpickle n'appelle pas __init__) ;
          • faits insérés hors _creer_fait → invariant _idx_n == len(self.faits) rompu."""
        if not hasattr(self, "_idx_n"):
            self.reconstruire_index()
        elif self._idx_n != len(self.faits):
            self.reconstruire_index()

    def _reassigner_entite(self, ancien_id, nouveau_id):
        """Repointe TOUS les faits touchant `ancien_id` (en sujet ET/OU objet) vers `nouveau_id`.
        OFF : transformation historique, scan linéaire (byte-pour-byte le code d'origine de fusion/réunion).
        ON  : ne parcourt que le voisinage via l'index, et tient l'index à jour."""
        if _USE_INDEX:
            self._idx_assurer()
            for fid in list(self._idx_sujet.get(ancien_id, ())):
                f = self.faits[fid]
                f.sujet_id = nouveau_id
                self._idx_deplacer_sujet(f, ancien_id, nouveau_id)
            for fid in list(self._idx_objet.get(ancien_id, ())):
                f = self.faits[fid]
                f.objet_id = nouveau_id
                self._idx_deplacer_objet(f, ancien_id, nouveau_id)
        else:
            for f in self.faits.values():
                if f.sujet_id == ancien_id:
                    f.sujet_id = nouveau_id
                if f.objet_id == ancien_id:
                    f.objet_id = nouveau_id

    def _plafond_menteur(self, f):
        if f.n_sources() < 2:
            f.certitude = min(f.certitude, config.V2_CERT_PLAFOND_MENTEUR)

    def faits_de(self, sujet_id, predicat):
        if _USE_INDEX:
            self._idx_assurer()
            ids = self._idx_sujet.get(sujet_id)
            if not ids:
                return []
            faits = self.faits
            # sorted(ids) ⇒ ordre des fid croissants = ordre d'insertion = itération dict du chemin OFF.
            # Garantit l'iso-résultat NON SEULEMENT en ensemble mais en ORDRE (memes[0], max(...) inchangés).
            return [faits[i] for i in sorted(ids) if faits[i].predicat == predicat]
        return [f for f in self.faits.values()
                if f.sujet_id == sujet_id and f.predicat == predicat]

    def faits_voisins(self, eid):
        """VOISINAGE COMPLET d'une entité : tous les faits où `eid` est sujet OU objet (les deux sens).
        Primitive de lecture de toile (même balayage que api.parcourir.liens_de, hors périmètre 2A).
        OFF : scan O(toile). ON : union des index O(degré). Ordre fid croissant pour iso-résultat."""
        if _USE_INDEX:
            self._idx_assurer()
            ids = self._idx_sujet.get(eid, set()) | self._idx_objet.get(eid, set())
            return [self.faits[i] for i in sorted(ids)]
        return [f for f in self.faits.values()
                if f.sujet_id == eid or f.objet_id == eid]

    # ── PROCÉDURE D'ÉCRITURE ─────────────────────────────────────────────
    def ingerer(self, sujet, predicat, objet, source_id, date_obs, date_validite=None,
                type_sujet=None, type_objet=None):
        spec = spec_predicat(predicat)                           # verbe brut inconnu → DEFAULT_SPEC sûr
        sujet_e, _ = self.resoudre(sujet, date_obs, type_sujet)   # le type du greffier voyage au nœud
        objet_id, objet_aff = None, objet
        if spec["objet_entite"]:
            objet_e, _ = self.resoudre(objet, date_obs, type_objet)
            objet_id, objet_aff = objet_e.id, objet_e.nom
            if objet_id == sujet_e.id:        # AUTO-RÉFÉRENCE (sujet==objet) : non-sens (« X parent de X »),
                return {"action": "REJET (fait auto-référentiel)",  # symptôme d'une collision d'homonymes
                        "touches": [], "sujet": sujet_e}

        cle_new = objet_id if objet_id is not None else norm_valeur(objet_aff)
        existants = self.faits_de(sujet_e.id, predicat)
        memes = [f for f in existants if f.cle_objet() == cle_new]
        valide_exp = parse_date(date_validite)
        valide_de = valide_exp or date_obs
        texte = phrase_fait(predicat, sujet_e.nom, objet_aff, "present")

        if memes:  # MÊME VALEUR → corroboration / répétition
            f = memes[0]
            srcs = {p["source_id"] for p in f.provenance}
            if source_id not in srcs:
                f.certitude = min(config.V2_CERT_PLAFOND, f.certitude + config.V2_CERT_GAIN_CORRO)
                f.provenance.append({"source_id": source_id, "date": date_obs, "type": "rapport"})
                f.derniere_confirmation = date_obs
                self._plafond_menteur(f)
                action = "CORROBORATION indépendante (Certitude ↑)"
                if f.statut == "disputé" and f.certitude >= 0.6 and f.n_sources() >= 2:
                    f.statut = "courant"
                    action += " → redevient COURANT"
            else:
                f.force = min(config.V2_FORCE_PLAFOND, f.force + config.V2_FORCE_GAIN_ACCES)
                f.derniere_confirmation = date_obs
                action = "RÉPÉTITION même source (Certitude INCHANGÉE — anti-rumeur)"
            return {"action": action, "touches": [f], "sujet": sujet_e}

        if not spec["fonctionnel"]:  # MULTI-VALUÉ → ajout
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "courant")
            return {"action": "AJOUT (prédicat multi-valué, pas un conflit)",
                    "touches": [f], "sujet": sujet_e}

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
            en_place.valide_jusqua = valide_de
            en_place.statut = "clos"
            en_place.derniere_contradiction = date_obs
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "courant")
            return {"action": f"CONFLIT → CLÔTURE de #{en_place.id} (clos), nouveau COURANT",
                    "touches": [en_place, f], "sujet": sujet_e}

        if ep_corrobore:
            en_place.statut = "disputé"
            en_place.certitude = max(0.0, en_place.certitude - config.V2_CERT_MALUS_DISPUTE)
            en_place.derniere_contradiction = date_obs
            f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                                  source_id, date_obs, valide_de, "disputé")
            return {"action": "CONFLIT → DISPUTÉ (vérité corroborée résiste à la source unique)",
                    "touches": [en_place, f], "sujet": sujet_e}

        en_place.statut = "disputé"
        en_place.derniere_contradiction = date_obs
        f = self._creer_fait(sujet_e.id, predicat, objet_aff, objet_id, texte,
                              source_id, date_obs, valide_de, "disputé")
        return {"action": "CONFLIT → DISPUTÉ (récence non établie)",
                "touches": [en_place, f], "sujet": sujet_e}

    # ── décroissances + accès / réveil ───────────────────────────────────
    def _decroitre(self, date):
        for f in self.faits.values():
            fac = config.V2_NOYAU_FACTEUR if f.noyau else 1.0
            dj = (date - f.dernier_acces).total_seconds() / 86400.0
            if dj > 0:
                f.force *= 0.5 ** (dj / (config.V2_FORCE_DEMIVIE * fac))
            dv = self._demivie(f.predicat)
            if dv is not None:
                dc = (date - f.derniere_confirmation).total_seconds() / 86400.0
                if dc > 0:
                    f.certitude *= 0.5 ** (dc / (dv * fac))
                self._plafond_menteur(f)

    def _protege_de_dormance(self, f):
        return f.noyau or f.n_sources() >= config.V2_DORMANCE_SOURCES_PROTEGE

    def _seuil_dormance(self, f):
        # Modulé par l'importance SI l'option dormance-modulée est active (sinon importance=0 → base).
        beta = config.IMP_BETA if config.OPT_DORMANCE_MODULEE else 0.0
        return config.V2_FORCE_SEUIL_DORMANT * (1.0 - beta * f.importance)

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
        for f in self.faits.values():
            if f.statut == "dormant":
                f.statut = f.statut_avant_dormance or "courant"
                f.statut_avant_dormance = None
        if beta is None:
            self._appliquer_dormance()
        else:
            anc, anc_opt = config.IMP_BETA, config.OPT_DORMANCE_MODULEE
            config.IMP_BETA, config.OPT_DORMANCE_MODULEE = beta, True
            try:
                self._appliquer_dormance()
            finally:
                config.IMP_BETA, config.OPT_DORMANCE_MODULEE = anc, anc_opt

    def acceder(self, f, date):
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
        for f in self.faits.values():
            if f.n_sources() >= 2:
                f.certitude = max(f.certitude, config.V2_CERT_PLANCHER_CORROBORE)

    # ── RETOUCHE SOURCÉE (clôture / contestation) ───────────────────────
    def clore_fait(self, f, source_id, date_fin):
        """Une clôture est une AFFIRMATION SUR LE MONDE : sourcée et datée. Le fait devient
        « était… jusqu'à [date] ». La source de clôture est tracée (type cloture)."""
        f.valide_jusqua = date_fin
        f.statut = "clos"
        f.derniere_contradiction = date_fin
        f.provenance.append({"source_id": source_id, "date": date_fin, "type": "cloture"})
        return f

    def contester_fait(self, f, source_id, date):
        """Contestation sourcée : le fait passe disputé, sa Certitude baisse, la source tracée."""
        f.statut = "disputé"
        f.certitude = max(0.0, f.certitude - config.V2_CERT_MALUS_DISPUTE)
        f.derniere_contradiction = date
        f.provenance.append({"source_id": source_id, "date": date, "type": "contestation"})
        return f

    # ── SOMMEIL (consolidation) ──────────────────────────────────────────
    def promouvoir(self):
        promus = []
        for f in self.faits.values():
            if (not f.noyau and f.n_sources() >= config.V2_NOYAU_SOURCES
                    and f.compteur_acces >= config.V2_NOYAU_ACCES):
                f.noyau = True
                promus.append(f.id)
        return promus

    def fusionner_entites(self):
        fusions, ids, supprimees = [], list(self.entites), set()
        for i in range(len(ids)):
            if ids[i] in supprimees:
                continue
            for j in range(i + 1, len(ids)):
                if ids[j] in supprimees:
                    continue
                e1, e2 = self.entites[ids[i]], self.entites[ids[j]]
                if (float(e1.embedding @ e2.embedding) > config.V2_FUSION_SEUIL
                        and types_compatibles(e1.type, e2.type)):
                    self._reassigner_entite(e2.id, e1.id)
                    if e2.nom not in e1.alias:
                        e1.alias.append(e2.nom)
                    supprimees.add(e2.id)
                    fusions.append({"garde": e1.id, "perd": e2.id})
        for pid in supprimees:
            del self.entites[pid]
        return fusions

    def _barre_confirmee(self, fam, communs, df, score):
        """BARRE DE CONFIRMATION MODULÉE PAR LA FAMILLE (le score reste calculé pareil ; c'est le
        SEUIL qui dépend de la nature de l'identité). Organisation/objet/lieu : identité RELATIONNELLE
        → la structure partagée suffit (barre inchangée, déjà filtrée par score ≥ REUNION_SEUIL).
        Personne : identité FORTE et unique → un seul voisin partagé est une COÏNCIDENCE, pas une
        confirmation → exiger PLUSIEURS voisins rares (ou un score structurel très haut). Non binaire :
        un vrai doublon de personne, qui converge sur plusieurs voisins rares, fusionne encore."""
        if fam not in config.REUNION_FAMILLES_IDENTITE_FORTE:
            return True
        n_rares = sum(1 for nk in communs if 1.0 / df[nk] >= config.REUNION_RARE_MIN)
        return (n_rares >= config.REUNION_PERSONNE_MIN_VOISINS
                or score >= config.REUNION_SEUIL_PERSONNE_FORT)

    def reunir_fragments(self):
        """RÉUNION OPPORTUNISTE des fragments (MSFT/Microsoft). Déclenchée par la STRUCTURE pondérée
        par la rareté, sous GATE de même famille connue. Embedding en appoint (jamais déclencheur seul).
        Réunit e2 dans e1 si le score de voisins communs dépasse le seuil. Réversible (journal + alias)."""
        # voisins de chaque entité (l'autre bout de chaque fait) + df (en combien d'entités un voisin apparaît)
        vois = {eid: set() for eid in self.entites}
        for f in self.faits.values():
            nk = ("e", f.objet_id) if f.objet_id is not None else ("v", norm_valeur(f.objet))
            vois.setdefault(f.sujet_id, set()).add(nk)
            if f.objet_id is not None:
                vois.setdefault(f.objet_id, set()).add(("e", f.sujet_id))
        df = {}
        for s in vois.values():
            for nk in s:
                df[nk] = df.get(nk, 0) + 1

        ids, absorbes = list(self.entites), set()
        for i in range(len(ids)):
            if ids[i] in absorbes:
                continue
            e1 = self.entites[ids[i]]
            fam = _famille(e1.type)
            if fam is None:                          # GATE : famille connue requise (précision d'abord)
                continue
            for j in range(i + 1, len(ids)):
                if ids[j] in absorbes:
                    continue
                e2 = self.entites[ids[j]]
                if _famille(e2.type) != fam:          # GATE : MÊME famille connue, sinon jamais réunir
                    continue
                communs = (vois[e1.id] & vois[e2.id]) - {("e", e1.id), ("e", e2.id)}
                if not communs:                       # pas de pont structurel → réunion opportuniste : on s'abstient
                    continue
                score = sum(1.0 / df[nk] for nk in communs)             # rareté : voisin banal pèse peu
                score += config.REUNION_EMBED_BONUS * max(0.0, float(e1.embedding @ e2.embedding))
                if score >= config.REUNION_SEUIL and self._barre_confirmee(fam, communs, df, score):
                    self._reassigner_entite(e2.id, e1.id)
                    for nom in [e2.nom] + e2.alias:
                        if nom not in e1.alias and norm_nom(nom) != norm_nom(e1.nom):
                            e1.alias.append(nom)       # trace d'origine (réversibilité minimale)
                    self.journal_reunion.append(
                        {"garde": e1.nom, "absorbe": e2.nom, "famille": fam, "score": round(score, 3),
                         "voisins_decisifs": [nk for nk in communs if 1.0 / df[nk] >= 0.25]})
                    vois[e1.id] |= vois[e2.id]
                    absorbes.add(e2.id)
        for pid in absorbes:
            del self.entites[pid]
        return self.journal_reunion[-len(absorbes):] if absorbes else []

    # ── SUBCONSCIENT #1 : VOLATILITÉ APPRISE (motif distillé au-dessus des faits, sans les toucher) ──
    def apprendre_volatilite(self):
        """Apprend par prédicat la volatilité OBSERVÉE (taux de clôture datée = clos / occurrences ;
        disputés EXCLUS = signal pur) et la MÉLANGE au prior à la main, pondéré par l'évidence (nb d'obs).
        Ne modifie AUCUN fait — remplit self.volatilite_apprise. Sous le seuil de matière → confiance 0,
        on reste sur le prior (« supposition ») : on ne confond jamais « 0 observation » avec « stable »."""
        occ = {}
        for f in self.faits.values():
            if f.statut == "disputé":
                continue                                # signal PUR : seulement les faits réglés (clos/courant)
            a = occ.setdefault(f.predicat, [0, 0])
            a[0] += 1
            a[1] += (f.statut == "clos")
        appris = {}
        for p, (n_occ, n_clos) in occ.items():
            prior = spec_predicat(p).get("volatilite", "stable")
            prior_dv = DEMIVIE_CERTITUDE.get(prior)
            prior_dv_f = config.SUBCON_DV_IMMUABLE if prior_dv is None else prior_dv
            taux = n_clos / n_occ if n_occ else 0.0
            obs_dv = max(config.SUBCON_DV_PLANCHER,
                         config.SUBCON_DV_REF * (0.5 ** (taux / config.SUBCON_DV_DEMI_TAUX)))
            w = 0.0 if (n_occ < config.SUBCON_MIN_OCC or n_clos < config.SUBCON_MIN_CLOS) \
                else n_occ / (n_occ + config.SUBCON_K_CONF)
            melange = (1 - w) * prior_dv_f + w * obs_dv
            dv = None if melange >= config.SUBCON_DV_IMMUABLE * 0.5 else melange
            etiq = "appris" if w >= 0.6 else ("mixte" if w >= 0.15 else "supposition")
            appris[p] = {"prior": prior, "prior_dv": prior_dv, "n_occ": n_occ, "n_clos": n_clos,
                         "taux": round(taux, 3), "confiance": round(w, 2), "obs_dv": round(obs_dv, 1),
                         "dv": (round(dv, 1) if dv is not None else None), "etiquette": etiq}
        self.volatilite_apprise = appris
        return appris

    def _demivie(self, predicat):
        """Demi-vie de certitude EFFECTIVE : apprise (subconscient) si active ET assez de matière, sinon
        le prior à la main exact (→ iso-résultat quand l'option est OFF)."""
        if config.OPT_SUBCONSCIENT_VOLATILITE:
            a = self.volatilite_apprise.get(predicat)
            if a and a["confiance"] > 0:
                return a["dv"]
        return demivie_certitude(predicat)

    def dump_volatilite(self):
        """Vue LISIBLE de ce que le subconscient a appris — inspectable et contestable, jamais une boîte noire."""
        out = []
        for p, a in sorted(self.volatilite_apprise.items(), key=lambda x: -x[1]["n_clos"]):
            dvm = "immuable" if a["prior_dv"] is None else f"{a['prior_dv']:.0f}j"
            dve = "immuable" if a["dv"] is None else f"{a['dv']:.0f}j"
            out.append(f"{p:18} prior={a['prior']:>9}({dvm:>8}) taux={a['taux']:>5.0%} n_obs={a['n_occ']:>3} "
                       f"clos={a['n_clos']:>3} conf={a['confiance']:.2f} → demi-vie={dve:>8} [{a['etiquette']}]")
        return "\n".join(out)

    def consolider(self, date, avant_dormance=None):
        """Décroissances → promotion → fusion → [réunion fragments] → plancher → [hook] → dormance."""
        if config.OPT_SUBCONSCIENT_VOLATILITE:        # le subconscient distille AVANT la décroissance
            self.apprendre_volatilite()
        self._decroitre(date)
        promus = self.promouvoir()
        fusions = self.fusionner_entites()
        if config.OPT_REUNION_FRAGMENTS:
            self.reunir_fragments()
        self.appliquer_plancher_certitude()
        if avant_dormance is not None:        # hook options (importance, typologie) — injecté
            avant_dormance(self)
        self._appliquer_dormance()
        dormis = [f.id for f in self.faits.values() if f.statut == "dormant"]
        return {"promus": promus, "fusions": fusions, "dormis": dormis}

    # ── affichage ────────────────────────────────────────────────────────
    def nom_entite(self, eid):
        return self.entites[eid].nom if eid in self.entites else "?"

    def fait_court(self, f):
        vol = spec_predicat(f.predicat)["volatilite"]
        de = f.valide_de.strftime("%Y-%m") if f.valide_de else "?"
        jus = f.valide_jusqua.strftime("%Y-%m") if f.valide_jusqua else "…"
        noy = " ★noyau" if f.noyau else ""
        return (f"#{f.id} {f.predicat}({self.nom_entite(f.sujet_id)})={f.objet} "
                f"| F={f.force:.2f} C={f.certitude:.2f} [{f.statut}]{noy} "
                f"| {f.n_sources()} src · {f.compteur_acces} accès | {de}→{jus} | {vol}")
