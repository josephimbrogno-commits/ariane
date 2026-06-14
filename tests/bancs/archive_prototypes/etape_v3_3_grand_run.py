# -*- coding: utf-8 -*-
"""
etape_v3_3_grand_run.py — GRAND RUN V3 + ABLATION (mission V3, §4.3 / §4.5).

Trois lectures sur le MÊME graphe (ingestion identique → greffier identique) :
  • C-v2     : retrieval entité (étape v2.5), SANS reconnaissance, SANS importance, dormance V2.
  • C-v3-β0  : reconnaissance/rappel ON, importance NON utilisée (β=0, pas dans le score). « La porte. »
  • C-v3     : reconnaissance ON + importance utilisée (dormance β=0.9 + terme de score). « L'axe. »

Lecture demandée :
 (1) faits MUETS : C-v2 vs C-v3 vs C-v3-β0 (l'effondrement vient-il de l'importance ou de la porte ?)
 (2) faits CHANGÉS : mêmes 3 colonnes (garde-fou anti-périmé : ils ne doivent pas reculer)
 (3) non-régression menteur / rumeur / Dupont.

Lance :  python etape_v3_3_grand_run.py
"""

import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import modele
import cycle
import monde
import v2_lecture
import v2_monde
import v3_importance
from util import Journal, assurer_dossiers
from monde import normaliser
from v2_modele import norm_nom, norm_valeur
from etape_v2_4_grand_run import (
    REPONDEUR, construire_cv2, construire_inerte, repondre_inerte, diagnostiquer,
)
from etape_v2_5_durci import correct_strict, menteur_resiste


def type_entites(g):
    tmap = {}
    for n in monde.ENTREPRISES:
        tmap[norm_nom(n)] = "organisation"
    for n in monde.VILLES_ENT:
        tmap[norm_nom(n)] = "lieu"
    for n in monde.PERSONNES:
        tmap[norm_nom(n)] = "personne"
    for n in monde.LIEUX:
        tmap[norm_nom(n)] = "lieu"
    for e in g.entites.values():
        t = tmap.get(norm_nom(e.nom))
        if t is None:
            t = "personne" if len(norm_nom(e.nom).split()) <= 1 else "organisation"
        e.type = t


def lire_C(g, question, mode):
    if mode == "v2":
        fe, v = v2_lecture.entree_vectorielle_v2(g, question)
        reco = []
    else:
        fe, v = v2_lecture.entree_vectorielle_v3(g, question, use_importance=(mode == "v3"))
        reco = v2_lecture.reconnaissance(g, question)
    fm = v2_lecture.marche_graphe(g, fe + reco, v)
    vus, inj = set(), []
    for f in reco + fe + fm:
        if f.id not in vus:
            vus.add(f.id); inj.append(f)
    bloc = v2_lecture.rendu_epistemique(g, inj)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    return modele.repondre(prompt, systeme=v2_lecture.SYS_REPONSE_V2, temperature=0.0, model=REPONDEUR)


def prec(items, cat=None):
    sel = [x for x in items if cat is None or x[0].categorie() == cat]
    return (100.0 * sum(1 for f, rep in sel if correct_strict(rep, f)) / len(sel)) if sel else 0.0


def muets(g, items):
    """Faits VRAIS devenus muets : réponse fausse ALORS QUE le fait est bien stocké (architecte)."""
    return sum(1 for f, rep in items
               if not correct_strict(rep, f) and diagnostiquer(g, f) == "architecte")


