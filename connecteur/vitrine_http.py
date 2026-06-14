# -*- coding: utf-8 -*-
"""
connecteur/vitrine_http.py — la vitrine, servie PAR LE RÉSEAU.

Mêmes valeurs que exemples/vitrine.py, mais tout passe par HTTP : on écrit des faits, on consolide,
on demande le CONTEXTE — et on voit la grammaire épistémique (présent / « était… jusqu'à » /
« à revérifier ») franchir le réseau. Plus une preuve que la règle d'or survit au pont (lier sans
source → HTTP 422).

Pré-requis : le service tourne (uvicorn connecteur.service:app --port 8077) + Ollama.
Lance :  python connecteur/vitrine_http.py
"""

import sys
import requests

BASE = "http://127.0.0.1:8077"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    s = requests.Session()
    print("santé :", s.get(f"{BASE}/sante").json())
    s.post(f"{BASE}/reset")

    # Trois histoires sur Nexora, pour faire naître les trois temps de la grammaire :
    faits = [
        # siège corroboré (2 sources indépendantes) → ACTUEL sûr → présent affirmé
        ("En janvier 2026, le siège de Nexora est à Lyon.", "Gazette",  "2026-01"),
        ("Le siège social de Nexora se trouve à Lyon.",      "Tribune",  "2026-02"),
        # PDG qui change : l'ancien sera CLOS (« était… jusqu'à »), le nouveau mono-source incertain
        ("En janvier 2026, le PDG de Nexora est Mme Karel.", "Gazette",  "2026-01"),
        ("Depuis mai 2026, le PDG de Nexora est M. Doss.",   "Officiel", "2026-05"),
    ]
    print("\n— ÉCRITURE (via HTTP /ecrire) —")
    for enonce, src, date in faits:
        r = s.post(f"{BASE}/ecrire", json={"enonce": enonce, "source_id": src, "date": date}).json()
        print(f"   {src:9} → {r.get('action')}")

    print("\n— CONSOLIDATION (via HTTP /consolider) —")
    print("  ", s.post(f"{BASE}/consolider", json={"date": "2026-06"}).json())

    print("\n— CONTEXTE (via HTTP /contexte) : la grammaire épistémique qui traverse le réseau —")
    r = s.post(f"{BASE}/contexte",
               json={"question": "Que sais-tu sur l'entreprise Nexora ?", "date": "2026-06"}).json()
    print(r["bloc"])

    print("\n— LA TRACE (via HTTP /inspecter) : rien n'est détruit —")
    for f in s.get(f"{BASE}/inspecter", params={"ref": "Nexora"}).json()["faits"]:
        print("  ", f)

    print("\n— RÈGLE D'OR à travers le pont : lier SANS source —")
    r = s.post(f"{BASE}/lier", json={"entite_a": "Nexora", "relation": "dirige", "entite_b": "X"})
    print(f"   HTTP {r.status_code} → {r.json().get('detail')}")

    print("\n— … et lier AVEC source (passe par le pipeline, plafond menteur) —")
    r = s.post(f"{BASE}/lier", json={"entite_a": "Orion", "relation": "appartient_a",
                                     "entite_b": "Nexora", "source_id": "BlogX", "date": "2026-03"}).json()
    print("  ", r.get("action"), "|", (r.get("faits") or ["—"])[0])


if __name__ == "__main__":
    main()
