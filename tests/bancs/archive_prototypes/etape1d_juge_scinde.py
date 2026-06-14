# -*- coding: utf-8 -*-
"""
etape1d_juge_scinde.py — JUGE SCINDÉ (deux détecteurs étanches) + cas limite.

Le juge est scindé en deux mini-appels qui ne peuvent pas se contaminer :
  • détecteur de CONFLITS  : ne voit QUE les souvenirs → produit les CONTREDIT (le monde) ;
  • détecteur d'USAGE      : voit la réponse → produit les CONFIRME (l'opinion).
Règle de combinaison : « LE CONFLIT BAT L'USAGE » (le monde bat l'opinion).

On teste (même jeu daté + pièges que l'étape 1c, juge = qwen3:30b-a3b) :
  1. 0 verdict catastrophique ?
  2. les 2 pièges « ancien ≠ périmé » tiennent-ils ?
  3. CAS LIMITE : si la réponse s'appuie sur un fait PÉRIMÉ (donc usage=UTILISE) ALORS qu'un
     fait plus récent le contredit (conflit=CONTREDIT), le verdict final est-il bien CONTREDIT ?

Si 0 catastrophe + pièges tenus + cas limite OK → on adopte le juge scindé.

Lance :  python etape1d_juge_scinde.py
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

# Réutilise STRICTEMENT le jeu de test daté + pièges de l'étape 1c.
from etape1c_duel_decouple import (
    TOUS_SOUV, TOUTES_Q, QUESTIONS, PERIME, ACTUEL, STABLE,
    ID_ANCIEN_VRAI, date_pour, nature, est_catastrophe, court,
)

JUGE = "qwen3:30b-a3b"
MARQUE = {"CONFIRME": "✓", "CONTREDIT": "✗", "NON_UTILISE": "·", "INCERTAIN": "?"}


def main():
    J = Journal("etape1d_juge_scinde")
    dire = J.dire

    dire("=" * 98)
    dire(" ÉTAPE 1d — JUGE SCINDÉ (conflits ⟂ usage) ; règle : LE CONFLIT BAT L'USAGE")
    dire(f"   Juge : {JUGE}   |   {len(TOUS_SOUV)} souvenirs datés, {len(TOUTES_Q)} questions")
    dire("=" * 98)

    horloge = HorlogeVirtuelle(config.DATE_DEBUT)
    mem = Memoire(horloge)
    for i, txt in enumerate(TOUS_SOUV, start=1):
        mem.ajouter(txt, date=date_pour(i))

    catastrophes = []
    verdicts = {}

    for qi, q in enumerate(TOUTES_Q, start=1):
        trouves = mem.rechercher(q)
        bloc = mem.texte_injection(trouves, avec_meta=True)
        prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {q}\nRéponse :"
        reponse = modele.repondre(prompt, systeme=cycle.SYS_REPONSE_C, temperature=0.0)

        detail = cycle.juger_scinde(q, reponse, trouves, model=JUGE, think=False)

        dire("─" * 98)
        dire(f"Q{qi} — « {q} »")
        dire(f"   Réponse (T=0) : « {reponse} »")
        dire(f"   {'souvenir':47}|nature| verdict      (conflit / usage)")
        for s, _ in trouves:
            d = detail[s.id]
            v = d["verdict"]
            if est_catastrophe(s.id, v):
                catastrophes.append((qi, s.id, v))
            verdicts[(qi, s.id)] = v
            alerte = "  ⚠ CATA" if est_catastrophe(s.id, v) else ""
            pic = " ←piège" if s.id == ID_ANCIEN_VRAI else ""
            dire(f"   #{s.id:<2} {court(s.contenu)}|{nature(s.id):^6}| "
                 f"{MARQUE.get(v,'?')} {v:<11} (conflit={d['conflit']:<9} usage={d['usage']}){alerte}{pic}")

    # ── VÉRIF catastrophes ───────────────────────────────────────────────
    dire("\n" + "=" * 98)
    dire(f" VÉRIF 1 — verdicts catastrophiques : {len(catastrophes)}")
    for (qi, sid, v) in catastrophes:
        dire(f"     ⚠ Q{qi} #{sid} ({nature(sid)}) → {v} : {TOUS_SOUV[sid - 1]}")

    # ── VÉRIF pièges ─────────────────────────────────────────────────────
    dire("\n VÉRIF 2 — pièges « ancien ≠ périmé »")
    viol31 = [(qi, v) for (qi, sid), v in verdicts.items()
              if sid == ID_ANCIEN_VRAI and v == "CONTREDIT"]
    if not viol31:
        dire(f"   Piège 1 — #{ID_ANCIEN_VRAI} « Velora fondée en 1998 » jamais contredit : ✅")
    else:
        dire(f"   Piège 1 — #{ID_ANCIEN_VRAI} contredit à tort : ❌ {viol31}")
    q11 = len(QUESTIONS) + 1
    b32 = verdicts.get((q11, 32), "?")
    b33 = verdicts.get((q11, 33), "?")
    b31 = verdicts.get((q11, 31), "?")
    piege2_ok = (b32 == "CONTREDIT") and (b33 != "CONTREDIT") and (b31 != "CONTREDIT")
    dire(f"   Piège 2 — Q11 siège Velora : #32(Brest)={b32}, #33(Nantes)={b33}, "
         f"#31(fondation)={b31}  {'✅' if piege2_ok else '⚠'}")

    # ── VÉRIF 3 — CAS LIMITE : conflit vs usage sur le même souvenir ──────
    dire("\n VÉRIF 3 — CAS LIMITE « le conflit bat l'usage »")
    q_h = "À quelle heure ferme la bibliothèque Halgren ?"
    trouves_h = mem.rechercher(q_h)
    reponse_forcee = "La bibliothèque Halgren ferme à 18h."  # s'appuie sur le fait PÉRIMÉ (#18)
    dire(f"   Question : « {q_h} »")
    dire(f"   Réponse FORCÉE (s'appuie sur le périmé) : « {reponse_forcee} »")
    detail_h = cycle.juger_scinde(q_h, reponse_forcee, trouves_h, model=JUGE, think=False)
    d18 = detail_h.get(18, {"verdict": "?", "conflit": "?", "usage": "?"})
    dire(f"   #18 « ...ferme à 18h » (PÉRIMÉ) → conflit={d18['conflit']}, "
         f"usage={d18['usage']}, VERDICT FINAL={d18['verdict']}")
    tie_ok = (d18["verdict"] == "CONTREDIT")
    if tie_ok and d18["usage"] == "UTILISE":
        dire("   ✅ Le souvenir périmé est UTILISÉ par la réponse MAIS le conflit l'emporte → CONTREDIT.")
    elif tie_ok:
        dire("   ✅ Verdict CONTREDIT (le conflit l'emporte), même si l'usage n'a pas été détecté UTILISE.")
    else:
        dire("   ❌ Le verdict n'est pas CONTREDIT — la règle n'a pas joué.")

    # ── VERDICT GLOBAL ───────────────────────────────────────────────────
    dire("\n" + "=" * 98)
    succes = (len(catastrophes) == 0) and (not viol31) and piege2_ok and tie_ok
    if succes:
        dire(" ✅✅ SUCCÈS COMPLET — 0 catastrophe, pièges tenus, cas limite OK.")
        dire("     → On ADOPTE le juge scindé pour l'étape 2.")
    else:
        dire(" ⚠ Pas un sans-faute → on reste sur qwen + prompt découplé simple (V1) + dates.")
    dire("=" * 98)

    chemin = os.path.join(config.DOSSIER_RESULTATS, "etape1d_juge_scinde.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({
            "catastrophes": len(catastrophes),
            "piege1_ok": not viol31,
            "piege2_ok": piege2_ok,
            "cas_limite_ok": tie_ok,
            "succes": succes,
        }, f, ensure_ascii=False, indent=2)
    dire(f"\n Journal : {J.chemin}\n Détails JSON : {chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