def main():
    assurer_dossiers()
    J = Journal("etape_v3_3")
    dire = J.dire
    dire("=" * 88)
    dire(" V3 · ÉTAPE 3 — GRAND RUN + ABLATION (C-v2 / C-v3-β0 / C-v3)")
    dire("=" * 88)

    faits, flux, special = v2_monde.generer_monde_v2()
    questions = v2_monde.choisir_questions(faits, config.N_QUESTIONS_EVAL_V2)

    dire("\n[1/3] Ingestion + typage + importance + plancher…")
    g, audit = construire_cv2(flux, dire)
    type_entites(g)
    v3_importance.calculer(g)
    g.appliquer_plancher_certitude()
    dire(f"  Graphe {len(g.entites)} entités / {len(g.faits)} faits ; extraction "
         f"{100*audit['extrait_ok']/audit['total']:.0f}%.")

    dire("\n[2/3] Baselines A / B / B′…")
    memB, memB2 = construire_inerte(faits, True), construire_inerte(faits, False)
    base = []
    for i, f in enumerate(questions, 1):
        q = f.question()
        base.append({
            "f": f,
            "A": modele.repondre(q, systeme=cycle.SYS_REPONSE_A, temperature=0.0, model=REPONDEUR),
            "B": repondre_inerte(memB, q), "Bp": repondre_inerte(memB2, q),
        })
        if i % 10 == 0:
            dire(f"    …{i}/{len(questions)}")
    pA = {c or "g": round(100*sum(1 for x in base if (c is None or x['f'].categorie()==c) and correct_strict(x['A'], x['f']))/max(1,len([x for x in base if c is None or x['f'].categorie()==c])),0) for c in (None,'changé','stable')}

    dire("\n[3/3] C-v2 / C-v3-β0 / C-v3-dorm / C-v3 (même graphe)…")
    #  v3dorm : reconnaissance + importance en DORMANCE seule (β=0.9), RETIRÉE du score de retrieval
    MODES = [("v2", 0.0), ("v3b0", 0.0), ("v3dorm", 0.9), ("v3", 0.9)]
    R = {}
    for mode, beta in MODES:
        g.recalculer_dormance(beta)
        items = [(f, lire_C(g, f.question(), mode)) for f in questions]
        R[mode] = {"items": items,
                   "global": round(prec(items), 0), "changé": round(prec(items, "changé"), 0),
                   "stable": round(prec(items, "stable"), 0), "muets": muets(g, items)}
        dire(f"  {mode:6} : changés {R[mode]['changé']:.0f}% stables {R[mode]['stable']:.0f}% "
             f"global {R[mode]['global']:.0f}% | faits muets {R[mode]['muets']}")

    # non-régression (graphe avec plancher ; indépendant du mode de lecture)
    g.recalculer_dormance(0.9)
    men = menteur_resiste(g, special)
    fr = special["rumeur"]
    e = g.trouver_entite(fr.entite)
    rf = next((x for x in g.faits_de(e.id, fr.predicat)
               if norm_valeur(x.objet) == norm_valeur(getattr(fr, "_faux", "∅"))), None) if e else None
    rumeur_ok = (rf is None) or (rf.certitude <= config.V2_CERT_PLAFOND_MENTEUR + 1e-9)
    dup = 0
    for f in special["dupont"]:
        e = g.trouver_entite(f.entite)
        fx = next((x for x in g.faits_de(e.id, f.predicat)
                   if norm_valeur(x.objet) == norm_valeur(f.val_init)), None) if e else None
        if fx and fx.certitude < 0.6:
            dup += 1

    # ── RAPPORT ──────────────────────────────────────────────────────────
    rep = []
    w = rep.append
    w("# Étape 3 — Grand run V3 + ablation\n")
    w(f"- Monde : {len(faits)} faits, {len(flux)} énoncés, {len(questions)} questions. "
      f"Répondeur `{REPONDEUR}`. Greffier (extraction) {100*audit['extrait_ok']/audit['total']:.0f}%.\n")
    w("## (1) Faits VRAIS devenus MUETS (le défaut visé)\n")
    w("| | C-v2 (V2) | C-v3-β0 (porte) | C-v3-dorm (porte+dormance) | C-v3 (axe complet) |")
    w("|---|---|---|---|---|")
    w(f"| **Faits muets** | {R['v2']['muets']} | {R['v3b0']['muets']} | {R['v3dorm']['muets']} | {R['v3']['muets']} |")
    w("\nLecture de l'ablation : C-v2 → C-v3-β0 = apport de la **reconnaissance/rappel** (la porte) ; "
      "C-v3-β0 → C-v3-dorm = effet de l'**importance en DORMANCE seule** ; C-v3-dorm → C-v3 = effet "
      "d'ajouter l'**importance au SCORE de retrieval**.\n")
    w("## (2) Précision (métrique stricte) — garde-fou anti-périmé\n")
    w("| Config | Changés | Stables | Global |")
    w("|---|---|---|---|")
    w(f"| A — modèle seul | {pA['changé']:.0f}% | {pA['stable']:.0f}% | {pA['g']:.0f}% |")
    for mode, nom in [("v2", "C-v2"), ("v3b0", "C-v3-β0 (porte)"),
                      ("v3dorm", "C-v3-dorm (porte+dormance)"), ("v3", "C-v3 (axe complet)")]:
        w(f"| **{nom}** | {R[mode]['changé']:.0f}% | {R[mode]['stable']:.0f}% | {R[mode]['global']:.0f}% |")
    w("\n*Les faits changés ne doivent pas reculer entre les colonnes (sinon des dormants importants "
      "mais PÉRIMÉS remonteraient à tort).*\n")
    w("## (3) Non-régression V2\n")
    w(f"- Menteur : **{men}/5** · Rumeur : **{'OK' if rumeur_ok else 'KO'}** · Dupont : **{dup}/3**.\n")

    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape_v3_3_rapport.md")
    with open(chemin, "w", encoding="utf-8") as fp:
        fp.write("\n".join(rep))
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape_v3_3_data.json"), "w", encoding="utf-8") as fp:
        json.dump({"A": pA, "muets": {m: R[m]["muets"] for m in R},
                   "prec": {m: {k: R[m][k] for k in ("changé", "stable", "global")} for m in R},
                   "menteur": men, "rumeur_ok": rumeur_ok, "dupont": dup}, fp, ensure_ascii=False, indent=2)

    dire("\n" + "=" * 88)
    dire(f" MUETS   : C-v2 {R['v2']['muets']} → β0 {R['v3b0']['muets']} → dorm {R['v3dorm']['muets']} → v3 {R['v3']['muets']}")
    dire(f" CHANGÉS : v2 {R['v2']['changé']:.0f}% / β0 {R['v3b0']['changé']:.0f}% / dorm {R['v3dorm']['changé']:.0f}% / v3 {R['v3']['changé']:.0f}%")
    dire(f" STABLES : v2 {R['v2']['stable']:.0f}% / β0 {R['v3b0']['stable']:.0f}% / dorm {R['v3dorm']['stable']:.0f}% / v3 {R['v3']['stable']:.0f}%")
    dire(f" GLOBAL  : v2 {R['v2']['global']:.0f}% / β0 {R['v3b0']['global']:.0f}% / dorm {R['v3dorm']['global']:.0f}% / v3 {R['v3']['global']:.0f}%")
    dire(f" Non-rég : menteur {men}/5 · rumeur {'OK' if rumeur_ok else 'KO'} · dupont {dup}/3")
    dire("=" * 88)
    dire(f"\n Rapport : {chemin}\n Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
