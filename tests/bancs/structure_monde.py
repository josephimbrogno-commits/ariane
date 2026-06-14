# -*- coding: utf-8 -*-
"""
structure_monde.py — GÉNÉRATEUR du banc « typologie des liens par la structure ».

Question : peut-on deviner la NATURE d'un lien (DURABLE / ÉPHÉMÈRE) à partir de la SEULE structure
du graphe (degrés des extrémités, réciprocité, date unique), sans la déclarer à la main ?

Règle d'or (§0) : le générateur étiquette chaque lien par sa VRAIE nature AU MOMENT de le créer.
Cette étiquette est la vérité-terrain ; elle n'est JAMAIS donnée au prédicteur structurel.

Anti-circularité : on inclut des CAS-PIÈGES qui cassent la corrélation facile connectivité↔nature :
  P-A : DURABLE vers un nœud cul-de-sac (frère d'un proche isolé) — S1 dirait « faible » à tort.
  P-B : ÉPHÉMÈRE touchant un carrefour (a mangé avec sa mère) — S1 dirait « fort » à tort.
  P-C : ÉPHÉMÈRE entre deux carrefours (deux importants croisés une fois) — S1 dirait « fort ».
  P-D : DURABLE entre deux isolés (deux inconnus mariés) — ni S1 ni la richesse n'aident.
Le verdict se lira SUR CES PIÈGES, jamais sur la moyenne.
"""

from dataclasses import dataclass, field

DURABLE = "DURABLE"
EPHEMERE = "ÉPHÉMÈRE"

# Nature VRAIE de chaque prédicat (vérité-terrain — JAMAIS vue par le prédicteur structurel).
#   reciproque : la relation ajoute-t-elle un lien inverse dans le graphe ? (symétrie/réciprocité)
#   datee      : occurrence unique datée ?
NATURE_PREDICAT = {
    "marie_a":      (DURABLE, True, False),
    "frere_de":     (DURABLE, True, False),
    "ami_de":       (DURABLE, True, False),
    "parent_de":    (DURABLE, True, False),    # inverse = enfant_de
    "enfant_de":    (DURABLE, True, False),    # lien inverse auxiliaire de parent_de
    "dirige":       (DURABLE, False, False),   # durable mais ASYMÉTRIQUE, sans date
    "appartient_a": (DURABLE, False, False),
    "possede":      (DURABLE, False, False),    # durable asymétrique non daté
    "travaille_pour": (DURABLE, False, False),  # durable asymétrique non daté
    "a_mange_avec": (EPHEMERE, False, True),
    "a_rencontre":  (EPHEMERE, False, True),
    "a_visite":     (EPHEMERE, False, True),
    "a_achete":     (EPHEMERE, False, True),
}
INVERSE = {"parent_de": "enfant_de"}  # prédicat du lien inverse (sinon même prédicat si symétrique)

# Les durables ASYMÉTRIQUES non datés : la frange que la structure seule ne voit pas.
# C'est la SEULE déclaration que s'autorise la béquille ciblée (ablation finale, étape 3).
ASYMETRIQUES_DURABLES = {"dirige", "appartient_a", "possede", "travaille_pour"}


@dataclass
class Lien:
    lid: int
    sujet: str
    objet: str
    predicat: str
    nature: str           # vérité-terrain (DURABLE / ÉPHÉMÈRE)
    forme: str            # "permanent" / "depuis" (date de début) / "ponctuel" (occurrence)
    valide_de: object     # borne de début (ou None)
    valide_jusqua: object  # borne de fin (ou None). ponctuel : de==jusqua ; depuis : jusqua=None
    piege: str            # "" / P-A..P-D / C-E (contre-exemple)
    primaire: bool = True  # False = lien inverse auxiliaire (pas évalué)


# ── MINI-MONDE (étape 1-2) ───────────────────────────────────────────────
#   (sujet, objet, prédicat, piège, forme)   forme : permanent / depuis / ponctuel
_MINI = [
    # cohérents DURABLE (carrefours)
    ("Maman", "Papa", "marie_a", "", "permanent"),
    ("Maman", "Moi", "parent_de", "", "permanent"),
    ("Maman", "Sœur", "parent_de", "", "permanent"),
    ("Papa", "Moi", "parent_de", "", "permanent"),
    ("Papa", "Sœur", "parent_de", "", "permanent"),
    ("Maman", "Amie", "ami_de", "", "permanent"),
    ("Directeur", "OrgX", "dirige", "", "permanent"),        # candidat FAUX-AMI (asym durable)
    ("Moi", "le Club Lecture", "appartient_a", "", "permanent"),  # candidat FAUX-AMI
    # cohérents ÉPHÉMÈRE (vers cul-de-sac)
    ("Moi", "Musée Rodin", "a_visite", "", "ponctuel"),
    ("Moi", "un Vélo", "a_achete", "", "ponctuel"),
    # CAS-PIÈGES
    ("Moi", "Léon", "frere_de", "P-A", "permanent"),         # durable vers isolé
    ("Moi", "Maman", "a_mange_avec", "P-B", "ponctuel"),     # éphémère touchant un carrefour
    ("Maman", "Directeur", "a_rencontre", "P-C", "ponctuel"),  # éphémère entre deux connectés
    ("Inconnu1", "Inconnu2", "marie_a", "P-D", "permanent"),  # durable entre deux isolés
    # CONTRE-EXEMPLE : durable PORTANT UNE DATE DE DÉBUT (« marié depuis 2015 »)
    ("Carl", "Dora", "marie_a", "C-E", "depuis"),
]

_T = 5  # mois de référence pour les dates


