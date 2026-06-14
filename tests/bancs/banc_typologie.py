# -*- coding: utf-8 -*-
"""
tests/bancs/banc_typologie.py — NON-RÉGRESSION de l'option typologie (mission Typologie).

Rejoue le grand monde gelé (graine 42) en utilisant le classifieur de la BIBLIOTHÈQUE
(memoire.options.typologie_liens.predire) au lieu du prototype plat. Le monde structure_monde
reste la fixture de banc (features hand-craftées des pièges). Les chiffres DOIVENT retomber
au pourcent près sur la référence du prototype.

Référence (prototype plat etape_structure_3, graine 42) :
  S1=52 %  S2=73 %  S1+S2=91 %  S1+S2+décl=100 %  ·  frange 6/46 (13 %)

Lance :  python tests/bancs/banc_typologie.py
"""

import os
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)                                  # racine : pour `import memoire`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # ce dossier : fixtures de banc
os.chdir(_RACINE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import structure_monde as S                                  # fixture de banc (monde + features)
from memoire.options.typologie_liens import predire, ASYMETRIQUES_DURABLES, DURABLE, EPHEMERE

SEED = 42
REFERENCE = {"S1": 52, "S2": 73, "S1S2": 91, "S1S2_decl": 100, "frange": (6, 46)}


def predire_lien(l, liens, deg, mode):
    feat = S.features(l, liens, deg)
    if mode == "S1S2_decl":
        if l.predicat in ASYMETRIQUES_DURABLES:
            return DURABLE
        return predire(feat, "S1S2")
    return predire(feat, mode)


def acc(primaires, liens, deg, mode):
    bon = sum(1 for l in primaires if predire_lien(l, liens, deg, mode) == l.nature)
    return 100.0 * bon / len(primaires)


def main():
    entites, liens = S.generer_grand(seed=SEED)
    deg = S.degres(liens)
    primaires = [l for l in liens if l.primaire]
    durables = [l for l in primaires if l.nature == DURABLE]

    print("=" * 88)
    print(f" NON-RÉGRESSION TYPOLOGIE (lib) — graine {SEED} · {len(primaires)} liens "
          f"({len(durables)} durables)")
    print("=" * 88)

    OK = []
    for mode in ("S1", "S2", "S1S2", "S1S2_decl"):
        a = round(acc(primaires, liens, deg, mode))
        ref = REFERENCE[mode]
        ok = (a == ref)
        OK.append(ok)
        print(f"   {'✅' if ok else '❌'} {mode:<12} {a:>3} %   (réf {ref} %)")

    rates = [l for l in durables if predire_lien(l, liens, deg, "S1S2") == EPHEMERE]
    fr_ok = (len(rates), len(durables)) == REFERENCE["frange"]
    OK.append(fr_ok)
    tous_asym = all(l.predicat in ASYMETRIQUES_DURABLES for l in rates)
    print(f"   {'✅' if fr_ok else '❌'} frange       {len(rates)}/{len(durables)} durables manqués "
          f"(réf {REFERENCE['frange'][0]}/{REFERENCE['frange'][1]}) · "
          f"{'tous asymétriques' if tous_asym else 'PAS tous asym !'}")

    print("\n" + "=" * 88)
    verdict = all(OK)
    print(f" {'✅ TYPOLOGIE : verdict reproduit AU CHIFFRE PRÈS depuis la bibliothèque' if verdict else '❌ DÉRIVE — régression cachée'}"
          f"  ({sum(OK)}/{len(OK)})")
    print("=" * 88)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
