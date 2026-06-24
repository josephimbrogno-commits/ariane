# -*- coding: utf-8 -*-
"""
tests/unitaires/test_canon_verbes_bruts.py — TEMPS A : canonicalisation des verbes bruts (déterministe).

Prouve, SANS LLM ni modèle :
  1. OFF (défaut) : un verbe brut listé (« ~diriger ») reste HORS-ontologie (« diriger ») → iso-résultat.
  2. ON : il est rabattu sur sa case canonique (« dirige ») — et l'orientation par l'axe rôle tient.
  3. ASSURANCE CARDINALE : le prédicat rabattu est FONCTIONNEL (clôt un mandat) là où le verbe brut ne
     clôt JAMAIS (DEFAULT_SPEC fonctionnel=False) → c'est précisément ce qui aurait évité le CW du MoE.
  4. CONSERVATEUR : un verbe brut NON listé (« ~saboter ») n'est jamais rabattu (ON==OFF) → la table
     ne touche QUE des correspondances certaines.
  5. End-to-end (via Memoire + StubLLM scripté) : ON → l'ancien dirigeant se CLÔT ; OFF → il reste courant
     (le verbe brut ne clôt pas) = le bug cardinal reproduit puis corrigé par le flag.

Lance :  python tests/unitaires/test_canon_verbes_bruts.py
"""
import os, sys
from datetime import datetime
_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
os.chdir(_RACINE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
from memoire import Memoire, config
from memoire.coeur.extraction import _finaliser
from memoire.coeur.ontologie import spec_predicat

OK = []
def chk(cond, label):
    OK.append(bool(cond)); print(f"   {'✅' if cond else '❌'} {label}")


def stub_embed(texte):
    v = np.zeros(24, dtype=np.float32)
    for i, c in enumerate(str(texte)):
        v[(i * 7 + ord(c)) % 24] += (ord(c) % 13) + 1
    n = np.linalg.norm(v)
    return v / n if n else v


def brut_dir(holder):
    return {"predicat": "~diriger", "sujet": "Nexora", "objet": holder,
            "type_e_sujet": "organisation", "type_e_objet": "personne",
            "polarite": "affirmee", "modalite": "accompli", "temporalite": "courant",
            "date_debut": None, "date_fin": None}


class ScriptLLM:
    """json() renvoie une grille multi-faits scriptée selon le dirigeant cité dans le prompt."""
    def texte(self, prompt, systeme=None, temperature=0.0):
        return ""
    def json(self, prompt, systeme=None):
        for who, an in (("Karel", "2020"), ("Doss", "2024")):
            if who in prompt:
                return {"faits": [{"predicat": "~diriger", "sujet": "Nexora", "objet": f"M. {who}",
                                   "type_e_sujet": "organisation", "type_e_objet": "personne",
                                   "polarite": "affirmee", "modalite": "accompli",
                                   "temporalite": "courant", "date_debut": an, "date_fin": None}]}
        return {"faits": []}


def main():
    print("=" * 88)
    print(" TEMPS A — CANONICALISATION DES VERBES BRUTS (déterministe)")
    print("=" * 88)
    chk(config.OPT_CANON_VERBES_BRUTS is True, "défaut : OPT_CANON_VERBES_BRUTS = True (activé, validé sûr)")

    txt = "Nexora dirige M. Karel."
    # 1) OFF : reste brut
    config.OPT_CANON_VERBES_BRUTS = False
    r_off = _finaliser(brut_dir("M. Karel"), txt, None, None)
    chk(r_off and r_off["predicat"] == "diriger", "OFF : « ~diriger » reste verbe brut « diriger » (iso)")
    chk(spec_predicat("diriger")["fonctionnel"] is False, "OFF : « diriger » brut est NON fonctionnel → ne clôt jamais")

    # 2) + 3) ON : rabattu sur « dirige », fonctionnel
    config.OPT_CANON_VERBES_BRUTS = True
    r_on = _finaliser(brut_dir("M. Karel"), txt, None, None)
    chk(r_on and r_on["predicat"] == "dirige", "ON : « ~diriger » rabattu sur la case « dirige »")
    chk(r_on["sujet"] == "Nexora" and r_on["objet"] == "M. Karel", "ON : axe rôle tient (org→personne, pas d'inversion)")
    chk(spec_predicat("dirige")["fonctionnel"] is True, "ON : « dirige » est FONCTIONNEL → clôt le mandat (assurance cardinale)")

    r_int = _finaliser({"predicat": "~interpreter", "sujet": "Rob Brown", "objet": "Coach Carter",
                        "type_e_sujet": "personne", "type_e_objet": "oeuvre", "polarite": "affirmee",
                        "modalite": "accompli", "temporalite": "courant", "date_debut": None, "date_fin": None},
                       "Rob Brown interprète Coach Carter.", None, None)
    chk(r_int and r_int["predicat"] == "a_interprete", "ON : « ~interpreter » rabattu sur « a_interprete »")

    # 4) conservateur : un brut NON listé n'est jamais touché
    for flag in (False, True):
        config.OPT_CANON_VERBES_BRUTS = flag
        r = _finaliser({"predicat": "~saboter", "sujet": "Groupe X", "objet": "le projet",
                        "type_e_sujet": "organisation", "type_e_objet": "valeur", "polarite": "affirmee",
                        "modalite": "accompli", "temporalite": "courant", "date_debut": None, "date_fin": None},
                       "Groupe X sabote le projet.", None, None)
        chk(r and r["predicat"] == "saboter", f"conservateur : « ~saboter » (hors table) reste brut (flag={flag})")

    # 5) End-to-end : la clôture du mandat ne marche QUE ON
    def mandats_clos(canon_on):
        config.OPT_CANON_VERBES_BRUTS = canon_on
        config.OPT_MULTI_TRIPLETS = True; config.OPT_ABSTENTION_PREDICAT = True
        mem = Memoire(ScriptLLM(), stub_embed)
        mem.ecrire("En 2020, Karel dirige Nexora.", source_id="s1", date="2020-01")
        mem.ecrire("En 2024, Doss dirige Nexora.", source_id="s2", date="2024-01")
        g = mem.g
        clos = sum(f.statut == "clos" for f in g.faits.values())
        courant = sum(f.statut == "courant" for f in g.faits.values())
        preds = {f.predicat for f in g.faits.values()}
        return clos, courant, preds

    clos_on, cour_on, preds_on = mandats_clos(True)
    clos_off, cour_off, preds_off = mandats_clos(False)
    chk("dirige" in preds_on and "diriger" not in preds_on, "E2E ON : faits sous « dirige » canonique")
    chk("diriger" in preds_off, "E2E OFF : faits restent sous « diriger » brut")
    chk(clos_on >= 1, f"E2E ON : l'ancien mandat se CLÔT (clos={clos_on})")
    chk(clos_off == 0, f"E2E OFF : aucun mandat clos (verbe brut ne clôt pas) → CW reproduit (clos={clos_off})")

    config.OPT_CANON_VERBES_BRUTS = True         # restaurer le défaut (ON)
    print("\n" + "=" * 88)
    verdict = all(OK)
    print(f" {'✅ TEMPS A OK — rabattage sûr, conservateur, assurance cardinale prouvée' if verdict else '❌ ÉCHEC'}  ({sum(OK)}/{len(OK)})")
    print("=" * 88)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