def _bornes(forme):
    if forme == "ponctuel":
        return _T, _T           # occurrence : début == fin
    if forme == "depuis":
        return _T, None         # date de début, toujours en cours
    return None, None           # permanent : aucune date


def generer_mini():
    liens = []
    lid = [0]

    def add(su, ob, pr, piege, forme, primaire=True):
        lid[0] += 1
        nat, recip, _ = NATURE_PREDICAT[pr]
        de, jus = _bornes(forme)
        liens.append(Lien(lid[0], su, ob, pr, nat, forme, de, jus, piege, primaire))

    for (su, ob, pr, piege, forme) in _MINI:
        add(su, ob, pr, piege, forme)
        _, recip, _ = NATURE_PREDICAT[pr]
        if recip:
            add(ob, su, INVERSE.get(pr, pr), "", "permanent", primaire=False)

    entites = sorted({l.sujet for l in liens} | {l.objet for l in liens})
    return entites, liens


# ── GRAND MONDE (étape 3) — ~50 entités, chargé en durables ASYMÉTRIQUES + ≥12 pièges ──
import random


def generer_grand(seed=42):
    rng = random.Random(seed)
    liens = []
    lid = [0]

    def add(su, ob, pr, piege, forme, primaire=True):
        lid[0] += 1
        nat, recip, _ = NATURE_PREDICAT[pr]
        de, jus = _bornes(forme)
        liens.append(Lien(lid[0], su, ob, pr, nat, forme, de, jus, piege, primaire))
        if primaire and recip:
            add(ob, su, INVERSE.get(pr, pr), "", "permanent", primaire=False)

    hubs = [f"Hub{i}" for i in range(5)]
    pers = [f"Per{i:02d}" for i in range(15)]
    orgs = [f"Org{i}" for i in range(6)]
    clubs = [f"Club{i}" for i in range(4)]
    objets = [f"Obj{i}" for i in range(6)]
    lieux = [f"Lieu{i}" for i in range(5)]
    isoles = [f"Iso{i:02d}" for i in range(10)]
    gens = hubs + pers

    # familles (durables RÉCIPROQUES) autour des hubs → clusters connectés
    for h in hubs:
        m = rng.sample(pers, 3)
        add(h, m[0], "marie_a", "", "permanent")
        add(h, m[1], "parent_de", "", "permanent")
        add(h, m[2], "frere_de", "", "permanent")
        add(h, rng.choice(pers), "ami_de", "", "permanent")

    # durables ASYMÉTRIQUES non datés (la FRANGE à chiffrer)
    for p in rng.sample(gens, 18):
        pr = rng.choice(["dirige", "travaille_pour", "appartient_a", "possede"])
        cible = (rng.choice(orgs) if pr in ("dirige", "travaille_pour")
                 else rng.choice(clubs) if pr == "appartient_a" else rng.choice(objets))
        add(p, cible, pr, "", "permanent")

    # éphémères COHÉRENTS (occurrences datées)
    for _ in range(14):
        pr = rng.choice(["a_visite", "a_achete", "a_mange_avec", "a_rencontre"])
        cible = (rng.choice(lieux) if pr == "a_visite" else rng.choice(objets) if pr == "a_achete"
                 else rng.choice(gens))
        add(rng.choice(gens), cible, pr, "", "ponctuel")

    # ── CAS-PIÈGES (≥12) ──
    for i in range(3):                              # P-A : durable vers cul-de-sac
        add(rng.choice(hubs), isoles[i], "frere_de", "P-A", "permanent")
    for i in range(3):                              # P-B : éphémère touchant un carrefour
        add(rng.choice(pers), rng.choice(hubs), "a_mange_avec", "P-B", "ponctuel")
    for i in range(3):                              # P-C : éphémère entre deux connectés
        a, b = rng.sample(hubs, 2)
        add(a, b, "a_rencontre", "P-C", "ponctuel")
    for i in range(3):                              # P-D : durable entre deux isolés
        add(isoles[3 + 2 * i], isoles[4 + 2 * i], "marie_a", "P-D", "permanent")
    for i in range(2):                              # C-E : durable AVEC date de début
        add(f"Cea{i}", f"Ceb{i}", "marie_a", "C-E", "depuis")

    entites = sorted({l.sujet for l in liens} | {l.objet for l in liens})
    return entites, liens


# ── FEATURES STRUCTURELLES (calculées sur le graphe, jamais sur les étiquettes) ──
def voisins(liens):
    g = {}
    for l in liens:
        g.setdefault(l.sujet, set()).add(l.objet)
        g.setdefault(l.objet, set()).add(l.sujet)
    return g


def degres(liens):
    g = voisins(liens)
    return {e: len(v) for e, v in g.items()}


def reciproque(lien, liens):
    """Existe-t-il un lien en sens INVERSE (objet→sujet) dans le graphe ?"""
    return any(l.sujet == lien.objet and l.objet == lien.sujet
               for l in liens if l.lid != lien.lid)


def features(lien, liens, deg):
    """Ce que VOIT le prédicteur : SEULEMENT la topologie + les bornes temporelles. Jamais le
    prédicat ni la nature. On distingue OCCURRENCE (début==fin, ponctuel) de DATE DE DÉBUT (en cours)."""
    de, jus = lien.valide_de, lien.valide_jusqua
    return {
        "deg_sujet": deg.get(lien.sujet, 0),
        "deg_objet": deg.get(lien.objet, 0),
        "reciproque": reciproque(lien, liens),
        "porte_date": de is not None,                      # signal NAÏF (à ne pas utiliser seul)
        "est_occurrence": (de is not None and jus is not None),  # occurrence ponctuelle (début==fin)
    }
