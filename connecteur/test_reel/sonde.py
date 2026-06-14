# -*- coding: utf-8 -*-
"""Sonde d'extraction : le greffier qwen mappe-t-il du langage REEL sur nos predicats ?"""
import sys, requests
sys.stdout.reconfigure(encoding="utf-8")
B = "http://127.0.0.1:8077"
requests.post(B + "/reset")
phrases = [
    ("Euronext est entree dans le CAC 40 le 22 septembre 2025.", "2025-09"),
    ("Teleperformance fait partie du CAC 40.", "2022-01"),
    ("Le Japon est qualifie pour la Coupe du monde 2026.", "2025-03"),
    ("Accor a integre le CAC 40 en mars 2024.", "2024-03"),
    ("Le 24 novembre 2025, l'indice CAC 40 vaut environ 8020 points.", "2025-11"),
]
for enonce, date in phrases:
    r = requests.post(B + "/ecrire", json={"enonce": enonce, "source_id": "Sonde", "date": date}).json()
    fait = (r.get("faits") or ["--"])[0]
    print(f"  [{r.get('action') or r.get('erreur')}]")
    print(f"    « {enonce} »")
    print(f"    => {fait}")
