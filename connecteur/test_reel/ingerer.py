# -*- coding: utf-8 -*-
"""
connecteur/test_reel/ingerer.py — ingestion CHRONOLOGIQUE fidèle de la vérité-terrain.

Modélisation epistémique réaliste (faits publics = plusieurs sources) :
  • chaque fait vrai est CORROBORÉ par 2 sources indépendantes → Certitude « sûr » (≥0.6).
  • les membres ACTUELS sont RECONFIRMÉS en mars 2026 (§1.1 : « composition inchangée ») → ils ne
    décroissent pas et restent « sûr » au 14/06/2026.
  • les membres SORTIS sont clos à leur date → « était… jusqu'à ».
  • le COURS (volatil, snapshot du 24/11/2025) n'est PAS reconfirmé → après consolidation au
    14/06/2026 il s'effondre en « à revérifier » (le piège de l'étage 2).
La vérité figée s'injecte en triplets EXACTS (pas de greffier). MEMORY.md (config B) = mêmes faits à plat.
"""
import os, re, sys, requests
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verite_terrain as VT

B = "http://127.0.0.1:8077"
CORRO = {"Euronext": "CafeBourse", "FIFA": "Wikipedia"}   # 2e source indépendante par domaine
RECONFIRME = "2026-03"   # §1.1 composition inchangée mars 2026
DATE_TEST = "2026-06"


def fid_de(res):
    s = (res.get("faits") or [""])[-1]
    m = re.search(r"#(\d+)", s)
    return int(m.group(1)) if m else None


def ecrire(sujet, pred, objet, source, date, validite=None):
    return requests.post(B + "/ecrire_triplet", json={
        "sujet": sujet, "predicat": pred, "objet": objet,
        "source_id": source, "date": date, "validite": validite}).json()


def main():
    requests.post(B + "/reset")
    print("=== INGESTION (chronologique, 2 sources, reconfirmation, consolidation) ===")
    n_clos = 0
    for sujet, pred, objet, src, valide_de, clore_a in sorted(VT.FAITS, key=lambda f: f[4]):
        src2 = CORRO.get(src, src + "-bis")
        r1 = ecrire(sujet, pred, objet, src, valide_de, valide_de)      # 1re source
        ecrire(sujet, pred, objet, src2, valide_de, valide_de)          # corroboration → « sûr »
        if clore_a:
            fid = fid_de(r1)
            if fid:
                requests.post(B + "/retoucher", json={
                    "fait_id": fid, "action": "clore", "source_id": src, "date": clore_a})
                n_clos += 1
        elif objet != "8020":      # actuels (hors cours) → reconfirmés mars 2026
            ecrire(sujet, pred, objet, src, RECONFIRME, valide_de)

    requests.post(B + "/consolider", json={"date": DATE_TEST})           # décroissances au 14/06/2026
    s = requests.get(B + "/sante").json()
    print(f"  {s['faits']} faits · {n_clos} clôtures datées · consolidé au {DATE_TEST}")

    # — MEMORY.md de la config B : mêmes faits, à plat (le RAG naïf, non trié) —
    L = ["# Mémoire — faits enregistrés\n", "## CAC 40 (indice boursier)"]
    for sujet, *_ , clore_a in [(f[0], f[5]) for f in VT.CAC]:
        L.append(f"- {sujet} fait partie du CAC 40.")
        if clore_a:
            L.append(f"- {sujet} est sortie du CAC 40 (sortie : {clore_a}).")
    L.append("- Le 24/11/2025, le CAC 40 valait environ 8020 points.")
    L.append("\n## Coupe du monde 2026")
    L.append("- Équipes qualifiées : " + ", ".join(f[0] for f in VT.CDM) + ".")
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MEMORY_B.md")
    open(chemin, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"  MEMORY.md (config B) : {chemin}")

    print("\n=== ÉTAT DE LA MÉMOIRE (preuves de tri au 14/06/2026) ===")
    for ent in ["Teleperformance", "Accor", "Euronext SA", "Edenred", "CAC 40", "Japon"]:
        r = requests.get(B + "/inspecter", params={"ref": ent}).json()
        if isinstance(r, dict) and r.get("faits"):
            for f in r["faits"]:
                if "appartient_a" in f or "prix_de" in f:
                    print(f"  {f}")


if __name__ == "__main__":
    main()
