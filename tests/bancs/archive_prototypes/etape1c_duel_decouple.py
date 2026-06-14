# -*- coding: utf-8 -*-
"""
etape1c_duel_decouple.py — JUGE DÉCOUPLÉ : ablation en DEUX TEMPS + 2 pièges.

On isole l'effet de chaque correction sur le juge découplé :
  • PHASE A = dates corrigées + prompt V1 (original).
  • PHASE B = dates corrigées + prompt V2 (durci : « le récent gagne par la DATE »,
              « la réponse peut être fausse », et surtout « ANCIEN n'est pas PÉRIMÉ »).
Les deux phases voient EXACTEMENT le même contexte (mémoire GELÉE : aucune mise à jour
entre les questions), si bien que le SEUL facteur qui change de A à B est le prompt.

Jeu de test = les 30 souvenirs / 10 questions de l'étape 1, datés selon la chronologie,
+ DEUX PIÈGES autour de l'entité « Velora » :
  • #31 « Velora fondée en 1998 » : ANCIEN mais toujours VRAI → ne doit JAMAIS être contredit.
  • #32 Brest (ancien siège) / #33 Nantes (depuis 2026) : la règle « le récent gagne » ne doit
    jouer qu'ENTRE ces deux-là (même attribut = siège), SANS toucher #31 (attribut = fondation).

Vérifs automatiques : (1) les 5 cas catastrophiques de qwen disparaissent ;
(2) aucun nouveau verdict catastrophique ; (3) les 2 pièges sont déjoués.

Lance :  python etape1c_duel_decouple.py
"""

import json
import os
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
from horloge import HorlogeVirtuelle
from memoire_store import Memoire
from util import Journal
import cycle
import modele

from etape1_micro import SOUVENIRS, QUESTIONS

JUGE_A = "llama3.1:8b"
JUGE_B = "qwen3:30b-a3b"
MARQUE = {"CONFIRME": "✓", "CONTREDIT": "✗", "NON_UTILISE": "·", "INCERTAIN": "?"}

# ── DEUX PIÈGES ajoutés au jeu de test (ids 31..34) ───────────────────────
SOUV_PIEGES = [
    "L'entreprise Velora a été fondée en 1998.",            # 31 STABLE — ancien MAIS vrai
    "Le siège de Velora se trouve à Brest.",                # 32 PÉRIMÉ — ancien siège
    "Depuis 2026, le siège de Velora se trouve à Nantes.",  # 33 ACTUEL — nouveau siège
    "Velora fabrique des batteries.",                       # 34 STABLE — contexte
]
Q_PIEGES = [
    "Où se trouve le siège de Velora aujourd'hui ?",        # Q11 : récent (Nantes) gagne sur Brest
    "En quelle année l'entreprise Velora a-t-elle été fondée ?",  # Q12 : #31 utilisé, jamais contredit
]
TOUS_SOUV = SOUVENIRS + SOUV_PIEGES
TOUTES_Q = QUESTIONS + Q_PIEGES

# ── VÉRITÉ-TERRAIN (par id), pièges inclus ───────────────────────────────
PERIME = {1, 5, 7, 11, 16, 18, 25, 32}
ACTUEL = {2, 6, 8, 12, 17, 19, 26, 33}
STABLE = {3, 4, 9, 10, 13, 14, 15, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31, 34}
ID_ANCIEN_VRAI = 31  # le piège « ancien mais vrai » : ne doit JAMAIS être CONTREDIT

# ── Dates reflétant la chronologie ───────────────────────────────────────
DATE_ANCIENNE = datetime(2024, 1, 1)       # faits dépassés / stables ordinaires
DATE_RECENTE = datetime(2026, 3, 1)        # faits « actuels » (nouvelles valeurs)
DATE_TRES_ANCIENNE = datetime(2019, 1, 1)  # #31 : volontairement très ancien (pour stresser le piège)
DATES_SPECIALES = {31: DATE_TRES_ANCIENNE}


def date_pour(i):
    if i in DATES_SPECIALES:
        return DATES_SPECIALES[i]
    return DATE_RECENTE if i in ACTUEL else DATE_ANCIENNE


def nature(sid):
    if sid in PERIME:
        return "PÉRIMÉ"
    if sid in ACTUEL:
        return "ACTUEL"
    return "STABLE"


def est_catastrophe(sid, verdict):
    """Catastrophe = renforcer un périmé, ou punir un fait vrai (actuel ou stable)."""
    if verdict == "CONFIRME" and sid in PERIME:
        return True
    if verdict == "CONTREDIT" and (sid in ACTUEL or sid in STABLE):
        return True
    return False


