# -*- coding: utf-8 -*-
"""
etape1_micro.py — LA MICRO-VERSION (étape 1).

But : VOIR le mécanisme vivre, en petit et en clair.
  - 30 souvenirs écrits à la main (faits stables + paires périmé/à-jour + bruit).
  - 10 questions.
  - Pour chaque question, on affiche : souvenirs trouvés, réponse, verdicts du juge,
    et la confiance AVANT → APRÈS de chaque souvenir touché.
  - Érosion temporelle douce entre les questions (horloge simulée).
  - Une consolidation (« sommeil ») à la fin.

Lance :  python etape1_micro.py
"""

import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # se placer dans le dossier du projet
try:
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows en UTF-8 (accents, ✓, …)
except Exception:
    pass

import config
from horloge import HorlogeVirtuelle
from memoire_store import Memoire
from util import Journal
import cycle


# ── Les 30 souvenirs de départ (tous confiance 0.60, créés le DATE_DEBUT) ──
#   • paires "périmé / à jour" : pour voir la SURPRISE (contradiction) jouer
#   • faits stables : pour voir le RENFORCEMENT (confirmation)
#   • #3/#4 : quasi-doublons (pour voir la fusion au « sommeil »)
#   • Mireval (21-23) + fillers (27-30) : jamais interrogés → on voit la PÉREMPTION
SOUVENIRS = [
    "Le PDG de Nexora est Mme Karel.",                                  # 1 périmé
    "Depuis mars 2026, le PDG de Nexora est M. Doss.",                  # 2 à jour
    "Le siège social de Nexora se trouve à Lyon.",                      # 3 stable
    "Nexora a son siège dans la ville de Lyon.",                        # 4 doublon de 3
    "Le module Z de Nexora coûte 120 euros.",                           # 5 périmé
    "Depuis 2026, le module Z de Nexora coûte 95 euros.",               # 6 à jour
    "La maire d'Aquilo est M. Brunet.",                                 # 7 périmé
    "Depuis les élections de 2026, la maire d'Aquilo est Mme Lefort.",  # 8 à jour
    "La ville d'Aquilo compte environ 80 000 habitants.",              # 9 stable
    "La rivière Vence traverse la ville d'Aquilo.",                     # 10 stable
    "Le Dr Sorel travaille à l'hôpital central d'Aquilo.",             # 11 périmé
    "Depuis 2026, le Dr Sorel dirige la clinique du Lac.",             # 12 à jour
    "Le Dr Sorel est spécialiste en cardiologie.",                     # 13 stable
    "L'entreprise Veltis fabrique des panneaux solaires.",             # 14 stable
    "Le directeur technique de Veltis est M. Aro.",                    # 15 stable
    "Veltis emploie 240 personnes.",                                   # 16 périmé
    "En 2026, Veltis emploie 310 personnes.",                          # 17 à jour
    "La bibliothèque Halgren ferme ses portes à 18h.",                 # 18 périmé
    "Depuis 2026, la bibliothèque Halgren ferme à 20h.",               # 19 à jour
    "La bibliothèque Halgren est située rue des Tilleuls.",            # 20 stable
    "L'entreprise Mireval produit du café équitable.",                 # 21 jamais interrogé
    "Le paquet de café Mireval coûte 6 euros.",                        # 22 jamais interrogé
    "Mireval a été fondée en 2015.",                                   # 23 jamais interrogé
    "Le festival Lumina a lieu chaque année en juillet.",              # 24 stable
    "Le festival Lumina se déroule à Aquilo.",                         # 25 périmé
    "Depuis 2026, le festival Lumina se déroule à Bornes.",            # 26 à jour
    "Le lac de Borne gèle rarement en hiver.",                         # 27 bruit
    "L'école Vauban propose un enseignement du mandarin.",             # 28 bruit
    "La gare de Tomel possède quatre quais.",                          # 29 bruit
    "Le pont de Sève mesure 200 mètres de long.",                      # 30 bruit
]

# ── Les 10 questions (mélange périmé / stable) ────────────────────────────
QUESTIONS = [
    "Qui dirige actuellement l'entreprise Nexora ?",
    "Quel est le prix actuel du module Z de Nexora ?",
    "Qui est la maire d'Aquilo en 2026 ?",
    "Où exerce le Dr Sorel aujourd'hui ?",
    "À quelle heure ferme la bibliothèque Halgren ?",
    "Combien de personnes l'entreprise Veltis emploie-t-elle en 2026 ?",
    "Dans quelle ville se tient désormais le festival Lumina ?",
    "Quelle est la spécialité médicale du Dr Sorel ?",
    "Où se trouve le siège social de Nexora ?",
    "Que fabrique l'entreprise Veltis ?",
]

JOURS_ENTRE_QUESTIONS = 3  # l'horloge avance de 3 jours simulés entre 2 questions


