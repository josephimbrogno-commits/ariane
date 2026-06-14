# -*- coding: utf-8 -*-
"""
etape1b_comparaison_juges.py — DUEL DE JUGES (étape 1, option 3).

On rejoue EXACTEMENT les mêmes 30 souvenirs et 10 questions que l'étape 1,
mais à chaque question on interroge DEUX juges sur un contexte IDENTIQUE :

  • Juge A = llama3.1:8b      (celui du « run précédent »)
  • Juge B = qwen3:30b-a3b    (juge plus costaud à tester)

Méthode (pour une comparaison honnête) :
  - mêmes souvenirs, mêmes questions (importés de etape1_micro) ;
  - réponse du modèle en température 0 (reproductible) ;
  - à chaque question, les DEUX juges voient le MÊME contexte
    (mêmes souvenirs, mêmes confiances, même réponse) ;
  - la trajectoire des confiances est pilotée par le juge A (= reproduit le run
    précédent), de sorte que le juge B est évalué dans la même situation.

Sortie : comparaison verdict par verdict + bilan des désaccords.

Lance :  python etape1b_comparaison_juges.py
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
from horloge import HorlogeVirtuelle
from memoire_store import Memoire
from util import Journal
import cycle
import modele

# On réutilise STRICTEMENT les mêmes données que l'étape 1.
from etape1_micro import SOUVENIRS, QUESTIONS, JOURS_ENTRE_QUESTIONS

JUGE_A = "llama3.1:8b"      # run précédent
JUGE_B = "qwen3:30b-a3b"    # nouveau juge à tester

MARQUE = {"CONFIRME": "✓", "CONTREDIT": "✗", "NON_UTILISE": "·", "INCERTAIN": "?"}


def court(txt, n=46):
    return (txt[: n - 1] + "…") if len(txt) > n else txt.ljust(n)


def juger_qwen(question, reponse, trouves):
    """Juge B, avec repli si le paramètre think n'est pas accepté."""
    try:
        return cycle.juger(question, reponse, trouves, model=JUGE_B, think=False)
    except Exception:
        # Repli : sans le paramètre think (certaines versions d'Ollama).
        return cycle.juger(question, reponse, trouves, model=JUGE_B)


def main():
    J = Journal("etape1b_duel_juges")
    dire = J.dire

    dire("=" * 92)
    dire(" ÉTAPE 1b — DUEL DE JUGES sur les MÊMES 30 souvenirs / 10 questions")
    dire(f"   Juge A (run précédent) : {JUGE_A}")
    dire(f"   Juge B (nouveau)       : {JUGE_B}")
    dire("   Contexte identique pour les deux juges à chaque question. Réponses en T=0.")
    dire("=" * 92)

    horloge = HorlogeVirtuelle(config.DATE_DEBUT)
    mem = Memoire(horloge)
    for txt in SOUVENIRS:
        mem.ajouter(txt)
    dire(f"\n→ {len(SOUVENIRS)} souvenirs créés (confiance {config.CONFIANCE_DEPART}).\n")
    dire("   (1er appel à qwen3 : chargement en VRAM, peut prendre ~15 s…)\n")

    # Compteurs globaux
    total = 0
    accords = 0
    desaccords = []          # liste de dict détaillés
    # Matrice de confusion A->B (qui dit quoi quand l'autre dit autre chose)
    par_verdict_A = {}

    for n, question in enumerate(QUESTIONS, start=1):
        mem.eroder()
        trouves = mem.rechercher(question)

        bloc = mem.texte_injection(trouves, avec_meta=True)
        prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
        reponse = modele.repondre(prompt, systeme=cycle.SYS_REPONSE_C, temperature=0.0)

        vA = cycle.juger(question, reponse, trouves, model=JUGE_A)
        vB = juger_qwen(question, reponse, trouves)

        dire("─" * 92)
        dire(f"QUESTION {n}/10 — [horloge {horloge.texte()}]  « {question} »")
        dire(f"   Réponse du modèle (T=0) : « {reponse} »")
        dire(f"   {'souvenir':47}| conf | juge A ({JUGE_A:12}) | juge B ({JUGE_B})")
        dire("   " + "-" * 88)

        for s, _ in trouves:
            a = vA.get(s.id, {"verdict": "INCERTAIN", "justification": "(non rendu)"})
            b = vB.get(s.id, {"verdict": "INCERTAIN", "justification": "(non rendu)"})
            va, vb = a["verdict"], b["verdict"]
            total += 1
            par_verdict_A.setdefault(va, {"accord": 0, "desaccord": 0})
            meme = (va == vb)
            if meme:
                accords += 1
                par_verdict_A[va]["accord"] += 1
                drapeau = "   accord"
            else:
                par_verdict_A[va]["desaccord"] += 1
                drapeau = "  ≠ DÉSACCORD"
                desaccords.append({
                    "question": question,
                    "souvenir_id": s.id,
                    "souvenir": s.contenu,
                    "confiance": round(s.confiance, 2),
                    "juge_A": va, "justif_A": a["justification"],
                    "juge_B": vb, "justif_B": b["justification"],
                })
            dire(f"   #{s.id:<2} {court(s.contenu)}| {s.confiance:.2f} | "
                 f"{MARQUE.get(va,'?')} {va:<11} | {MARQUE.get(vb,'?')} {vb:<11}{drapeau}")

            # La trajectoire des confiances est pilotée par le juge A (= run précédent).
            mem.appliquer_verdict(s, va)

        mem.cycles += 1
        horloge.avancer(JOURS_ENTRE_QUESTIONS)
        dire("")

    # ── BILAN ────────────────────────────────────────────────────────────
    dire("=" * 92)
    dire(" BILAN DU DUEL")
    dire("=" * 92)
    taux = 100.0 * accords / total if total else 0
    dire(f"   Verdicts comparés : {total}")
    dire(f"   Accords           : {accords}  ({taux:.0f} %)")
    dire(f"   Désaccords        : {len(desaccords)}  ({100 - taux:.0f} %)")
    dire("")
    dire("   Répartition des désaccords selon ce qu'a dit le juge A :")
    for va, c in sorted(par_verdict_A.items()):
        if c["desaccord"]:
            dire(f"      quand A dit {va:<11}: {c['desaccord']} désaccord(s) "
                 f"sur {c['accord'] + c['desaccord']}")
    dire("")

    dire("─" * 92)
    dire(" DÉTAIL DES DÉSACCORDS (à toi de juger qui a raison) :")
    dire("─" * 92)
    if not desaccords:
        dire("   Aucun désaccord : les deux juges sont d'accord sur tout.")
    for d in desaccords:
        dire(f"\n   • Q: « {d['question']} »")
        dire(f"     Souvenir #{d['souvenir_id']} (conf {d['confiance']}) : {d['souvenir']}")
        dire(f"       Juge A {JUGE_A:14} → {d['juge_A']:<11} : {d['justif_A']}")
        dire(f"       Juge B {JUGE_B:14} → {d['juge_B']:<11} : {d['justif_B']}")

    # Sauvegarde JSON
    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape1b_comparaison_juges.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(
            {"total": total, "accords": accords, "taux_accord_pct": round(taux, 1),
             "desaccords": desaccords},
            f, ensure_ascii=False, indent=2,
        )
    dire("")
    dire("=" * 92)
    dire(f" ✅ Duel terminé. Journal : {J.chemin}")
    dire(f"    Détails JSON : {chemin}")
    dire("=" * 92)
    J.fermer()


if __name__ == "__main__":
    main()