# Les 5 cas catastrophiques produits par qwen au tout premier duel (sans dates).
CAS_PRECEDENTS = [
    (1, 2, "CONTREDIT"), (1, 1, "CONFIRME"),
    (5, 19, "CONTREDIT"), (5, 18, "CONFIRME"),
    (2, 6, "CONTREDIT"),
]


def court(txt, n=46):
    return (txt[: n - 1] + "…") if len(txt) > n else txt.ljust(n)


def juger(question, reponse, trouves, model, systeme, think=None):
    """Appel juge robuste (modele.juger gère déjà retries + repli)."""
    return cycle.juger(question, reponse, trouves, model=model, think=think,
                       systeme=systeme, montrer_confiance=False)


def main():
    J = Journal("etape1c_ablation")
    dire = J.dire

    dire("=" * 96)
    dire(" ÉTAPE 1c — JUGE DÉCOUPLÉ : ablation V1→V2 (mémoire gelée) + 2 pièges Velora")
    dire(f"   Juge A : {JUGE_A}   |   Juge B : {JUGE_B}   |   {len(TOUS_SOUV)} souvenirs, "
         f"{len(TOUTES_Q)} questions")
    dire("=" * 96)

    # Mémoire GELÉE : on la construit une fois, on n'y touche plus (ni érosion ni verdicts).
    horloge = HorlogeVirtuelle(config.DATE_DEBUT)
    mem = Memoire(horloge)
    for i, txt in enumerate(TOUS_SOUV, start=1):
        mem.ajouter(txt, date=date_pour(i))

    # Contextes précalculés (identiques pour A et B) : recherche + réponse en T=0.
    dire("\n— CONTEXTES (réponses du modèle en T=0, mémoire gelée) —")
    contextes = []
    for qi, q in enumerate(TOUTES_Q, start=1):
        trouves = mem.rechercher(q)
        bloc = mem.texte_injection(trouves, avec_meta=True)
        prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {q}\nRéponse :"
        reponse = modele.repondre(prompt, systeme=cycle.SYS_REPONSE_C, temperature=0.0)
        contextes.append((q, trouves, reponse))
        dire(f"  Q{qi}: « {q} »\n       → « {reponse} »")

    # ── Une phase = un prompt de juge, appliqué aux contextes gelés ──────
    def run_phase(nom, systeme):
        dire("\n" + "=" * 96)
        dire(f" {nom}")
        dire("=" * 96)
        verdicts = {}
        catA, catB = [], []
        for qi, (q, trouves, reponse) in enumerate(contextes, start=1):
            vA = juger(q, reponse, trouves, JUGE_A, systeme)
            vB = juger(q, reponse, trouves, JUGE_B, systeme, think=False)
            dire("─" * 96)
            dire(f"Q{qi} — « {q} »")
            dire(f"   {'souvenir':47}|nature| A ({JUGE_A:11})| B ({JUGE_B})")
            for s, _ in trouves:
                a = vA.get(s.id, {"verdict": "INCERTAIN"})["verdict"]
                b = vB.get(s.id, {"verdict": "INCERTAIN"})["verdict"]
                verdicts[(qi, s.id)] = (a, b)
                cA, cB = est_catastrophe(s.id, a), est_catastrophe(s.id, b)
                if cA:
                    catA.append((qi, s.id, a))
                if cB:
                    catB.append((qi, s.id, b))
                alerte = ""
                if cA or cB:
                    alerte = "  ⚠ CATA(" + ("A" if cA else "") + ("B" if cB else "") + ")"
                pic31 = " ←piège" if s.id == ID_ANCIEN_VRAI else ""
                dire(f"   #{s.id:<2} {court(s.contenu)}|{nature(s.id):^6}| "
                     f"{MARQUE.get(a,'?')} {a:<11}| {MARQUE.get(b,'?')} {b:<11}{alerte}{pic31}")
        return {"verdicts": verdicts, "catA": catA, "catB": catB}

    resA = run_phase("PHASE A — dates corrigées + prompt V1 (ORIGINAL)", cycle.SYS_JUGE_DECOUPLE_V1)
    resB = run_phase("PHASE B — dates corrigées + prompt V2 (DURCI)", cycle.SYS_JUGE_DECOUPLE_V2)

    # ── SYNTHÈSE DE L'ABLATION ───────────────────────────────────────────
    dire("\n" + "=" * 96)
    dire(" SYNTHÈSE DE L'ABLATION — nombre de verdicts CATASTROPHIQUES")
    dire("=" * 96)
    dire(f"   {'':24}| Juge A ({JUGE_A}) | Juge B ({JUGE_B})")
    dire(f"   Phase A (prompt V1)     |        {len(resA['catA']):<2}          |        {len(resA['catB']):<2}")
    dire(f"   Phase B (prompt V2)     |        {len(resB['catA']):<2}          |        {len(resB['catB']):<2}")
    dire("")
    for nom, res in [("A (V1)", resA), ("B (V2)", resB)]:
        for jn, cat in [("A " + JUGE_A, res["catA"]), ("B " + JUGE_B, res["catB"])]:
            if cat:
                dire(f"   Catastrophes phase {nom}, juge {jn} :")
                for (qi, sid, v) in cat:
                    txt = TOUS_SOUV[sid - 1]
                    dire(f"       ⚠ Q{qi} #{sid} ({nature(sid)}) → {v} : {txt}")

    # ── VÉRIF 1 : les 5 cas catastrophiques de qwen ──────────────────────
    dire("\n" + "=" * 96)
    dire(" VÉRIF 1 — les 5 cas catastrophiques de qwen (1er duel) : V1 puis V2")
    dire("=" * 96)
    cas_ok_V2 = True
    for (qi, sid, mauvais) in CAS_PRECEDENTS:
        v1 = resA["verdicts"].get((qi, sid), ("?", "?"))[1]
        v2 = resB["verdicts"].get((qi, sid), ("?", "?"))[1]
        ok_v2 = not est_catastrophe(sid, v2)
        cas_ok_V2 = cas_ok_V2 and ok_v2
        dire(f"   Q{qi} #{sid} ({nature(sid)}) — 1er duel={mauvais} → V1={v1} → V2={v2}  "
             f"{'✅' if ok_v2 else '❌'}")

    # ── VÉRIF 2 : les 2 pièges ───────────────────────────────────────────
    dire("\n" + "=" * 96)
    dire(" VÉRIF 2 — les 2 pièges « ancien ≠ périmé »")
    dire("=" * 96)
    # Piège 1 : #31 ne doit JAMAIS être CONTREDIT (aucune question, aucune phase, aucun juge)
    viol31 = []
    for nomp, res in [("A/V1", resA), ("B/V2", resB)]:
        for (qi, sid), (a, b) in res["verdicts"].items():
            if sid == ID_ANCIEN_VRAI:
                if a == "CONTREDIT":
                    viol31.append((nomp, "A", qi, a))
                if b == "CONTREDIT":
                    viol31.append((nomp, "B", qi, b))
    dire(f"   Piège 1 — #{ID_ANCIEN_VRAI} « Velora fondée en 1998 » (ancien mais vrai) "
         f"contredit à tort ?")
    if not viol31:
        dire("      ✅ Jamais contredit (toutes phases, tous juges).")
    else:
        for (nomp, jg, qi, v) in viol31:
            dire(f"      ❌ {nomp} juge {jg} Q{qi} → {v}")

    # Piège 2 : à la Q11 (siège Velora), récent (#33 Nantes) gagne, ancien siège (#32 Brest)
    # contredit, et #31 (fondation) intact.
    dire("   Piège 2 — Q11 « siège de Velora » : Brest(#32 périmé)→CONTREDIT, "
         "Nantes(#33 actuel)→pas contredit, fondation(#31)→intacte")
    q11 = len(QUESTIONS) + 1  # 11
    for nomp, res in [("A/V1", resA), ("B/V2", resB)]:
        v = res["verdicts"]
        b32 = v.get((q11, 32), ("?", "?"))[1]
        b33 = v.get((q11, 33), ("?", "?"))[1]
        b31 = v.get((q11, 31), ("?", "?"))[1]
        ok = (b32 == "CONTREDIT") and (b33 != "CONTREDIT") and (b31 != "CONTREDIT")
        dire(f"      {nomp} (juge B) : #32={b32}, #33={b33}, #31={b31}  "
             f"{'✅' if ok else '⚠'}")

    # ── VERDICT GLOBAL ───────────────────────────────────────────────────
    dire("\n" + "=" * 96)
    succes = (len(resB["catB"]) == 0) and cas_ok_V2 and (not viol31)
    if succes:
        dire(" ✅ SUCCÈS (Phase B / juge qwen) : 0 catastrophe, 5 cas corrigés, pièges déjoués.")
    else:
        dire(" ⚠ RÉSULTAT MITIGÉ — voir détails ci-dessus (le rapport expliquera pourquoi).")
    dire("=" * 96)

    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape1c_ablation.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({
            "phaseA_catA": len(resA["catA"]), "phaseA_catB": len(resA["catB"]),
            "phaseB_catA": len(resB["catA"]), "phaseB_catB": len(resB["catB"]),
            "cas_precedents_ok_V2": cas_ok_V2,
            "piege1_violations": viol31,
            "succes": succes,
        }, f, ensure_ascii=False, indent=2)
    dire(f"\n Journal : {J.chemin}\n Détails JSON : {chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
