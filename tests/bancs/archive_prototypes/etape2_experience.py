# -*- coding: utf-8 -*-
"""
etape2_experience.py — L'EXPÉRIENCE (étape 2).

Compare, sur les MÊMES ~60 questions, trois configurations :
  • A — modèle seul          (aucune mémoire)
  • B — RAG classique inerte (mêmes souvenirs, SANS date ni confiance, AUCUNE mise à jour)
  • C — la mémoire qui trie  (système complet, nourri chronologiquement, érosion +
                              confirmation/contradiction + consolidation)

Hypothèse : C bat A et B sur les FAITS QUI ONT CHANGÉ, en restant ≥ B sur les faits stables.

Produit un rapport markdown lisible dans resultats/etape2_rapport.md (+ logs JSON).

Lance :  python etape2_experience.py
"""

import json
import os
import sys
import random
from datetime import timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import cycle
from horloge import HorlogeVirtuelle
from memoire_store import Memoire
from util import Journal, assurer_dossiers
import monde
from monde import normaliser


# ──────────────────────────────────────────────────────────────────────────
#  Outils
# ──────────────────────────────────────────────────────────────────────────
def correct(reponse, cle_attendue):
    """Correspondance automatique : la clé attendue apparaît-elle dans la réponse ?"""
    return cle_attendue in normaliser(reponse)


def souvenir_cle(meta_kind, fait):
    return fait.cle_init if meta_kind == "init" else fait.cle_finale


