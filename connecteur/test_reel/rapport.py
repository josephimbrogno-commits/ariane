# -*- coding: utf-8 -*-
"""
connecteur/test_reel/rapport.py — assemble le RAPPORT (markdown) du test en vraie vie : tableau
A/B/C par étage + global, et verbatims choisis. Notation mécanique (réutilise noter.classer).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
import verite_terrain as VT
import noter

ICI = os.path.dirname(os.path.abspath(__file__))
qmap = {q["id"]: q for q in VT.QUESTIONS}


def charger(nom):
    p = os.path.join(ICI, nom)
    return json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else None


def main():
    fichiers = [("1", "resultats_e1.json"), ("2", "resultats_e2.json"), ("3", "resultats_e3.json")]
    data = {et: charger(f) for et, f in fichiers}
    L = []
    w = L.append
    w("# Ariane face au monde réel — test du connecteur OpenClaw sur des faits datés (14/06/2026)\n")
    w("Vérité-terrain figée §1 (Euronext, FIFA, vérifiée à la main). Notation mécanique : "
      "OK = correct · **FAUX = périmé/menteur affirmé au présent** · REFUS = dit ne pas savoir.\n")
    w("- **A** = agent nu (qwen3:30b, sans mémoire) · **B** = memory-core natif (RAG Markdown) · "
      "**C** = notre mémoire (tri du périmé).\n")

    global_cnt = {c: {} for c in "ABC"}
    for et, res in data.items():
        if not res:
            continue
        ids = sorted(int(i) for i in res["A"].keys())
        w(f"\n## Étage {et}\n")
        w("| Q | attendu | A | B | C |")
        w("|---|---|---|---|---|")
        for qid in ids:
            q = qmap[qid]
            verdicts = {}
            for c in "ABC":
                v = noter.classer(res[c].get(str(qid), ""), q)
                verdicts[c] = v
                global_cnt[c][v] = global_cnt[c].get(v, 0) + 1
            w(f"| Q{qid} | {q['attendu'][:42]} | {verdicts['A']} | {verdicts['B']} | {verdicts['C']} |")

    w("\n## Synthèse globale\n")
    w("| Config | OK | FAUX | REFUS | AUTRE | %OK |")
    w("|---|---|---|---|---|---|")
    for c in "ABC":
        n = sum(global_cnt[c].values())
        ok = global_cnt[c].get("OK", 0)
        w(f"| {c} | {ok} | {global_cnt[c].get('FAUX',0)} | {global_cnt[c].get('REFUS',0)} "
          f"| {global_cnt[c].get('AUTRE',0)} | {100*ok/max(1,n):.0f}% |")

    # verbatims clés
    w("\n## Verbatims clés (pour l'article)\n")
    cibles = [("1", 7, "Alstom — sortie 2024 (le confidently wrong)"),
              ("3", 10, "Teleperformance « revenue 2026 » (menteur)"),
              ("3", 12, "Italie « qualifiée » (menteur mono-source)"),
              ("2", 8, "Cours du CAC aujourd'hui (le piège)")]
    for et, qid, titre in cibles:
        res = data.get(et)
        if not res:
            continue
        w(f"\n**{titre}** — Q{qid} : « {qmap[qid]['q']} »")
        for c in "ABC":
            a = noter.nettoyer(res[c].get(str(qid), ""))
            a = a if len(a) <= 280 else a[:277] + "..."
            w(f"- **{c}** [{noter.classer(res[c].get(str(qid), ''), qmap[qid])}] : {a}")

    # — variante B-naïf vs C : le décrochage du RAG naïf —
    bn = charger("resultats_bnaif.json")
    e_par_q = {}
    for et in ("1", "2", "3"):
        if data.get(et):
            for q in VT.QUESTIONS:
                if str(q["id"]) in data[et].get("C", {}):
                    e_par_q[q["id"]] = data[et]
    if bn:
        bn = bn["Bnaif"]
        w("\n## B-naïf vs C — le décrochage du RAG sans discipline de notes\n")
        w("Mêmes questions, mais le RAG natif a des notes **naïves** (appartenance jamais mise à jour, "
          "sorties non enregistrées, sources non étiquetées) — le cas réel fréquent.\n")
        w("| Q | B-naïf | C | attendu |")
        w("|---|---|---|---|")
        nb_ok = nc_ok = 0
        for qid in sorted(int(i) for i in bn.keys()):
            q = qmap[qid]
            vb = noter.classer(bn[str(qid)], q)
            cans = e_par_q.get(qid, {}).get("C", {}).get(str(qid), "")
            vc = noter.classer(cans, q)
            nb_ok += vb == "OK"; nc_ok += vc == "OK"
            w(f"| Q{qid} | {vb} | {vc} | {q['attendu'][:38]} |")
        w(f"\n**B-naïf {nb_ok}/{len(bn)} · C {nc_ok}/{len(bn)}** sur ces cas. Verbatims B-naïf :\n")
        for qid in sorted(int(i) for i in bn.keys()):
            a = noter.nettoyer(bn[str(qid)])
            a = a if len(a) <= 220 else a[:217] + "..."
            w(f"- **Q{qid}** [{noter.classer(bn[str(qid)], qmap[qid])}] : {a}")

    w("\n## Lecture (honnête)\n")
    w("- **A (agent nu) s'effondre** : confidently wrong sur les faits datés (connaissances figées).\n"
      "- **B bien nourri ≈ C** : avec un modèle capable ET des notes datées/sourcées propres, le RAG "
      "égale la mémoire structurée sur ces questions. La thèse « le tri bat le rappel » NE tient PAS "
      "quand le RAG est bien tenu.\n"
      "- **B-naïf s'effondre là où C tient** : sans discipline de notes, le RAG sert le périmé et les "
      "menteurs avec aplomb. **La valeur de C n'est pas d'être plus maligne que le RAG, mais de rendre "
      "la correction STRUCTURELLE** — indépendante de la qualité des notes et du re-raisonnement du modèle.\n"
      "- **Limites mesurées** : extraction du greffier ~40 % sur langage réel (ontologie synthétique ne "
      "couvre pas « qualifié pour », « est entrée dans ») → vérité injectée en triplets exacts ; rendu "
      "n'expose pas la date d'ENTRÉE (échec Q4) ; flood de nœud-hub corrigé côté connecteur (focus).\n")

    rapport = "\n".join(L) + "\n"
    chemin = os.path.join(ICI, "RAPPORT_REEL.md")
    open(chemin, "w", encoding="utf-8").write(rapport)
    print(rapport)
    print(f"\n=> écrit : {chemin}")


if __name__ == "__main__":
    main()