def main():
    J = Journal("etape1")
    dire = J.dire

    dire("=" * 78)
    dire(" ÉTAPE 1 — MICRO-VERSION : voir la mémoire qui trie en action")
    dire("=" * 78)
    dire(f" Modèle : {config.MODELE_LLM} | demi-vie : {config.DEMI_VIE_JOURS} j | "
         f"gain +{config.GAIN_CONFIRMATION} | perte -{config.PERTE_CONTRADICTION}")
    dire("")

    # 1) Construire la mémoire de départ
    horloge = HorlogeVirtuelle(config.DATE_DEBUT)
    mem = Memoire(horloge)
    dire(f"→ Création de {len(SOUVENIRS)} souvenirs (confiance de départ "
         f"{config.CONFIANCE_DEPART}, date {horloge.texte()})…")
    for txt in SOUVENIRS:
        mem.ajouter(txt)
    dire("   …mémoire prête.\n")
    mem.enregistrer_confiances()

    # 2) Boucle de questions
    for n, question in enumerate(QUESTIONS, start=1):
        dire("─" * 78)
        dire(f"QUESTION {n}/{len(QUESTIONS)} — [horloge {horloge.texte()}]")
        dire(f"  « {question} »")

        # (a) Érosion temporelle depuis la dernière fois
        mem.eroder()

        # (b) Recherche
        trouves = mem.rechercher(question)
        dire("\n  ▸ Souvenirs trouvés (similarité) :")
        for s, score in trouves:
            dire(f"      #{s.id:<2} [sim {score:.2f}] [conf {s.confiance:.2f}] {s.contenu}")

        # (c) Réponse du modèle (Config C : avec date + confiance)
        bloc = mem.texte_injection(trouves, avec_meta=True)
        prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
        reponse = cycle.modele.repondre(prompt, systeme=cycle.SYS_REPONSE_C)
        dire(f"\n  ▸ Réponse du modèle :\n      « {reponse} »")

        # (d) Le juge
        verdicts = cycle.juger(question, reponse, trouves)
        dire("\n  ▸ Verdicts du juge & mise à jour des confiances :")
        for s, _ in trouves:
            info = verdicts.get(s.id, {"verdict": "INCERTAIN", "justification": "(non rendu)"})
            avant = s.confiance
            mem.appliquer_verdict(s, info["verdict"])
            apres = s.confiance
            fleche = "→"
            marque = {"CONFIRME": "✓", "CONTREDIT": "✗", "NON_UTILISE": "·", "INCERTAIN": "?"}.get(
                info["verdict"], "?"
            )
            dire(f"      {marque} #{s.id:<2} {info['verdict']:<11} "
                 f"conf {avant:.2f} {fleche} {apres:.2f}  | {info['justification']}")

        mem.cycles += 1
        mem.enregistrer_confiances()

        # (e) L'horloge avance avant la question suivante
        horloge.avancer(JOURS_ENTRE_QUESTIONS)
        dire("")

    # 3) Consolidation (« sommeil ») de démonstration
    dire("─" * 78)
    dire("SOMMEIL — consolidation de la mémoire (fusion des doublons, archivage des faibles)")
    rapport = mem.consolider()
    if rapport["fusions"]:
        for f in rapport["fusions"]:
            dire(f"   ⤳ doublon fusionné : on garde #{f['garde']}, on archive "
                 f"#{f['archive']} (similarité {f['similarite']})")
    else:
        dire("   ⤳ aucun doublon assez proche pour être fusionné.")
    if rapport["archivages_faibles"]:
        for a in rapport["archivages_faibles"]:
            dire(f"   ⤳ archivé (trop faible) : #{a['id']} (confiance {a['confiance']})")
    else:
        dire("   ⤳ aucun souvenir sous le seuil d'archivage.")
    dire("")

    # 4) Bilan : où en sont les confiances ?
    dire("─" * 78)
    dire("BILAN FINAL — confiance de chaque souvenir (triée par confiance décroissante)")
    dire("  Lecture : les faits CONFIRMÉS montent, les PÉRIMÉS chutent, les JAMAIS")
    dire("  CONSULTÉS s'érodent doucement. C'est exactement l'effet recherché.\n")
    for s in sorted(mem.souvenirs, key=lambda x: -x.confiance):
        etat = "" if s.statut == "actif" else "  [ARCHIVÉ]"
        marque = ""
        if s.compteur_confirmations:
            marque = f"  (confirmé ×{s.compteur_confirmations})"
        elif s.compteur_contradictions:
            marque = f"  (contredit ×{s.compteur_contradictions})"
        dire(f"   conf {s.confiance:.2f}  #{s.id:<2} {s.contenu}{marque}{etat}")

    # 5) Sauvegardes inspectables
    chemin_json = os.path.join(config.DOSSIER_RESULTATS, "etape1_memoire_finale.json")
    mem.sauvegarder(chemin_json)
    chemin_hist = os.path.join(config.DOSSIER_RESULTATS, "etape1_historique_confiance.json")
    with open(chemin_hist, "w", encoding="utf-8") as f:
        json.dump(mem.historique_confiance, f, ensure_ascii=False, indent=2)

    dire("")
    dire("=" * 78)
    dire(f" ✅ Étape 1 terminée.")
    dire(f"   • Journal complet : {J.chemin}")
    dire(f"   • Mémoire finale  : {chemin_json}")
    dire(f"   • Historique conf.: {chemin_hist}")
    dire("=" * 78)
    J.fermer()


if __name__ == "__main__":
    main()
