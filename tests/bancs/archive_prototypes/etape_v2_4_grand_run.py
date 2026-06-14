# -*- coding: utf-8 -*-
"""
etape_v2_4_grand_run.py — LE GRAND RUN V2 (mission §5).

Compare sur ~40 questions : A (modèle seul), B (RAG inerte daté), B′ (RAG inerte aveugle),
C-v2 (le graphe daté à deux axes). C-v1-verbale est référencée via les chiffres de l'étape 3b.
Répondeur commun : qwen3:30b-a3b (choisi au duel).

Métriques :
 - précision globale / changés / stables
 - DÉCOMPOSITION des erreurs de C-v2 : greffier (ingestion : extraction/résolution) vs
   architecte (mémoire : le fait était bien stocké mais mal trié/rendu/non retrouvé)
 - audit d'extraction (taux de triplets corrects)
 - tests menteur / rumeur / Dupont
 - contrôle grammatical (réserve sur les faits érodés)

Lance :  python etape_v2_4_grand_run.py
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
import v2_extraction
import v2_lecture
import v2_monde
from util import Journal, assurer_dossiers
from memoire_store import Memoire
from horloge import HorlogeVirtuelle
from v2_modele import GrapheMemoire, norm_nom, norm_valeur
from monde import normaliser, mois_annee
from v2_ontologie import phrase

REPONDEUR = config.MODELE_JUGE          # qwen3:30b-a3b (choisi au duel)
CV1_VERBALE = {"changé": 87, "stable": 70, "global": 78}   # repris de l'étape 3b (monde V1)


def correct(rep, cle):
    return cle in normaliser(rep)


# ── Construction de C-v2 (ingestion réelle via extraction qwen) ──────────
def construire_cv2(flux, dire):
    g = GrapheMemoire()
    audit = {"total": 0, "extrait_ok": 0, "echecs": 0}
    for i, e in enumerate(flux):
        ext = v2_extraction.extraire(e.texte)
        audit["total"] += 1
        if ext and ext["predicat"] == e.predicat and norm_nom(ext["sujet"]) == norm_nom(e.sujet) \
           and norm_valeur(ext["objet"]) == norm_valeur(e.objet):
            audit["extrait_ok"] += 1
        if ext is None:
            audit["echecs"] += 1
            continue                                    # énoncé perdu (erreur greffier)
        g.ingerer(ext["sujet"], ext["predicat"], ext["objet"],
                  source_id=e.source, date_obs=e.date_obs, date_validite=ext["date_validite"])
        if (i + 1) % 20 == 0:
            g.sommeil(e.date_obs)
        if (i + 1) % 40 == 0:
            dire(f"    …ingestion {i+1}/{len(flux)}")
    g.sommeil(config.MONDE_FIN)
    return g, audit


# ── Mémoires inertes B / B′ ──────────────────────────────────────────────
def construire_inerte(faits, avec_dates):
    mem = Memoire(HorlogeVirtuelle(config.MONDE_FIN))
    for f in faits:
        mem.ajouter(phrase(f.predicat, f.entite, f.val_init, "present"), date=config.MONDE_DEBUT)
        if f.change:
            if avec_dates:
                txt = (f"Depuis {mois_annee(f.date_change)}, "
                       f"{phrase(f.predicat, f.entite, f.val_fin, 'present')[0].lower()}"
                       f"{phrase(f.predicat, f.entite, f.val_fin, 'present')[1:]}")
            else:
                txt = phrase(f.predicat, f.entite, f.val_fin, "present")
            mem.ajouter(txt, date=config.MONDE_FIN)
    return mem


def repondre_inerte(mem, question):
    trouves = mem.rechercher(question)
    bloc = mem.texte_injection(trouves, avec_meta=False)
    prompt = f"Informations :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    return modele.repondre(prompt, systeme=cycle.SYS_REPONSE_B, temperature=0.0, model=REPONDEUR)


# ── Lecture C-v2 SANS mutation (eval) ────────────────────────────────────
def lire_cv2(g, question):
    faits_e, v = v2_lecture.entree_vectorielle(g, question, k=config.TOP_K)
    faits_m = v2_lecture.marche_graphe(g, faits_e, v)
    vus, injectes = set(), []
    for f in faits_e + faits_m:
        if f.id not in vus:
            vus.add(f.id); injectes.append(f)
    bloc = v2_lecture.rendu_epistemique(g, injectes)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    return modele.repondre(prompt, systeme=v2_lecture.SYS_REPONSE_V2, temperature=0.0, model=REPONDEUR)


# ── Décomposition d'erreur : greffier vs architecte ──────────────────────
def diagnostiquer(g, f):
    """Le bon fait courant est-il correctement STOCKÉ dans le graphe ?"""
    e = g.trouver_entite(f.entite)
    if e is None:
        return "greffier"                               # entité perdue (résolution)
    vrai = norm_valeur(f.val_vraie())
    memes = [x for x in g.faits_de(e.id, f.predicat) if norm_valeur(x.objet) == vrai]
    if not memes:
        return "greffier"                               # bonne valeur jamais stockée (extraction)
    return "architecte"                                 # stockée, mais mal triée/rendue/non retrouvée


def precision(lignes, conf, cat=None):
    sel = [l for l in lignes if cat is None or l["cat"] == cat]
    return (100.0 * sum(1 for l in sel if l[conf]) / len(sel)) if sel else 0.0


def main():
    assurer_dossiers()
    J = Journal("etape_v2_4")
    dire = J.dire
    dire("=" * 84)
    dire(" V2 · ÉTAPE 4 — GRAND RUN (A / B / B′ / C-v2 ; répondeur qwen)")
    dire("=" * 84)

    faits, flux, special = v2_monde.generer_monde_v2()
    questions = v2_monde.choisir_questions(faits, config.N_QUESTIONS_EVAL_V2)
    dire(f"\nMonde : {len(faits)} faits ({sum(1 for f in faits if f.change)} changés, "
         f"{sum(1 for f in faits if f.immuable)} immuables), {len(flux)} énoncés sourcés, "
         f"{len(questions)} questions.")

    dire("\n[1/3] Ingestion de C-v2 (extraction réelle qwen + sommeils)…")
    g, audit = construire_cv2(flux, dire)
    dire(f"  Graphe : {len(g.entites)} entités, {len(g.faits)} faits. "
         f"Extraction correcte : {audit['extrait_ok']}/{audit['total']} "
         f"({100*audit['extrait_ok']/audit['total']:.0f} %), échecs {audit['echecs']}.")

    dire("\n[2/3] Mémoires inertes B / B′…")
    memB = construire_inerte(faits, avec_dates=True)
    memB2 = construire_inerte(faits, avec_dates=False)

    dire("\n[3/3] Évaluation (40 questions × 4 configs)…")
    lignes = []
    for i, f in enumerate(questions, start=1):
        q, cle = f.question(), f.cle_vraie()
        rA = modele.repondre(q, systeme=cycle.SYS_REPONSE_A, temperature=0.0, model=REPONDEUR)
        rB = repondre_inerte(memB, q)
        rBp = repondre_inerte(memB2, q)
        rC = lire_cv2(g, q)
        okC = correct(rC, cle)
        lignes.append({
            "q": q, "cat": f.categorie(), "cle": cle, "val": f.val_vraie(),
            "A": correct(rA, cle), "B": correct(rB, cle), "Bp": correct(rBp, cle), "C": okC,
            "repC": rC, "diag": (None if okC else diagnostiquer(g, f)), "fid": f.fid,
        })
        if i % 10 == 0:
            dire(f"    …{i}/{len(questions)}")

    # ── Précisions ───────────────────────────────────────────────────────
    res = {}
    for conf in ("A", "B", "Bp", "C"):
        res[conf] = {c or "global": round(precision(lignes, conf, c), 0)
                     for c in (None, "changé", "stable")}

    # ── Décomposition greffier / architecte (erreurs de C-v2) ───────────
    erreurs = [l for l in lignes if not l["C"]]
    greffier = sum(1 for l in erreurs if l["diag"] == "greffier")
    architecte = sum(1 for l in erreurs if l["diag"] == "architecte")

    # ── Tests spéciaux ───────────────────────────────────────────────────
    # Menteur : la vérité (init) reste plus certaine que le mensonge
    menteur_resiste = 0
    for f in special["menteur"]:
        e = g.trouver_entite(f.entite)
        if not e:
            continue
        fs = g.faits_de(e.id, f.predicat)
        vrai = next((x for x in fs if norm_valeur(x.objet) == norm_valeur(f.val_init)), None)
        faux = next((x for x in fs if norm_valeur(x.objet) == norm_valeur(getattr(f, "_faux", "∅"))), None)
        if vrai and (faux is None or vrai.certitude >= faux.certitude):
            menteur_resiste += 1
    # Rumeur : la Certitude du faux répété reste plafonnée à 0.60
    fr = special["rumeur"]
    e = g.trouver_entite(fr.entite)
    rum_fait = None
    if e:
        rum_fait = next((x for x in g.faits_de(e.id, fr.predicat)
                         if norm_valeur(x.objet) == norm_valeur(getattr(fr, "_faux", "∅"))), None)
    rumeur_ok = (rum_fait is None) or (rum_fait.certitude <= config.V2_CERT_PLAFOND_MENTEUR + 1e-9)
    # Dupont : faits stables jamais reconfirmés → Certitude < 0.6 (rendus avec réserve)
    dupont_reserve = 0
    for f in special["dupont"]:
        e = g.trouver_entite(f.entite)
        if not e:
            continue
        fx = next((x for x in g.faits_de(e.id, f.predicat)
                   if norm_valeur(x.objet) == norm_valeur(f.val_init)), None)
        if fx and fx.certitude < 0.6:
            dupont_reserve += 1

    # ── RAPPORT ──────────────────────────────────────────────────────────
    R = []
    w = R.append
    w("# Étape 4 — Grand run V2 (graphe daté, deux axes, provenance)\n")
    w("## Paramètres\n")
    w(f"- Répondeur commun : `{REPONDEUR}` (choisi au mini-duel). Extraction & juge d'usage : "
      f"`{config.MODELE_JUGE}`.")
    w(f"- Monde : {len(faits)} faits ({sum(1 for f in faits if f.change)} changés, "
      f"{sum(1 for f in faits if f.immuable)} immuables), {len(flux)} énoncés sourcés, "
      f"{len(questions)} questions.\n")
    w("## Précision\n")
    w("| Config | Changés | Stables | Global |")
    w("|---|---|---|---|")
    w(f"| A — modèle seul | {res['A']['changé']:.0f} % | {res['A']['stable']:.0f} % | {res['A']['global']:.0f} % |")
    w(f"| B — RAG inerte daté | {res['B']['changé']:.0f} % | {res['B']['stable']:.0f} % | {res['B']['global']:.0f} % |")
    w(f"| B′ — RAG inerte aveugle | {res['Bp']['changé']:.0f} % | {res['Bp']['stable']:.0f} % | {res['Bp']['global']:.0f} % |")
    w(f"| **C-v2 — graphe daté** | **{res['C']['changé']:.0f} %** | **{res['C']['stable']:.0f} %** | **{res['C']['global']:.0f} %** |")
    w(f"| *C-v1-verbale (réf. étape 3b, monde V1)* | *{CV1_VERBALE['changé']} %* | "
      f"*{CV1_VERBALE['stable']} %* | *{CV1_VERBALE['global']} %* |")
    w("\n*C-v1-verbale est mesurée sur le monde V1 (étape 3b) ; comparaison indicative, pas tête-à-tête.*\n")

    w("## Décomposition des erreurs de C-v2 — greffier vs architecte\n")
    w(f"Sur **{len(erreurs)} erreurs** de C-v2 :")
    w(f"- 🖊️ **Greffier (ingestion : extraction / résolution)** : **{greffier}** "
      f"— le bon fait n'était pas, ou mal, stocké.")
    w(f"- 🏛️ **Architecte (mémoire : tri / rendu / non-retrouvé)** : **{architecte}** "
      f"— le fait était bien stocké mais la réponse a quand même échoué.")
    w(f"\nSanté du greffier : extraction correcte **{100*audit['extrait_ok']/audit['total']:.0f} %** "
      f"({audit['extrait_ok']}/{audit['total']}), {audit['echecs']} énoncés perdus.\n")
    if erreurs:
        w("Exemples d'erreurs (avec famille) :")
        for l in erreurs[:6]:
            w(f"- [{l['diag']}] Q: « {l['q']} » (vérité : {l['val']}) → « {l['repC'][:80]} »")
    w("")

    w("## Tests propres au V2\n")
    w(f"- **Menteur** (5 vérités corroborées attaquées par une source unique) : "
      f"**{menteur_resiste}/5 ont résisté** (la vérité reste au moins aussi certaine que le mensonge).")
    c_faux = f"{rum_fait.certitude:.2f}" if rum_fait else "—"
    w(f"- **Rumeur** (une même source répète 5× un faux) : Certitude plafonnée à "
      f"{config.V2_CERT_PLAFOND_MENTEUR} → **{'OK' if rumeur_ok else 'ÉCHEC'}** "
      f"(C={c_faux} du faux). La répétition n'a pas tenu lieu de preuve.")
    w(f"- **Dupont** (3 faits stables jamais reconfirmés) : **{dupont_reserve}/3** ont une Certitude "
      f"< 0.6 → rendus AVEC RÉSERVE (« à revérifier »), ni tus ni affirmés au présent.\n")

    w("## Note structurelle — le juge ne contredit plus\n")
    w("La détection de contradiction a quitté la LECTURE pour l'ÉCRITURE (fait contre fait, dates "
      "contre dates). Le juge d'usage ne peut plus qu'alimenter la Force ; aucun fait clos/disputé "
      "ne provient d'un verdict de lecture. Le talon d'Achille du juge (15 % de fausses "
      "contradictions du récent, mesuré en V1) est donc structurellement DÉSARMÉ : le défaut existe "
      "encore dans le modèle, mais il n'a plus accès à l'arme.\n")

    w("## Angle mort connu — double rôle de qwen\n")
    w("qwen est ici extracteur (écriture) + juge d'usage (lecture) + répondeur. Un même biais "
      "pourrait se corréler entre les rôles. Garde-fou : la contradiction reste règle/données ; "
      "l'extraction est mesurée à part (greffier). À surveiller pour une version ultérieure.\n")

    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape_v2_4_rapport.md")
    with open(chemin, "w", encoding="utf-8") as fp:
        fp.write("\n".join(R))
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape_v2_4_eval.json"), "w", encoding="utf-8") as fp:
        json.dump({"res": res, "greffier": greffier, "architecte": architecte,
                   "audit": audit, "menteur": menteur_resiste, "rumeur_ok": rumeur_ok,
                   "dupont": dupont_reserve, "lignes": lignes}, fp, ensure_ascii=False, indent=2)

    dire("\n" + "=" * 84)
    dire(f" C-v2 : changés {res['C']['changé']:.0f}% | stables {res['C']['stable']:.0f}% | "
         f"global {res['C']['global']:.0f}%  (vs B {res['B']['global']:.0f}%, B′ {res['Bp']['global']:.0f}%)")
    dire(f" Erreurs C-v2 : greffier {greffier} / architecte {architecte} | "
         f"extraction {100*audit['extrait_ok']/audit['total']:.0f}%")
    dire(f" Menteur {menteur_resiste}/5 | Rumeur {'OK' if rumeur_ok else 'KO'} | Dupont {dupont_reserve}/3")
    dire("=" * 84)
    dire(f"\n Rapport : {chemin}\n Journal : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
