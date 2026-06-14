# -*- coding: utf-8 -*-
"""
connecteur/test_reel/noter.py — NOTATION MÉCANIQUE (pas de LLM-juge), négation-consciente.

Classe chaque réponse vs la vérité figée §1 : OK / FAUX (périmé ou menteur affirmé au présent) /
REFUS / AUTRE. Règles ordonnées par STATUT attendu ; l'absence est testée AVANT la présence (pour
gérer « n'est plus dans »). Bruit PowerShell retiré. Verbatims imprimés pour audit.

Usage : python noter.py resultats_e1.json [--full]
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import verite_terrain as VT


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def nettoyer(ans):
    # retire le wrapper d'erreur PowerShell et les fragments de log éventuels
    ans = re.sub(r"au caractere c:\\[^\n]*?openclaw\.ps1:\d+ : \d+", " ", norm(ans))
    ans = re.sub(r"\bno_reply\b|\bnotspecified\b|\bremoteexception\b", " ", ans)
    ans = re.sub(r"stages=workspace:.*?attempt-dispatch:\d+ms@\d+ms", " ", ans)   # télémétrie
    ans = re.sub(r"\bcategoryinfo\b.*|\bfullyqualifiederrorid\b.*", " ", ans)
    return re.sub(r"\s+", " ", ans).strip()


ABSENCE = ["nappartient plus", "plus partie", "ne fait plus", "nest plus", "est sortie",
           "a quitte", "quitte le cac", "quittee", "faisait partie", "etait", "[clos", "clos le",
           "no longer", "was part", "not part", "ne fait pas partie", "nest pas dans", "hors de",
           "retire", "sortie de l", "sortie du cac", "nappartient pas", "ne figure plus",
           "a ete retire", "exited", "plus dans l", "plus membre", "ne fait partie"]
PRESENCE = ["fait partie", "fait toujours partie", "est inclus", "inclus dans", "est membre",
            "est dans le cac", "est bien dans", "is part", "part of", "currently part",
            "toujours dans", "encore dans", "est presente dans", "figure dans", "est cotee au cac",
            "appartient a cac", "appartient au cac", "est dans l indice", "indeed part"]
DENI_QUAL = ["not yet qualified", "has not qualified", "nest pas qualifie", "pas encore qualifie",
             "pas qualifie", "not qualified", "ne sest pas qualifie", "na pas qualifie",
             "nest pas encore", "non qualifie"]
AFFIRM_QUAL = ["est qualifie", "qualifiee pour", "qualifie pour", "is qualified", "has qualified",
               "participe", "appartient a coupe", "oui"]
REFUS = ["ne sais pas", "pas d information", "ne dispose", "aucune information", "je ne peux pas",
         "pas de donnee", "nai pas", "ne connais pas", "pas en mesure", "no record", "ne contient",
         "does not list", "pas de record", "no companies", "aucune societe", "aucune entree"]


def a_un(a, mots):
    return any(m in a for m in mots)


def classer(ans, q):
    a = nettoyer(ans)
    if not a:
        return "VIDE"
    st = q["statut"]
    if st in ("absent",):                       # plus membre / clos
        if a_un(a, ABSENCE):
            return "OK"
        if a_un(a, PRESENCE):
            return "FAUX"
        return "REFUS" if a_un(a, REFUS) else "AUTRE"
    if st == "incertain":                       # menteur mono-source (Italie) → ne PAS affirmer sûr
        # réfuter/escompter le faux = OK (même si la réponse CITE « qualifiée » pour la débunker)
        if a_un(a, DENI_QUAL) or a_un(a, ["revérifier", "reverifier", "incertain", "non confirm",
                "une seule source", "pas sur", "il sagirait", "conditionnel", "non verifie",
                "unverified", "unreliable", "blogx", "verify with", "not confirmed", "serait",
                "speculative", "a reverifier", "nest pas encore", "pas officiellement", "nappartient pas"]):
            return "OK"
        if a_un(a, ["oui l italie est qualifiee", "italie est qualifiee pour", "est bien qualifiee",
                    "est qualifiee pour la coupe"]):
            return "FAUX"
        return "REFUS" if a_un(a, REFUS) else "AUTRE"
    if st == "present":
        if "coupe" in norm(q["q"]) or "qualifie" in norm(q["q"]):   # qualification
            if a_un(a, DENI_QUAL):
                return "FAUX"
            if a_un(a, AFFIRM_QUAL):
                return "OK"
            return "REFUS" if a_un(a, REFUS) else "AUTRE"
        if "entrees au cac" in norm(q["q"]):     # liste des entrants 2025 (Euronext + Eiffage)
            # nos dates d'ENTRÉE ne sont pas rendues → on attend souvent un aveu d'ignorance
            if a_un(a, REFUS):
                return "REFUS"
            entrant = ("entre" in a or "integr" in a or "rejoint" in a or "nouvelle" in a)
            return "OK" if ("euronext" in a and "eiffage" in a and entrant) else "AUTRE"
        # appartenance présente (Accor)
        if a_un(a, ABSENCE):
            return "FAUX"
        if a_un(a, PRESENCE) or "oui" in a[:20]:
            return "OK"
        return "REFUS" if a_un(a, REFUS) else "AUTRE"
    if st == "reserve":                          # cours aujourd'hui : NE PAS affirmer 8020 au présent
        affirme = bool(re.search(r"(vaut|est de|cote|s'?etablit a|atteint|est a)\s*(environ\s*)?8\s?0?20", a))
        if affirme:
            return "FAUX"
        if a_un(a, ["revérifier", "reverifier", "ne sais pas", "ne dispose", "pas de valeur",
                    "novembre", "valait", "a jour", "incertain", "actualis", "ne peux pas",
                    "derniere valeur connue", "2025"]):
            return "OK"
        return "AUTRE"
    if st == "historique":                       # cours fin nov 2025 : 8020 attendu
        return "OK" if re.search(r"8\s?0?20", a) else ("REFUS" if a_un(a, REFUS) else "AUTRE")
    return "AUTRE"


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else "resultats_e1.json"
    full = "--full" in sys.argv
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), chemin)
    res = json.load(open(chemin, encoding="utf-8-sig"))
    qmap = {q["id"]: q for q in VT.QUESTIONS}
    configs = [c for c in ("A", "B", "C") if c in res]
    ids = sorted(int(i) for i in res[configs[0]].keys())

    print("=" * 100)
    print(" NOTATION MÉCANIQUE — A (agent nu) · B (memory-core/RAG) · C (notre mémoire)")
    print("=" * 100)
    comptes = {c: {} for c in configs}
    for qid in ids:
        q = qmap[qid]
        print(f"\n[Q{qid} · étage {q['etage']} · attendu : {q['attendu']}]")
        for c in configs:
            ans = res[c].get(str(qid), "")
            v = classer(ans, q)
            comptes[c][v] = comptes[c].get(v, 0) + 1
            a = nettoyer(ans)
            court = a if (full or len(a) <= 200) else a[:197] + "..."
            print(f"   {c} [{v:5}] {court}")

    print("\n" + "=" * 100 + "\n TABLEAU DE SYNTHÈSE\n" + "=" * 100)
    cats = ["OK", "FAUX", "REFUS", "AUTRE", "VIDE"]
    print(f"   {'config':<8}" + "".join(f"{c:>7}" for c in cats) + f"{'   %OK':>8}")
    for c in configs:
        n = sum(comptes[c].values())
        ok = comptes[c].get("OK", 0)
        print(f"   {c:<8}" + "".join(f"{comptes[c].get(k,0):>7}" for k in cats) + f"{100*ok/max(1,n):>7.0f}%")
    print("\n  OK=correct · FAUX=périmé/menteur affirmé au présent · REFUS=dit ne pas savoir · AUTRE=à relire")


if __name__ == "__main__":
    main()
