# -*- coding: utf-8 -*-
"""
etape_v3_1_importance.py — MICRO-TEST DU CALCUL D'IMPORTANCE (V3, étape 1).

Mini-graphe familial écrit à la main. On calcule l'importance des ENTITÉS (PageRank pondéré)
et des FAITS (croisement poids_relation × importance_entité), et on vérifie les TROIS cas de
croisement de la mission :
    nom-du-proche (CAPITAL) > parent-d'inconnus (MOYEN-FAIBLE) > repas-du-proche (FAIBLE)

Pas d'appel LLM (seulement des embeddings pour l'ingestion). Lance :  python etape_v3_1_importance.py
"""

import os
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import v3_importance
from util import Journal
from v2_modele import GrapheMemoire, norm_nom, norm_valeur

D = datetime(2026, 6, 1)

# (sujet, predicat, objet, source) — graphe familial autour de « ma mère »
FAITS = [
    ("ma mère", "nom_de", "Marie", "état civil"),
    ("ma mère", "nom_de", "Marie", "carnet"),                 # corroboré (2 sources)
    ("ma mère", "marie_a", "mon père", "famille"),
    ("ma mère", "marie_a", "mon père", "mairie"),
    ("ma mère", "parent_de", "moi", "famille"),
    ("ma mère", "parent_de", "ma sœur", "famille"),
    ("grand-mère", "parent_de", "ma mère", "famille"),
    ("ma mère", "connait", "grand-mère", "famille"),
    ("ma mère", "profession_de", "médecin", "ordre"),
    ("ma mère", "repas_de", "des pâtes", "moi"),              # RÉCENT, trivial
    ("moi", "repas_de", "une pizza", "moi"),
    ("mon père", "profession_de", "ingénieur", "ordre"),
    # cas 3 : parenté entre INCONNUS isolés (poids haut, mais entités sans importance)
    ("M. Inconnu", "parent_de", "Mlle Obscure", "rumeur"),
]
TYPES = {"ma mère": "personne", "mon père": "personne", "moi": "personne",
         "ma sœur": "personne", "grand-mère": "personne",
         "M. Inconnu": "personne", "Mlle Obscure": "personne"}


def ent(g, nom):
    for e in g.entites.values():
        if norm_nom(nom) in [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]:
            return e
    return None


def fait(g, pred, sujet, obj_contient=None):
    e = ent(g, sujet)
    for f in g.faits.values():
        if f.predicat == pred and f.sujet_id == e.id:
            if obj_contient is None or obj_contient in norm_valeur(f.objet):
                return f
    return None


def main():
    J = Journal("etape_v3_1_importance")
    dire = J.dire
    dire("=" * 88)
    dire(" V3 · ÉTAPE 1 — CALCUL DE L'IMPORTANCE (PageRank pondéré + croisement)")
    dire(f"   d={config.IMP_DAMPING} | α={config.IMP_ALPHA} | seeds : degré {config.IMP_SEED_DEGRE} "
         f"+ sources {config.IMP_SEED_SOURCES} + catégorie {config.IMP_SEED_CATEGORIE}")
    dire("=" * 88)

    g = GrapheMemoire()
    for (su, pr, ob, src) in FAITS:
        g.ingerer(su, pr, ob, source_id=src, date_obs=D)
    for nom, typ in TYPES.items():
        e = ent(g, nom)
        if e:
            e.type = typ

    imp_ent = v3_importance.calculer(g)

    # ── Classement des ENTITÉS ───────────────────────────────────────────
    dire("\n— IMPORTANCE DES ENTITÉS (la « rivière » coule vers les nœuds centraux) —")
    for eid in sorted(imp_ent, key=lambda x: -imp_ent[x]):
        e = g.entites[eid]
        deg = sum(1 for f in g.faits.values() if f.sujet_id == eid or f.objet_id == eid)
        dire(f"   {imp_ent[eid]:.3f}  {e.nom:<14} ({e.type}, degré {deg})")

    # ── Classement des FAITS ─────────────────────────────────────────────
    dire("\n— IMPORTANCE DES FAITS (poids_relation × max(imp_sujet, imp_objet)^α) —")
    for f in sorted(g.faits.values(), key=lambda x: -x.importance):
        from v2_ontologie import poids_importance
        dire(f"   {f.importance:.3f}  [w={poids_importance(f.predicat):.2f}] "
             f"{f.predicat}({g.nom_entite(f.sujet_id)})={f.objet}")

    # ── LES TROIS CAS DE CROISEMENT ──────────────────────────────────────
    dire("\n" + "=" * 88)
    dire(" LES TROIS CAS DE CROISEMENT (test d'acceptation principal)")
    dire("=" * 88)
    f_nom = fait(g, "nom_de", "ma mère")
    f_repas = fait(g, "repas_de", "ma mère")
    f_inconnu = fait(g, "parent_de", "M. Inconnu")
    dire(f"   CAPITAL       nom de ma mère        : {f_nom.importance:.3f}  "
         f"(relation forte × entité importante)")
    dire(f"   MOYEN-FAIBLE  parent d'inconnus     : {f_inconnu.importance:.3f}  "
         f"(relation forte × entités sans importance)")
    dire(f"   FAIBLE        repas de ma mère      : {f_repas.importance:.3f}  "
         f"(relation triviale écrase l'entité importante)")

    ordre_ok = f_nom.importance > f_inconnu.importance > f_repas.importance
    dire("")
    dire(f"   {'✅' if ordre_ok else '❌'} Ordre attendu CAPITAL > MOYEN-FAIBLE > FAIBLE : "
         f"{f_nom.importance:.3f} > {f_inconnu.importance:.3f} > {f_repas.importance:.3f}")
    # contraste canonique : le nom (à protéger) bien au-dessus du repas (effaçable)
    ratio = f_nom.importance / max(f_repas.importance, 1e-6)
    dire(f"   {'✅' if ratio > 5 else '⚠'} « nom du proche » vaut ×{ratio:.0f} le « repas du proche » "
         f"→ c'est lui qu'il faudra protéger de la dormance (étape 2).")

    dire("\n" + "=" * 88)
    dire(f" ✅ Micro-test importance terminé. Journal : {J.chemin}")
    dire("=" * 88)
    J.fermer()


if __name__ == "__main__":
    main()