# ──────────────────────────────────────────────────────────────────────────
#  CONFIG C — construction chronologique de la mémoire
# ──────────────────────────────────────────────────────────────────────────
def construire_memoire_C(faits, dire):
    horloge = HorlogeVirtuelle(config.MONDE_DEBUT)
    mem = Memoire(horloge)
    meta = {}                      # sid -> (fait, kind)
    sid_vrai = {}                  # fid -> sid du souvenir portant la valeur VRAIE finale

    # — Événements : arrivées de faits + consultations + photos mensuelles —
    evts = []
    for f in faits:
        evts.append((f.date_init, 0, "arrivee", f, "init"))
        if f.change:
            evts.append((f.date_change, 0, "arrivee", f, "final"))

    # — Consultations par BALAYAGES MENSUELS, pondérées par la « popularité » du fait —
    rng = random.Random(config.SEED_MONDE + 2)
    pop = {f.fid: rng.random() ** 1.5 for f in faits}     # popularité skewée (certains ~0)
    moy = sum(pop.values()) / len(pop)
    k = config.CONSULT_CIBLE_PAR_MOIS / (len(faits) * moy)  # vise ~N consultations / mois
    n_consult_prevu = 0
    dm = config.MONDE_DEBUT
    while dm <= config.MONDE_FIN:
        for f in faits:
            if rng.random() < min(1.0, pop[f.fid] * k):
                jour = dm + timedelta(days=rng.randint(0, 27))  # étalé dans le mois
                if jour <= config.MONDE_FIN:
                    evts.append((jour, 1, "consult", f, None))
                    n_consult_prevu += 1
        m, y = dm.month, dm.year
        dm = dm.replace(year=y + (m // 12), month=(m % 12) + 1, day=1)

    # photos au 1er de chaque mois
    d = config.MONDE_DEBUT
    while d <= config.MONDE_FIN:
        evts.append((d, 2, "photo", None, None))
        # mois suivant
        m, y = d.month, d.year
        d = d.replace(year=y + (m // 12), month=(m % 12) + 1, day=1)

    evts.sort(key=lambda e: (e[0], e[1]))

    snapshots = []                 # (date, moy_vrais, moy_perimes, n_vrais, n_perimes)
    juge_total = 0                 # verdicts conséquents (CONFIRME/CONTREDIT) émis
    juge_faux = 0                  # verdicts faux vs vérité-terrain
    juge_details = []
    n_consult = 0

    def photo(date):
        vrais, perimes = [], []
        for s in mem.souvenirs:
            f, kind = meta[s.id]
            est_vrai = (souvenir_cle(kind, f) == f.verite_a(date))
            (vrais if est_vrai else perimes).append(s.confiance)
        moy = lambda L: round(sum(L) / len(L), 4) if L else None
        snapshots.append((date.strftime("%Y-%m-%d"), moy(vrais), moy(perimes),
                          len(vrais), len(perimes)))

    for (date, _, typ, f, kind) in evts:
        mem.horloge.date = date
        mem.eroder()

        if typ == "arrivee":
            enonce = f.enonce_init() if kind == "init" else f.enonce_change()
            s = mem.ajouter(enonce, date=date)
            meta[s.id] = (f, kind)
            # le souvenir portant la valeur VRAIE finale (pour les « faux oublis »)
            if (kind == "final") or (kind == "init" and not f.change):
                sid_vrai[f.fid] = s.id

        elif typ == "consult":
            q = f.question
            reponse, trouves = cycle.repondre_C(mem, q)
            verdicts = cycle.juger_champion(q, reponse, trouves)
            for s, _ in trouves:
                v = verdicts.get(s.id, {"verdict": "INCERTAIN"})["verdict"]
                # mesure de faillibilité du juge (vs vérité-terrain à CETTE date)
                fs, ks = meta[s.id]
                s_vrai = (souvenir_cle(ks, fs) == fs.verite_a(date))
                if v in ("CONFIRME", "CONTREDIT"):
                    juge_total += 1
                    faux = (v == "CONTREDIT" and s_vrai) or (v == "CONFIRME" and not s_vrai)
                    if faux:
                        juge_faux += 1
                        juge_details.append({
                            "date": date.strftime("%Y-%m-%d"), "question": q,
                            "souvenir": s.contenu, "verdict": v,
                            "souvenir_vrai_a_cette_date": s_vrai})
                mem.appliquer_verdict(s, v)
            n_consult += 1
            if n_consult % config.N_CONSOLIDATION == 0:
                mem.consolider()

        elif typ == "photo":
            photo(date)

    # photo finale
    mem.horloge.date = config.MONDE_FIN
    mem.eroder()
    photo(config.MONDE_FIN)
    rapport_conso = mem.consolider()

    dire(f"  Config C construite : {len(mem.souvenirs)} souvenirs, "
         f"{len(mem.actifs())} actifs, {n_consult} consultations.")
    return mem, meta, sid_vrai, snapshots, (juge_total, juge_faux, juge_details), n_consult


# ──────────────────────────────────────────────────────────────────────────
#  CONFIG B — RAG inerte : tous les souvenirs (anciens ET nouveaux), figés
# ──────────────────────────────────────────────────────────────────────────
def construire_memoire_B(faits):
    horloge = HorlogeVirtuelle(config.MONDE_FIN)
    mem = Memoire(horloge)
    for f in faits:
        mem.ajouter(f.enonce_init(), date=f.date_init)
        if f.change:
            mem.ajouter(f.enonce_change(), date=f.date_change)
    return mem


# ──────────────────────────────────────────────────────────────────────────
#  ÉVALUATION
# ──────────────────────────────────────────────────────────────────────────
def evaluer(questions_eval, memB, memC, dire):
    lignes = []
    for i, f in enumerate(questions_eval, start=1):
        attendu = f.cle_vraie_finale()
        rep_A = cycle.repondre_A(f.question)
        rep_B, _ = cycle.repondre_B(memB, f.question)
        rep_C, _ = cycle.repondre_C(memC, f.question)
        lignes.append({
            "fid": f.fid, "question": f.question, "categorie": f.categorie(),
            "attendu": attendu, "val_finale": f.val_finale if f.change else f.val_init,
            "A": rep_A, "okA": correct(rep_A, attendu),
            "B": rep_B, "okB": correct(rep_B, attendu),
            "C": rep_C, "okC": correct(rep_C, attendu),
        })
        if i % 10 == 0:
            dire(f"    …{i}/{len(questions_eval)} questions évaluées")
    return lignes


def precision(lignes, conf, categorie=None):
    sel = [l for l in lignes if categorie is None or l["categorie"] == categorie]
    if not sel:
        return 0.0, 0, 0
    ok = sum(1 for l in sel if l["ok" + conf])
    return 100.0 * ok / len(sel), ok, len(sel)


# ──────────────────────────────────────────────────────────────────────────
#  RAPPORT
# ──────────────────────────────────────────────────────────────────────────
def ecrire_rapport(faits, questions_eval, lignes, snapshots, juge, memC, meta, sid_vrai, n_consult):
    R = []
    w = R.append

    n_ch = sum(1 for f in faits if f.change)
    w("# Étape 2 — « La mémoire qui trie » : résultats de l'expérience\n")
    w("## Paramètres utilisés (valeurs par défaut, sans ajustement)\n")
    w("| Paramètre | Valeur |")
    w("|---|---|")
    w(f"| Répondeur (modèle) | `{config.MODELE_LLM}` |")
    w(f"| Juge (config championne) | `{config.MODELE_JUGE}` + prompt découplé simple (V1), confiance masquée |")
    w(f"| Embeddings | `{config.MODELE_EMBEDDINGS}` |")
    w(f"| Confiance de départ | {config.CONFIANCE_DEPART} |")
    w(f"| Gain (confirmation) | +{config.GAIN_CONFIRMATION} |")
    w(f"| Perte (contradiction) | −{config.PERTE_CONTRADICTION} |")
    w(f"| Demi-vie d'érosion | {config.DEMI_VIE_JOURS} jours |")
    w(f"| Seuil d'archivage | {config.SEUIL_ARCHIVAGE} |")
    w(f"| Seuil de fusion (doublons) | {config.SEUIL_FUSION} |")
    w(f"| Consolidation tous les | {config.N_CONSOLIDATION} interactions |")
    w(f"| Top-k recherche | {config.TOP_K} |")
    w(f"| Chronologie simulée | {config.MONDE_DEBUT:%Y-%m-%d} → {config.MONDE_FIN:%Y-%m-%d} (12 mois) |")
    w(f"| Consultations simulées (config C) | {n_consult} (balayages mensuels, "
      f"~{config.CONSULT_CIBLE_PAR_MOIS}/mois pondérés par popularité) |")
    w(f"| Graine aléatoire | {config.SEED_MONDE} |")
    w("")
    w("## Le monde synthétique\n")
    w(f"- **{len(faits)} faits** sur **{len(set(f.entite for f in faits))} entités** "
      f"(entreprises, villes, personnes, lieux).")
    w(f"- **{n_ch} faits changent** au fil des 12 mois ({100*n_ch/len(faits):.0f} %), "
      f"à des dates connues (vérité-terrain). **{len(faits)-n_ch}** restent stables.")
    w(f"- Évaluation finale : **{len(questions_eval)} questions** "
      f"({sum(1 for f in questions_eval if f.change)} sur des faits changés, "
      f"{sum(1 for f in questions_eval if not f.change)} sur des faits stables).\n")

    # — Résultats —
    w("## Résultats — précision (réponse correcte vs vérité-terrain)\n")
    w("| Configuration | Globale | **Faits changés** (métrique décisive) | Faits stables |")
    w("|---|---|---|---|")
    res = {}
    for conf, nom in [("A", "A — modèle seul"), ("B", "B — RAG inerte"), ("C", "C — mémoire qui trie")]:
        g, gok, gn = precision(lignes, conf)
        c, cok, cn = precision(lignes, conf, "changé")
        s, sok, sn = precision(lignes, conf, "stable")
        res[conf] = {"global": g, "change": c, "stable": s}
        w(f"| {nom} | {g:.0f} % ({gok}/{gn}) | {c:.0f} % ({cok}/{cn}) | {s:.0f} % ({sok}/{sn}) |")
    w("")

    # — Verdict —
    cC, cB, cA = res["C"]["change"], res["B"]["change"], res["A"]["change"]
    sC, sB = res["C"]["stable"], res["B"]["stable"]
    succes = (cC > cB) and (cC > cA) and (sC >= sB - 1e-9)
    w("## Verdict sur l'hypothèse\n")
    w(f"> **Critère de succès** : C > B et C > A sur les faits changés, avec C ≥ B sur les faits stables.\n")
    if succes:
        w(f"### ✅ SUCCÈS\n")
        w(f"Sur les faits qui ont changé, **C atteint {cC:.0f} %**, contre **{cB:.0f} % pour B** "
          f"(RAG inerte) et **{cA:.0f} % pour A** (modèle seul). Sur les faits stables, "
          f"C ({sC:.0f} %) reste ≥ B ({sB:.0f} %). L'hypothèse est confirmée : dater les souvenirs, "
          f"contredire l'ancien et entretenir le récent permet de répondre juste là où le RAG "
          f"classique ressort l'ancien et le nouveau en vrac.")
    else:
        w(f"### ⚠ ÉCHEC (ou partiel) — et pourquoi\n")
        w(f"Sur les faits changés : C={cC:.0f} %, B={cB:.0f} %, A={cA:.0f} %. "
          f"Stables : C={sC:.0f} %, B={sB:.0f} %.")
        explications = []
        if cC <= cB:
            explications.append(
                "- **C ne dépasse pas B sur les faits changés.** Causes possibles : le répondeur "
                "n'exploite pas assez le signal de date/confiance ; ou les anciens faits ne sont pas "
                "assez contredits/érodés (juge ou demi-vie). À regarder dans les exemples et la "
                "faillibilité du juge ci-dessous.")
        if sC < sB:
            explications.append(
                "- **C perd sur les faits stables** : l'érosion a probablement archivé des faits "
                "VRAIS rarement consultés (faux oublis, cf. section dédiée).")
        if cA >= cC:
            explications.append(
                "- **Le modèle seul fait aussi bien** : le monde est peut-être trop « devinable » "
                "par le modèle, ou les questions pas assez spécifiques.")
        w("\n".join(explications) if explications else "Voir détails ci-dessous.")
    w("")

    # — Faux oublis —
    w("## Faux oublis — faits VRAIS perdus par l'érosion (config C)\n")
    perdus = []
    for f in faits:
        sid = sid_vrai.get(f.fid)
        if sid is None:
            continue
        s = next((x for x in memC.souvenirs if x.id == sid), None)
        if s and (s.statut == "archive" or s.confiance < config.SEUIL_ARCHIVAGE):
            perdus.append((f, s))
    w(f"- **{len(perdus)} / {len(faits)} faits vrais** sont tombés sous le seuil ou ont été archivés "
      f"(jamais consultés assez pour entretenir la flamme).")
    if perdus:
        w("  Exemples :")
        for (f, s) in perdus[:5]:
            w(f"  - « {s.contenu} » (confiance {s.confiance:.2f}, {s.statut})")
    w("")

    # — Faillibilité du juge —
    jt, jf, jd = juge
    w("## Faillibilité du juge (mesurée pendant la chronologie)\n")
    taux = (100.0 * jf / jt) if jt else 0.0
    w(f"- Verdicts conséquents (CONFIRME/CONTREDIT) émis : **{jt}**.")
    w(f"- Verdicts **faux** vs vérité-terrain : **{jf}** (**{taux:.0f} %**).")
    if jd:
        w("  Exemples d'erreurs du juge :")
        for d in jd[:4]:
            w(f"  - {d['date']} — « {d['souvenir']} » jugé {d['verdict']} "
              f"(vrai à cette date : {d['souvenir_vrai_a_cette_date']})")
    w("")

    # — Courbe de confiance —
    w("## Confiance moyenne au fil du temps (config C) — vrais vs périmés\n")
    w("| Date | Confiance moy. VRAIS | Confiance moy. PÉRIMÉS | n vrais | n périmés |")
    w("|---|---|---|---|---|")
    for (d, mv, mp, nv, npp) in snapshots:
        w(f"| {d} | {mv if mv is not None else '—'} | {mp if mp is not None else '—'} | {nv} | {npp} |")
    w("\n*(Données aussi en CSV : `resultats/etape2_courbe_confiance.csv`.)*\n")

    # — 5 exemples commentés —
    w("## 5 exemples commentés\n")
    exemples = [l for l in lignes if l["categorie"] == "changé"][:5]
    for l in exemples:
        w(f"**Q : {l['question']}**  ")
        w(f"Vérité (valeur actuelle) : *{l['val_finale']}*  ")
        w(f"- A (seul) : « {l['A']} » → {'✅' if l['okA'] else '❌'}  ")
        w(f"- B (RAG inerte) : « {l['B']} » → {'✅' if l['okB'] else '❌'}  ")
        w(f"- C (mémoire qui trie) : « {l['C']} » → {'✅' if l['okC'] else '❌'}  ")
        w("")

    # — Échec du juge scindé (résultat, pas un détour) —
    w("## Annexe — l'échec du juge scindé (un résultat, pas un détour)\n")
    w("Avant de retenir la config championne, nous avons testé un **juge scindé** en deux "
      "détecteurs étanches : un détecteur de CONFLITS (ne voit que les souvenirs → produit les "
      "CONTREDIT) et un détecteur d'USAGE (voit la réponse → produit les CONFIRME), combinés par "
      "la règle **« le conflit bat l'usage »** (le monde bat l'opinion).\n")
    w("**Résultat : échec — 6 verdicts catastrophiques contre 1 pour le juge combiné simple.** "
      "Privé de la question et de la réponse, le détecteur de conflits devient *incohérent sur la "
      "comparaison de dates pures* (il contredit parfois le fait récent au lieu de l'ancien) et "
      "adjuge même les paires hors-sujet. La leçon : **le goulot n'est pas l'architecture du juge, "
      "c'est la fiabilité brute du modèle sur la récence ; lui donner plus de contexte (juge "
      "combiné) l'aide davantage que de l'isoler.** D'où la config retenue ici : juge combiné "
      "simple (V1) + souvenirs datés. La règle « le conflit bat l'usage » reste juste sur le plan "
      "conceptuel et le code est conservé (`cycle.juger_scinde`).\n")

    return "\n".join(R), res, succes


# ──────────────────────────────────────────────────────────────────────────
def main():
    assurer_dossiers()
    J = Journal("etape2")
    dire = J.dire
    dire("=" * 80)
    dire(" ÉTAPE 2 — EXPÉRIENCE (config championne, paramètres par défaut)")
    dire("=" * 80)

    dire("\n[1/5] Génération du monde synthétique…")
    faits = monde.generer_monde()
    questions_eval = monde.choisir_questions_eval(faits, config.N_QUESTIONS_EVAL)
    dire(f"  {len(faits)} faits, {sum(1 for f in faits if f.change)} changés, "
         f"{len(questions_eval)} questions d'éval.")

    dire("\n[2/5] Construction de la mémoire C (chronologie 12 mois)… (le plus long)")
    memC, meta, sid_vrai, snapshots, juge, n_consult = construire_memoire_C(faits, dire)

    dire("\n[3/5] Construction de la mémoire B (RAG inerte)…")
    memB = construire_memoire_B(faits)
    dire(f"  Config B : {len(memB.souvenirs)} souvenirs figés.")

    dire("\n[4/5] Évaluation des 3 configs sur les questions finales…")
    lignes = evaluer(questions_eval, memB, memC, dire)

    dire("\n[5/5] Rédaction du rapport…")
    texte, res, succes = ecrire_rapport(faits, questions_eval, lignes, snapshots, juge,
                                        memC, meta, sid_vrai, n_consult)

    chemin_rapport = os.path.join(config.DOSSIER_RESULTATS, "etape2_rapport.md")
    with open(chemin_rapport, "w", encoding="utf-8") as fp:
        fp.write(texte)

    # CSV courbe
    chemin_csv = os.path.join(config.DOSSIER_RESULTATS, "etape2_courbe_confiance.csv")
    with open(chemin_csv, "w", encoding="utf-8") as fp:
        fp.write("date,conf_vrais,conf_perimes,n_vrais,n_perimes\n")
        for (d, mv, mp, nv, npp) in snapshots:
            fp.write(f"{d},{mv},{mp},{nv},{npp}\n")

    # logs eval bruts
    chemin_log = os.path.join(config.DOSSIER_RESULTATS, "etape2_eval_detail.json")
    with open(chemin_log, "w", encoding="utf-8") as fp:
        json.dump(lignes, fp, ensure_ascii=False, indent=2)

    memC.sauvegarder(os.path.join(config.DOSSIER_RESULTATS, "etape2_memoireC_finale.json"))

    dire("\n" + "=" * 80)
    dire(" RÉSULTAT (faits changés = métrique décisive) :")
    dire(f"   A (seul)        : {res['A']['change']:.0f} %")
    dire(f"   B (RAG inerte)  : {res['B']['change']:.0f} %")
    dire(f"   C (mémoire trie): {res['C']['change']:.0f} %")
    dire(f"   → {'✅ SUCCÈS' if succes else '⚠ voir le rapport (échec expliqué)'}")
    dire("=" * 80)
    dire(f"\n Rapport   : {chemin_rapport}")
    dire(f" Courbe CSV: {chemin_csv}")
    dire(f" Détails   : {chemin_log}")
    dire(f" Journal   : {J.chemin}")
    J.fermer()


if __name__ == "__main__":
    main()
