# -*- coding: utf-8 -*-
"""
etape_v2_1_ingestion.py — MICRO-TEST D'ÉCRITURE (V2, étape de construction 1).

20 énoncés (avec sources nommées et dates) couvrant : création, corroboration indépendante,
répétition même source (anti-rumeur), conflit fonctionnel → CLÔTURE, menteur vs vérité
corroborée → DISPUTÉ, résolution de dispute, fait immuable, multi-valué, résolution d'alias.

On montre l'état de la base APRÈS CHAQUE énoncé. L'extraction LLM est exécutée et MESURÉE
(surface d'erreur du V2), mais la logique d'écriture est pilotée par des triplets de RÉFÉRENCE
pour une démonstration nette des transitions d'état.

Lance :  python etape_v2_1_ingestion.py
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
from util import Journal
from v2_modele import GrapheMemoire, norm_nom, norm_valeur
import v2_extraction


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


# (source, date, texte, [référence] sujet, predicat, objet, validite, cas attendu)
ENONCES = [
    ("Gazette",     "2026-01-05", "Le PDG de Nexora est Mme Karel.",            "Nexora", "pdg_de", "Mme Karel", None, "création"),
    ("Gazette",     "2026-02-05", "Mme Karel dirige toujours Nexora.",          "Nexora", "pdg_de", "Mme Karel", None, "répétition même source"),
    ("Tribune",     "2026-02-12", "Mme Karel préside Nexora.",                  "Nexora", "pdg_de", "Mme Karel", None, "corroboration indépendante"),
    ("Officiel",    "2026-05-20", "Depuis mai 2026, M. Doss est le PDG de Nexora.", "Nexora", "pdg_de", "M. Doss", "2026-05", "conflit → clôture"),
    ("Presse",      "2026-05-25", "M. Doss préside désormais Nexora.",          "Nexora", "pdg_de", "M. Doss", None, "corroboration (nouveau courant)"),
    ("Gazette",     "2026-01-08", "Le siège de Veltis est à Lyon.",             "Veltis", "siege_de", "Lyon", None, "création"),
    ("Tribune",     "2026-01-20", "Veltis a son siège à Lyon.",                 "Veltis", "siege_de", "Lyon", None, "corroboration indépendante"),
    ("BlogDouteux", "2026-03-01", "Le siège de Veltis serait à Brest.",         "Veltis", "siege_de", "Brest", None, "menteur → DISPUTÉ"),
    ("BlogDouteux", "2026-03-05", "Le siège de Veltis serait encore à Brest.",  "Veltis", "siege_de", "Brest", None, "répétition même source (anti-rumeur)"),
    ("Officiel",    "2026-03-15", "Veltis confirme son siège à Lyon.",          "Veltis", "siege_de", "Lyon", None, "corroboration → Lyon redevient courant"),
    ("Gazette",     "2026-01-03", "Veltis a été fondée en 1998.",               "Veltis", "date_fondation_de", "1998", "1998", "immuable (création)"),
    ("Almanach",    "2026-04-10", "Veltis existe depuis 1998.",                 "Veltis", "date_fondation_de", "1998", "1998", "corroboration immuable"),
    ("Gazette",     "2026-02-01", "Veltis fabrique des panneaux solaires.",     "Veltis", "produit", "panneaux solaires", None, "multi-valué (création)"),
    ("Gazette",     "2026-02-02", "Veltis fabrique aussi des batteries.",       "Veltis", "produit", "batteries", None, "multi-valué (ajout, pas conflit)"),
    ("Gazette",     "2026-01-04", "Mme Karel est née en 1970.",                 "Mme Karel", "date_naissance_de", "1970", "1970", "immuable (entité réutilisée)"),
    ("Tribune",     "2026-01-22", "Karel, née en 1970, fête son anniversaire.", "Karel", "date_naissance_de", "1970", "1970", "corroboration + alias"),
    ("Gazette",     "2026-01-06", "M. Dupont est marié à Mme Sora.",            "M. Dupont", "marie_a", "Mme Sora", None, "stable (cas Dupont)"),
    ("Inconnu",     "2026-04-01", "Nexora Corp emploie 500 personnes.",         "Nexora Corp", "effectif_de", "500", None, "alias + création"),
    ("Officiel",    "2026-05-02", "Depuis mai 2026, Nexora emploie 520 personnes.", "Nexora", "effectif_de", "520", "2026-05", "conflit → clôture"),
    ("Presse",      "2026-05-10", "Nexora compte 520 employés.",               "Nexora", "effectif_de", "520", None, "corroboration"),
]


def ent_par_nom(g, nom):
    for e in g.entites.values():
        noms = [norm_nom(e.nom)] + [norm_nom(a) for a in e.alias]
        if norm_nom(nom) in noms:
            return e
    return None


def main():
    J = Journal("etape_v2_1_ingestion")
    dire = J.dire
    dire("=" * 90)
    dire(" V2 · ÉTAPE 1 — MICRO-TEST D'ÉCRITURE (graphe daté, deux axes Force/Certitude)")
    dire(f"   Force : init {config.V2_FORCE_INIT}, demi-vie {config.V2_FORCE_DEMIVIE} j | "
         f"Certitude : init {config.V2_CERT_INIT_1SOURCE}, +{config.V2_CERT_GAIN_CORRO}/corro, "
         f"plafond menteur {config.V2_CERT_PLAFOND_MENTEUR}")
    dire("=" * 90)

    g = GrapheMemoire()
    extr_ok = 0

    for i, (src, dt, txt, su, pr, ob, va, cas) in enumerate(ENONCES, start=1):
        dire("\n" + "─" * 90)
        dire(f"[{i:2}] {src} ({dt}) : « {txt} »")

        # Extraction LLM (mesurée), puis logique pilotée par la référence
        ext = v2_extraction.extraire(txt)
        if ext and ext["predicat"] == pr and norm_nom(ext["sujet"]) == norm_nom(su) \
           and norm_valeur(ext["objet"]) == norm_valeur(ob):
            extr_ok += 1
            marque = "✓"
        else:
            marque = "✗"
        ext_aff = (f"({ext['sujet']}, {ext['predicat']}, {ext['objet']}, {ext['date_validite']})"
                   if ext else "ÉCHEC")
        dire(f"     extraction LLM : {ext_aff}  [{marque} vs référence]")

        res = g.ingerer(su, pr, ob, source_id=src, date_obs=d(dt), date_validite=va)
        dire(f"     → cas attendu : {cas}")
        dire(f"     → ACTION : {res['action']}")
        for f in res["touches"]:
            dire(f"         {g.fait_court(f)}")

        # état courant du sujet pour ce prédicat
        sujet_e = res["sujet"]
        memes_pred = g.faits_de(sujet_e.id, pr)
        if len(memes_pred) > 1:
            dire(f"     état de {pr}({sujet_e.nom}) :")
            for f in sorted(memes_pred, key=lambda x: x.id):
                dire(f"         {g.fait_court(f)}")

    # ── BILAN ────────────────────────────────────────────────────────────
    dire("\n" + "=" * 90)
    dire(" BILAN DE LA BASE")
    dire("=" * 90)
    dire(f"   Entités : {len(g.entites)} | Faits : {len(g.faits)}")
    dire(f"   Extraction LLM correcte : {extr_ok}/{len(ENONCES)} "
         f"({100*extr_ok/len(ENONCES):.0f} %) — surface d'erreur V2, mesurée à part.")
    if g.journal_resolution:
        dire("   Résolutions ambiguës (audit) :")
        for r in g.journal_resolution:
            dire(f"      « {r['nom']} » ~ « {r['proche']} » (score {r['score']}) → {r['decision']}")

    # ── VÉRIFICATIONS AUTOMATIQUES (un mécanisme par ligne) ──────────────
    dire("\n" + "=" * 90)
    dire(" VÉRIFICATIONS (vérité-terrain des mécanismes)")
    dire("=" * 90)

    def fait_courant(nom, pred):
        e = ent_par_nom(g, nom)
        if not e:
            return None
        cs = [f for f in g.faits_de(e.id, pred) if f.statut == "courant"]
        return cs[0] if cs else None

    def faits(nom, pred):
        e = ent_par_nom(g, nom)
        return g.faits_de(e.id, pred) if e else []

    def ok(cond, label):
        dire(f"   {'✅' if cond else '❌'} {label}")

    # 1) Clôture : Karel clos (était PDG), Doss courant corroboré
    karel = next((f for f in faits("Nexora", "pdg_de")
                  if "karel" in norm_valeur(f.objet)), None)
    doss = fait_courant("Nexora", "pdg_de")
    ok(karel and karel.statut == "clos" and karel.valide_jusqua is not None,
       f"CLÔTURE : ancien PDG (Karel) clos avec date de fin "
       f"({karel.valide_jusqua.strftime('%Y-%m') if karel and karel.valide_jusqua else '—'})")
    ok(doss and "doss" in norm_valeur(doss.objet) and doss.n_sources() >= 2 and doss.certitude >= 0.7,
       f"NOUVEAU COURANT : Doss PDG, corroboré (C={doss.certitude:.2f}, {doss.n_sources() if doss else 0} src)")

    # 2) Menteur : Lyon courant fort, Brest disputé faible (la vérité n'a pas basculé)
    lyon = fait_courant("Veltis", "siege_de")
    brest = next((f for f in faits("Veltis", "siege_de") if "brest" in norm_valeur(f.objet)), None)
    ok(lyon and "lyon" in norm_valeur(lyon.objet) and lyon.certitude >= 0.8,
       f"MENTEUR : la vérité résiste — siège courant = Lyon (C={lyon.certitude:.2f}, {lyon.n_sources() if lyon else 0} src)")
    ok(brest and brest.statut == "disputé" and brest.certitude <= config.V2_CERT_PLAFOND_MENTEUR,
       f"ANTI-RUMEUR : Brest reste disputé et plafonné (C={brest.certitude:.2f}, {brest.n_sources() if brest else 0} src) malgré répétition")

    # 3) Immuable : fondation corroborée, volatilité immuable
    fond = next((f for f in faits("Veltis", "date_fondation_de")), None)
    from v2_ontologie import PREDICATS
    ok(fond and PREDICATS["date_fondation_de"]["volatilite"] == "immuable" and fond.n_sources() >= 2,
       f"IMMUABLE : fondation Veltis (volatilité immuable, C ne décroîtra jamais, {fond.n_sources() if fond else 0} src)")

    # 4) Multi-valué : 2 produits courants
    prods = [f for f in faits("Veltis", "produit") if f.statut == "courant"]
    ok(len(prods) == 2, f"MULTI-VALUÉ : Veltis a {len(prods)} produits courants (ajout, pas conflit)")

    # 5) Alias : Nexora Corp → Nexora ; une seule entité Karel
    nex = ent_par_nom(g, "Nexora")
    ok(nex and any("corp" in norm_nom(a) for a in nex.alias),
       f"ALIAS : « Nexora Corp » résolu vers Nexora (alias {nex.alias if nex else []})")
    karels = [e for e in g.entites.values() if norm_nom(e.nom) == "karel"]
    ok(len(karels) == 1, f"ENTITÉ UNIQUE : une seule Mme Karel (réutilisée pour la naissance)")

    # 6) Effectif : 500 clos, 520 courant
    eff_cour = fait_courant("Nexora", "effectif_de")
    ok(eff_cour and "520" in eff_cour.objet, "CLÔTURE 2 : effectif 500 → 520 (succession datée)")

    dire("\n" + "=" * 90)
    dire(f" ✅ Micro-test d'écriture terminé. Journal : {J.chemin}")
    dire("=" * 90)
    J.fermer()


if __name__ == "__main__":
    main()
