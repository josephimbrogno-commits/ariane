# -*- coding: utf-8 -*-
"""
etape_v2_5_durci.py — MÉTRIQUE STRICTE puis FIX (retrieval + plancher de Certitude).

Ordre demandé :
 1) Re-noter les 5 configs avec une métrique STRICTE (anti-hedging) AVANT tout fix :
    juste = la BONNE valeur citée ET (pour un fait changé) l'ANCIENNE non réassertée comme
    courante. L'imparfait borné (« était PDG jusqu'en mai ») reste CORRECT.
 2) Appliquer les fixes : entrée vectorielle élargie + bonus d'entité (architecte),
    et plancher de Certitude pour les faits ≥2 sources (menteur) ; re-mesurer C-v2.

Lance :  python etape_v2_5_durci.py
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
import v2_lecture
import v2_monde
from util import Journal, assurer_dossiers
from monde import normaliser
from v2_modele import norm_valeur
from etape_v2_4_grand_run import (
    REPONDEUR, construire_cv2, construire_inerte, repondre_inerte, diagnostiquer, correct,
)

PASSE = ["etait", "jusqu", "ancien", "plus le", "auparavant", "avant", "precedent",
         "anciennement", "fut ", "remplac", "quitt", "succed", "n est plus"]


def correct_lenient(rep, f):
    """Ancienne métrique (sous-chaîne) adaptée à la signature (rep, fait)."""
    return correct(rep, f.cle_vraie())


def correct_strict(rep, f):
    """Bonne valeur citée ET ancienne non réassertée comme courante (imparfait borné = OK)."""
    n = normaliser(rep)
    if f.cle_vraie() not in n:
        return False
    if f.change and f.cle_init != f.cle_vraie() and f.cle_init in n:
        if not any(m in n for m in PASSE):
            return False        # l'ancienne valeur est réassertée au présent → faux
    return True


def lire(g, question, retrieval_fn):
    faits_e, v = retrieval_fn(g, question)
    faits_m = v2_lecture.marche_graphe(g, faits_e, v)
    vus, injectes = set(), []
    for f in faits_e + faits_m:
        if f.id not in vus:
            vus.add(f.id); injectes.append(f)
    bloc = v2_lecture.rendu_epistemique(g, injectes)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    return modele.repondre(prompt, systeme=v2_lecture.SYS_REPONSE_V2, temperature=0.0, model=REPONDEUR)


def menteur_resiste(g, special):
    n = 0
    for f in special["menteur"]:
        e = g.trouver_entite(f.entite)
        if not e:
            continue
        fs = g.faits_de(e.id, f.predicat)
        vrai = next((x for x in fs if norm_valeur(x.objet) == norm_valeur(f.val_init)), None)
        faux = next((x for x in fs if norm_valeur(x.objet) == norm_valeur(getattr(f, "_faux", "∅"))), None)
        if vrai and (faux is None or vrai.certitude >= faux.certitude):
            n += 1
    return n


def prec(items, fn, cat=None):
    sel = [x for x in items if cat is None or x[0].categorie() == cat]
    return (100.0 * sum(1 for f, rep in sel if fn(rep, f)) / len(sel)) if sel else 0.0


def main():
    assurer_dossiers()
    J = Journal("etape_v2_5")
    dire = J.dire
    dire("=" * 84)
    dire(" V2 · ÉTAPE 5 — métrique STRICTE puis FIX (retrieval + plancher)")
    dire("=" * 84)

    faits, flux, special = v2_monde.generer_monde_v2()
    questions = v2_monde.choisir_questions(faits, config.N_QUESTIONS_EVAL_V2)

    dire("\n[1/4] Ingestion de C-v2…")
    g, audit = construire_cv2(flux, dire)
    dire(f"  Graphe {len(g.entites)} entités / {len(g.faits)} faits ; extraction "
         f"{100*audit['extrait_ok']/audit['total']:.0f}%.")

    dire("\n[2/4] Réponses A / B / B′ (capturées pour la notation stricte)…")
    memB = construire_inerte(faits, True)
    memB2 = construire_inerte(faits, False)
    rA, rB, rBp = [], [], []
    for i, f in enumerate(questions, 1):
        q = f.question()
        rA.append((f, modele.repondre(q, systeme=cycle.SYS_REPONSE_A, temperature=0.0, model=REPONDEUR)))
        rB.append((f, repondre_inerte(memB, q)))
        rBp.append((f, repondre_inerte(memB2, q)))
        if i % 10 == 0:
            dire(f"    …{i}/{len(questions)}")

    dire("\n[3/4] C-v2 AVANT fix (retrieval k=5)…")
    cv2_old = [(f, lire(g, f.question(), v2_lecture.entree_vectorielle)) for f in questions]
    menteur_pre = menteur_resiste(g, special)

    dire("[4/4] FIX : plancher de Certitude + retrieval élargi/boosté → C-v2 APRÈS fix…")
    g.appliquer_plancher_certitude()
    cv2_new = [(f, lire(g, f.question(), v2_lecture.entree_vectorielle_v2)) for f in questions]
    menteur_post = menteur_resiste(g, special)

    # ── Tableaux ─────────────────────────────────────────────────────────
    def bloc_prec(items, fn):
        return {c or "global": round(prec(items, fn, c), 0) for c in (None, "changé", "stable")}

    # lenient (ancienne métrique) pour montrer l'artefact, + stricte
    L = {  # lenient
        "A": bloc_prec(rA, correct_lenient), "B": bloc_prec(rB, correct_lenient),
        "Bp": bloc_prec(rBp, correct_lenient), "C": bloc_prec(cv2_old, correct_lenient),
    }
    S = {  # stricte (pré-fix)
        "A": bloc_prec(rA, correct_strict), "B": bloc_prec(rB, correct_strict),
        "Bp": bloc_prec(rBp, correct_strict), "C": bloc_prec(cv2_old, correct_strict),
    }
    Cnew = bloc_prec(cv2_new, correct_strict)

    # décomposition des erreurs C-v2 APRÈS fix
    err = [(f, rep) for (f, rep) in cv2_new if not correct_strict(rep, f)]
    greffier = sum(1 for f, _ in err if diagnostiquer(g, f) == "greffier")
    architecte = len(err) - greffier

    # ── RAPPORT ──────────────────────────────────────────────────────────
    R = []
    w = R.append
    w("# Étape 5 — Métrique stricte + fixes (retrieval, plancher de Certitude)\n")
    w("## 1) Re-notation avec la métrique STRICTE (anti-hedging), AVANT tout fix\n")
    w("Métrique stricte : la bonne valeur citée ET, pour un fait changé, l'ancienne non réassertée "
      "comme courante (l'imparfait borné « était… jusqu'en… » reste correct).\n")
    w("| Config | Changés (lenient → **stricte**) | Stables | Global (lenient → **stricte**) |")
    w("|---|---|---|---|")
    for k, nom in [("A", "A — modèle seul"), ("B", "B — RAG inerte daté"),
                   ("Bp", "B′ — RAG inerte aveugle"), ("C", "C-v2 — graphe daté")]:
        w(f"| {nom} | {L[k]['changé']:.0f}% → **{S[k]['changé']:.0f}%** | "
          f"{S[k]['stable']:.0f}% | {L[k]['global']:.0f}% → **{S[k]['global']:.0f}%** |")
    w(f"\n**Leçon méthodologique** : l'écart lenient→stricte chez B′ (aveugle) "
      f"({L['Bp']['changé']:.0f}% → {S['Bp']['changé']:.0f}% sur les changés) chiffre **l'artefact de "
      f"hedging** : la correspondance par sous-chaîne récompensait B′ qui déverse l'ancienne ET la "
      f"nouvelle valeur. La métrique stricte, qui exige de TRANCHER, neutralise l'artefact.\n")

    w("## 2) Après fixes — C-v2 (métrique stricte)\n")
    w("Fixes : (a) entrée vectorielle élargie (k=8) + **bonus si l'entité de la question est nommée** "
      "(sort les faits noyés) ; (b) **plancher de Certitude** pour les faits ≥2 sources.\n")
    w("| C-v2 | Changés | Stables | Global |")
    w("|---|---|---|---|")
    w(f"| AVANT fix | {S['C']['changé']:.0f}% | {S['C']['stable']:.0f}% | {S['C']['global']:.0f}% |")
    w(f"| **APRÈS fix** | **{Cnew['changé']:.0f}%** | **{Cnew['stable']:.0f}%** | **{Cnew['global']:.0f}%** |")
    w(f"\nDécomposition des erreurs restantes de C-v2 (après fix) : "
      f"🖊️ greffier **{greffier}** / 🏛️ architecte **{architecte}**.\n")
    w(f"**Menteur** : {menteur_pre}/5 avant plancher → **{menteur_post}/5 après** "
      f"(une vérité corroborée ne descend plus sous {config.V2_CERT_PLANCHER_CORROBORE}, "
      f"elle reste plus certaine qu'un mensonge récent à source unique).\n")

    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape_v2_5_rapport.md")
    with open(chemin, "w", encoding="utf-8") as fp:
        fp.write("\n".join(R))
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape_v2_5_data.json"), "w", encoding="utf-8") as fp:
        json.dump({"lenient": L, "stricte": S, "C_apres": Cnew,
                   "menteur_pre": menteur_pre, "menteur_post": menteur_post,
                   "greffier": greffier, "architecte": architecte}, fp, ensure_ascii=False, indent=2)

    dire("\n" + "=" * 84)
    dire(f" STRICTE (changés) : B={S['B']['changé']:.0f}% B′={S['Bp']['changé']:.0f}% "
         f"C-v2={S['C']['changé']:.0f}% → APRÈS fix C-v2={Cnew['changé']:.0f}%")
    dire(f" Global strict : B′={S['Bp']['global']:.0f}% C-v2 {S['C']['global']:.0f}%→{Cnew['global']:.0f}%")
    dire(f" Menteur {menteur_pre}/5 → {menteur_post}/5 | erreurs C-v2 après : greffier {greffier} / architecte {architecte}")
    dire("=" * 84)
    dire(f"\n Rapport : {chemin}\n Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
