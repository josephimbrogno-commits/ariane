# -*- coding: utf-8 -*-
"""
memoire/coeur/grammaire.py — GRAMMAIRE DE COMPOSITION DE CHAÎNES (chantier NOYAU 2B).

Discipline l'inférence par marche de graphe (cf. sonde 1A, verdict GO). `marche_graphe`
RASSEMBLE le voisinage 2-sauts d'une graine : les faits composables tombent dans le même
contexte. Composer NAÏVEMENT toute paire de faits partageant un pivot produit une majorité
ÉCRASANTE de faux (collègues, beaux-frères, inter-entreprises : 66 faux pour 14 vrais sur le
banc 1A). Une TABLE BLANCHE curée à la main (paire de prédicats + rôle du pivot + prédicat de
sortie) PLUS un gate de compatibilité de type au pivot ramène le faux à 0 SANS perdre un vrai.

CE MODULE NE MODIFIE RIEN. Il LIT le graphe et émet des FAITS INFÉRÉS, toujours QUALIFIÉS
« inféré » (jamais présentés comme observés), traçables à leurs deux faits sources, et héritant
du statut épistémique LE PLUS FAIBLE de la chaîne (un maillon clos/disputé/dormant contamine).

Greffé sur le pipeline derrière l'interrupteur d'environnement NOYAU_GRAMMAIRE (défaut OFF).
N'importe QU'EN LECTURE depuis graphe.py / ontologie.py (jamais d'écriture, jamais de mutation).
"""

from dataclasses import dataclass, field

from .graphe import types_compatibles
from .ontologie import spec_predicat


# ════════════════════════════════════════════════════════════════════════════════════════════════
# 1. TABLE BLANCHE CURÉE — les SEULES paires de prédicats que l'on accepte de composer.
#
# Clé   : (predicat_1, role_pivot_dans_f1, predicat_2, role_pivot_dans_f2)
#         role ∈ {'s' (le pivot est SUJET du fait), 'o' (le pivot est OBJET-entité du fait)}.
#         La clé décrit une chaîne « tête-à-queue » : le pivot est l'entité PARTAGÉE par f1 et f2.
# Valeur: (predicat_sortie, sens)
#         sens ∈ {'f1->f2'} : le SUJET du fait composé est le bout libre de f1, l'OBJET est le
#         bout libre de f2. (Une seule orientation suffit : l'énumération essaie f1/f2 dans les
#         deux ordres, donc l'inverse d'une règle se déduit en relisant la chaîne à l'envers.)
#
# JUSTIFICATION RÈGLE PAR RÈGLE — chaque règle doit être UNIVERSELLEMENT valide (précision d'abord ;
# dans le doute, on n'inscrit PAS : un faux composé est pire qu'un vrai manqué).
# ════════════════════════════════════════════════════════════════════════════════════════════════
GRAMMAIRE = {
    # ── PARENTÉ : grand-parent = parent du parent ────────────────────────────────────────────────
    # parent_de(X → PIVOT) ∘ parent_de(PIVOT → Z)  ⇒  grand_parent(X → Z).
    # Universel : si X est parent de PIVOT et PIVOT parent de Z, alors X est grand-parent de Z.
    # Pivot = personne des deux côtés (type_objet(parent_de)=personne == type_sujet(parent_de)).
    # Les PIÈGES type-compatibles que cette règle EXCLUT par construction : parent_de ∘ marie_a
    # (le conjoint de l'enfant n'est pas un petit-enfant), parent_de ∘ frere_de (le frère de
    # l'enfant — donc l'autre enfant — n'est pas un petit-enfant mais un enfant).
    ("parent_de", "o", "parent_de", "s"): ("grand_parent", "f1->f2"),

    # ── EMPLOI : patron = le dirigeant de mon employeur ──────────────────────────────────────────
    # travaille_pour(P → ORG) ∘ pdg_de(ORG → B)  ⇒  a_pour_patron(P → B).
    # Universel : si P travaille pour ORG et B dirige ORG, le patron de P est B.
    # Pivot = organisation (type_objet(travaille_pour)=organisation == type_sujet(pdg_de)).
    # PIÈGES EXCLUS : travaille_pour ∘ travaille_pour (deux COLLÈGUES — type-compatibles au pivot
    # ORG, mais aucune relation hiérarchique) ; travaille_pour ∘ a_acquis / partenaire_de
    # (relations INTER-entreprises, type org→org, sans rapport avec le patron du salarié).
    # → c'est l'absence de ces paires dans la table, PAS le type, qui les tue : preuve que la
    #   table sémantique tranche là où la compat de type seule échoue.
    ("travaille_pour", "o", "pdg_de", "s"): ("a_pour_patron", "f1->f2"),

    # ── EMPLOI (variante de notation) : « dirige » est le synonyme canonique de « pdg_de » ───────
    # CANON_PREDICATS (ontologie) rabat pdg_de → dirige (même signature org→personne). Selon la
    # source, le graphe peut porter l'une ou l'autre forme ; on inscrit donc la variante « dirige »
    # pour que la règle patron tienne quelle que soit la forme stockée. Même garantie, même pivot.
    # (Ne se déclenche PAS sur le banc 1A, qui emploie pdg_de : règle de robustesse, faux=0 préservé.)
    ("travaille_pour", "o", "dirige", "s"): ("a_pour_patron", "f1->f2"),
}

