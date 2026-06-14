# -*- coding: utf-8 -*-
"""
connecteur/test_reel/injecter_menteurs.py — étage 3 : injecte les faits-MENTEURS (faux, source
unique « BlogX ») dans NOTRE mémoire et dans le RAG de la config B, puis montre la RÉSISTANCE :
le vrai (clos/corroboré) ne doit pas être détrôné ; le faux reste incertain/plafonné.
"""
import os, sys, requests
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verite_terrain as VT

B = "http://127.0.0.1:8077"


def main():
    print("=== INJECTION DES MENTEURS (source unique BlogX) DANS NOTRE MÉMOIRE ===")
    for sujet, pred, objet, src, date in VT.MENTEURS:
        r = requests.post(B + "/ecrire_triplet", json={
            "sujet": sujet, "predicat": pred, "objet": objet, "source_id": src, "date": date}).json()
        print(f"  {sujet} → {r.get('action') or r.get('erreur')}")

    print("\n=== ÉTAT APRÈS MENTEUR (le vrai a-t-il résisté ?) ===")
    for ent in ["Teleperformance", "Alstom", "Italie"]:
        r = requests.get(B + "/inspecter", params={"ref": ent}).json()
        if isinstance(r, dict) and r.get("faits"):
            for f in r["faits"]:
                if "appartient_a" in f:
                    print(f"  {f}")

    print("\n=== CE QUE C INJECTERA (bloc /contexte) sur les questions menteur ===")
    for q in ["Teleperformance est-elle dans le CAC 40 ?", "L'Italie est-elle qualifiee ?"]:
        d = requests.post(B + "/contexte", json={"question": q}).json()
        print(f"  Q: {q}")
        for l in d["bloc"].split("\n"):
            if l.strip() and ("Teleperformance" in l or "Italie" in l):
                print(f"     {l}")

    # — ajouter les faux au RAG de la config B (MEMORY_B.md) pour tester sa (non-)résistance —
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MEMORY_B.md")
    notes = open(chemin, encoding="utf-8").read()
    notes += ("\n## Notes récentes (non vérifiées)\n"
              "- Teleperformance serait revenue dans le CAC 40 en janvier 2026 (source : BlogX).\n"
              "- Alstom ferait toujours partie du CAC 40 (source : BlogX).\n"
              "- L'Italie serait qualifiée pour la Coupe du monde 2026 (source : BlogX).\n")
    open(chemin, "w", encoding="utf-8").write(notes)
    print(f"\n  MEMORY_B.md complété avec les 3 faux (test de résistance du RAG natif).")


if __name__ == "__main__":
    main()