# Gabarits de rendu des prédicats COMPOSÉS (absents de l'ontologie : ce sont des sorties d'inférence).
_GABARITS_INFERE = {
    "grand_parent":  ("{s} est grand-parent de {o}", "{s} était grand-parent de {o}"),
    "a_pour_patron": ("le patron de {s} est {o}",     "le patron de {s} était {o}"),
}

# ── ORDRE DE FAIBLESSE ÉPISTÉMIQUE (plus le rang est haut, plus le maillon est DÉFAVORABLE) ───────
# courant (sain) < dormant (estompé) < disputé (contesté) < clos (périmé). Le fait composé hérite
# du PIRE rang de ses deux sources : un seul maillon faible contamine toute la chaîne.
_RANG_STATUT = {"courant": 0, "dormant": 1, "disputé": 2, "dispute": 2, "clos": 3}


@dataclass
class FaitInfere:
    """Fait COMPOSÉ par la grammaire. JAMAIS un fait observé : `qualif` le clame toujours, et
    `inferé=True` est immuable. Traçable (`sources` = ids des deux faits-maillons)."""
    predicat: str
    sujet_id: int
    objet_id: int
    sujet: str
    objet: str
    statut: str                      # statut épistémique HÉRITÉ (le plus faible des deux maillons)
    certitude: float                 # min des certitudes des deux maillons
    valide_jusqua: object            # borne de clôture héritée (la plus précoce), sinon None
    sources: tuple                   # (id_f1, id_f2) — provenance vérifiable
    actif: bool                      # False si un maillon est clos (périmé) → exclu du contexte actif
    inferé: bool = field(default=True, init=False)   # marqueur DUR : ceci n'est pas observé

    @property
    def qualif(self):
        suff = {"clos": " (périmé)", "disputé": " (disputé)", "dispute": " (disputé)",
                "dormant": " (dormant)"}.get(self.statut, "")
        return "inféré" + suff

    def phrase(self):
        gab = _GABARITS_INFERE.get(self.predicat, ("{s} → {o}", "{s} → {o}"))
        temps = 1 if self.statut == "clos" else 0
        return gab[temps].format(s=self.sujet, o=self.objet)

    def rendu(self):
        """Ligne de contexte EXPLICITEMENT marquée inférée (jamais confondable avec un souvenir)."""
        return f"• [INFÉRÉ — {self.qualif}, composé de #{self.sources[0]}+#{self.sources[1]}] {self.phrase()}."


def _role(f, eid):
    """Rôle joué par l'entité eid dans le fait f : 's' (sujet), 'o' (objet-entité), sinon None."""
    if f.sujet_id == eid:
        return "s"
    if f.objet_id == eid:
        return "o"
    return None


def _bout_libre(f, eid):
    """L'autre bout de f (l'entité qui n'est pas le pivot eid)."""
    return f.objet_id if f.sujet_id == eid else f.sujet_id


def _type_pivot(predicat, role):
    """Type joué par le pivot dans f : type_sujet si role='s', type_objet si role='o'."""
    spec = spec_predicat(predicat)
    return spec["type_sujet"] if role == "s" else spec["type_objet"]


def _enchainable(f):
    """(a) On n'enchaîne QUE des prédicats dont l'objet est une ENTITÉ résoluble (objet_entite=True)
    ET dont l'objet a bien été résolu (objet_id non nul). Un fait à objet-valeur ne se compose pas."""
    return spec_predicat(f.predicat).get("objet_entite", False) and f.objet_id is not None


def _statut_pire(f1, f2):
    """Statut épistémique le plus FAIBLE des deux maillons (récence/clôture/dispute la plus
    défavorable). Renvoie (statut, certitude_min, valide_jusqua_le_plus_precoce, actif)."""
    r1 = _RANG_STATUT.get(f1.statut, 0)
    r2 = _RANG_STATUT.get(f2.statut, 0)
    pire = f1.statut if r1 >= r2 else f2.statut
    cert = min(f1.certitude, f2.certitude)
    bornes = [b for b in (f1.valide_jusqua, f2.valide_jusqua) if b is not None]
    vj = min(bornes) if bornes else None
    actif = max(r1, r2) < _RANG_STATUT["clos"]      # un maillon clos (périmé) ⇒ chaîne inactive
    return pire, cert, vj, actif


def _incidences(faits):
    """eid -> [(fait, role)] : pour chaque entité-bout, les faits qui l'incident (avec son rôle)."""
    inc = {}
    for f in faits:
        for eid in (f.sujet_id, f.objet_id):
            if eid is not None:
                inc.setdefault(eid, []).append((f, _role(f, eid)))
    return inc


def composer(g, faits, maxf=6, inclure_inactifs=True):
    """Compose les chaînes 2-faits LICITES d'un pool (ce que `marche_graphe` rassemble).

    Pour chaque couple de faits partageant une entité-pivot, dans les DEUX ordres :
      (a) les DEUX prédicats sont `objet_entite=True` et l'objet est résolu (sinon pas de chaîne) ;
      (b) GATE DE TYPE : le pivot joue le MÊME type connu des deux côtés (`types_compatibles`) ;
      (c) la paire (p1, role1, p2, role2) figure dans la TABLE BLANCHE `GRAMMAIRE` — sinon REJET ;
      (d) on émet un `FaitInfere` MARQUÉ inféré (jamais observé) ;
      (e) il HÉRITE du statut épistémique le plus FAIBLE de ses deux maillons (clos/disputé/dormant
          contamine ; un maillon périmé ⇒ chaîne `actif=False`) ;
      (f) on PLAFONNE le nombre de faits composés DISTINCTS émis à `maxf`.

    `inclure_inactifs` : si False, les chaînes périmées (un maillon clos) sont totalement écartées ;
    si True (défaut), elles sont émises mais marquées `actif=False` (traçabilité + honnêteté).
    Renvoie une liste de `FaitInfere` distincts (dédupliqués par (prédicat, sujet, objet)).
    """
    inc = _incidences(faits)
    vus, sortie = {}, []
    for eid, lst in inc.items():
        n = len(lst)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                f1, r1 = lst[i]
                f2, r2 = lst[j]
                if r1 is None or r2 is None:
                    continue
                if not (_enchainable(f1) and _enchainable(f2)):       # (a)
                    continue
                regle = GRAMMAIRE.get((f1.predicat, r1, f2.predicat, r2))   # (c) table blanche
                if regle is None:
                    continue
                t1, t2 = _type_pivot(f1.predicat, r1), _type_pivot(f2.predicat, r2)  # (b) gate type
                if t1 is None or t2 is None or not types_compatibles(t1, t2):
                    continue
                src, dst = _bout_libre(f1, eid), _bout_libre(f2, eid)
                if src is None or dst is None or src == dst or src == eid or dst == eid:
                    continue
                rel, _sens = regle
                cle = (rel, src, dst)
                if cle in vus:
                    continue
                statut, cert, vj, actif = _statut_pire(f1, f2)          # (e) héritage du plus faible
                if not actif and not inclure_inactifs:
                    continue
                fi = FaitInfere(predicat=rel, sujet_id=src, objet_id=dst,
                                sujet=g.nom_entite(src), objet=g.nom_entite(dst),
                                statut=statut, certitude=cert, valide_jusqua=vj,
                                sources=(f1.id, f2.id), actif=actif)
                vus[cle] = fi
                sortie.append(fi)
    # (f) PLAFOND : actifs d'abord, puis par certitude décroissante ; on coupe à maxf.
    sortie.sort(key=lambda x: (not x.actif, -x.certitude))
    return sortie[:maxf] if maxf is not None else sortie


def rendu_infere(inferes, actifs_seulement=True):
    """Bloc de contexte des faits inférés, chacun EXPLICITEMENT marqué. Par défaut on ne rend que
    les inférences ACTIVES (les périmées restent traçables mais hors du contexte présenté au LLM)."""
    lignes = [fi.rendu() for fi in inferes if fi.actif or not actifs_seulement]
    return "\n".join(lignes)
