# -*- coding: utf-8 -*-
"""
etape3_sensibilite.py — RUN DE SENSIBILITÉ (étape 3).

Rejoue l'expérience de l'étape 2 en balayant la DEMI-VIE d'érosion (60 / 120 / 240 j),
tous les autres paramètres mémoire inchangés. Ajoute un baseline B′ « vraiment aveugle »
(RAG inerte SANS date dans le texte injecté), pour isoler le vrai apport des métadonnées
datées de la config C.

Produit :
  - resultats/etape3_rapport.md   (sensibilité, croisement C↔B, note méthodo sur B, limite juge)
  - resultats/etape3_dashboard.html (tableau de bord statique : courbes + explorateur)
  - resultats/etape3_data.json     (données brutes)
  - resultats/etape3_courbe_hlXX.csv

Lance :  python etape3_sensibilite.py
"""

import json
import os
import sys

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

from etape2_experience import (
    correct, construire_memoire_C, construire_memoire_B, precision,
)

DEMI_VIES = [60, 120, 240]
CONSULT_PAR_MOIS_ETAPE3 = 10   # un peu plus léger que l'étape 2 (3 reconstructions de C)


def construire_memoire_B_prime(faits):
    """B′ — RAG inerte VRAIMENT aveugle : énoncés SANS date (ni dans le texte ni en méta)."""
    mem = Memoire(HorlogeVirtuelle(config.MONDE_FIN))
    for f in faits:
        mem.ajouter(f.enonce_init(), date=f.date_init)
        if f.change:
            mem.ajouter(f.enonce_final_sansdate(), date=f.date_change)
    return mem


def eval_base(questions, memB, memB2, dire):
    """Réponses A / B / B′ — indépendantes de la demi-vie, calculées une seule fois."""
    out = []
    for i, f in enumerate(questions, start=1):
        att = f.cle_vraie_finale()
        a = cycle.repondre_A(f.question)
        b, _ = cycle.repondre_B(memB, f.question)
        bp, _ = cycle.repondre_B(memB2, f.question)
        out.append({
            "fid": f.fid, "question": f.question, "categorie": f.categorie(),
            "attendu": att, "val": f.val_finale if f.change else f.val_init,
            "A": a, "okA": correct(a, att),
            "B": b, "okB": correct(b, att),
            "Bp": bp, "okBp": correct(bp, att),
        })
        if i % 20 == 0:
            dire(f"    base …{i}/{len(questions)}")
    return out


def eval_C(questions, memC):
    res = {}
    for f in questions:
        c, _ = cycle.repondre_C(memC, f.question)
        res[f.fid] = (c, correct(c, f.cle_vraie_finale()))
    return res


def faux_oublis(memC, faits, sid_vrai):
    n = 0
    for f in faits:
        sid = sid_vrai.get(f.fid)
        if sid is None:
            continue
        s = next((x for x in memC.souvenirs if x.id == sid), None)
        if s and (s.statut == "archive" or s.confiance < config.SEUIL_ARCHIVAGE):
            n += 1
    return n


# ──────────────────────────────────────────────────────────────────────────
def main():
    assurer_dossiers()
    J = Journal("etape3")
    dire = J.dire
    config.CONSULT_CIBLE_PAR_MOIS = CONSULT_PAR_MOIS_ETAPE3

    dire("=" * 80)
    dire(" ÉTAPE 3 — SENSIBILITÉ à la demi-vie (60/120/240 j) + baseline B′ aveugle")
    dire("=" * 80)

    faits = monde.generer_monde()
    questions = monde.choisir_questions_eval(faits, config.N_QUESTIONS_EVAL)
    dire(f"\nMonde : {len(faits)} faits ({sum(1 for f in faits if f.change)} changés), "
         f"{len(questions)} questions d'éval.")

    dire("\n[Baselines] A (seul), B (inerte daté), B′ (inerte aveugle)…")
    memB = construire_memoire_B(faits)
    memB2 = construire_memoire_B_prime(faits)
    base = eval_base(questions, memB, memB2, dire)
    precB = {cat or "global": precision(base, "B", cat)[0] for cat in (None, "changé", "stable")}
    precBp = {cat or "global": precision(base, "Bp", cat)[0] for cat in (None, "changé", "stable")}
    precA = {cat or "global": precision(base, "A", cat)[0] for cat in (None, "changé", "stable")}

    # — Balayage demi-vie —
    resultats = []
    courbes = {}
    qC = {}   # fid -> {hl: (reponse, ok)}
    for hl in DEMI_VIES:
        dire(f"\n[Demi-vie {hl} j] construction de C…")
        config.DEMI_VIE_JOURS = float(hl)
        memC, meta, sid_vrai, snaps, juge, nconsult = construire_memoire_C(faits, dire)
        cmap = eval_C(questions, memC)
        for fid, (rep, ok) in cmap.items():
            qC.setdefault(fid, {})[hl] = (rep, ok)
        lignes = [{**b, "C": cmap[b["fid"]][0], "okC": cmap[b["fid"]][1]} for b in base]
        precC = {cat or "global": precision(lignes, "C", cat)[0] for cat in (None, "changé", "stable")}
        jt, jf, _ = juge
        fo = faux_oublis(memC, faits, sid_vrai)
        resultats.append({
            "demi_vie": hl, "n_actifs": len(memC.actifs()), "n_consult": nconsult,
            "prec_C": precC, "faux_oublis": fo, "n_faits": len(faits),
            "juge_total": jt, "juge_faux": jf,
        })
        courbes[hl] = snaps
        # CSV
        with open(os.path.join(config.DOSSIER_RESULTATS, f"etape3_courbe_hl{hl}.csv"),
                  "w", encoding="utf-8") as fp:
            fp.write("date,conf_vrais,conf_perimes,n_vrais,n_perimes\n")
            for (d, mv, mp, nv, npp) in snaps:
                fp.write(f"{d},{mv},{mp},{nv},{npp}\n")
        dire(f"   → C: global {precC['global']:.0f}% | changés {precC['changé']:.0f}% | "
             f"stables {precC['stable']:.0f}% | actifs {len(memC.actifs())} | faux oublis {fo}")

    # — Croisement C ↔ B / B′ sur les faits changés —
    def croisement(ref):
        precedent = None
        for r in resultats:
            c = r["prec_C"]["changé"]
            if c > ref:
                if precedent is None:
                    return f"dès {r['demi_vie']} j (C={c:.0f}% > {ref:.0f}%)"
                return f"entre {precedent} et {r['demi_vie']} j (à {r['demi_vie']} j : C={c:.0f}% > {ref:.0f}%)"
            precedent = r["demi_vie"]
        return f"jamais sur la plage testée (C max < {ref:.0f}%)"

    crois_B = croisement(precB["changé"])
    crois_Bp = croisement(precBp["changé"])

    # ── DONNÉES (dashboard + inspection) ─────────────────────────────────
    data = {
        "params": {
            "repondeur": config.MODELE_LLM, "juge": config.MODELE_JUGE,
            "gain": config.GAIN_CONFIRMATION, "perte": config.PERTE_CONTRADICTION,
            "seuil_archivage": config.SEUIL_ARCHIVAGE,
            "consult_par_mois": CONSULT_PAR_MOIS_ETAPE3,
            "chronologie": f"{config.MONDE_DEBUT:%Y-%m-%d} → {config.MONDE_FIN:%Y-%m-%d}",
            "n_faits": len(faits), "n_changes": sum(1 for f in faits if f.change),
            "n_questions": len(questions),
        },
        "baselines": {"A": precA, "B": precB, "Bprime": precBp},
        "hls": [{"demi_vie": r["demi_vie"], "prec_C": r["prec_C"], "faux_oublis": r["faux_oublis"],
                 "n_actifs": r["n_actifs"], "n_faits": r["n_faits"],
                 "juge_total": r["juge_total"], "juge_faux": r["juge_faux"],
                 "courbe": [{"date": d, "vrais": mv, "perimes": mp, "nv": nv, "np": npp}
                            for (d, mv, mp, nv, npp) in courbes[r["demi_vie"]]]}
                for r in resultats],
        "croisement_B": crois_B, "croisement_Bprime": crois_Bp,
        "questions": [{
            "question": b["question"], "categorie": b["categorie"], "attendu": b["val"],
            "A": b["A"], "okA": b["okA"], "B": b["B"], "okB": b["okB"],
            "Bp": b["Bp"], "okBp": b["okBp"],
            "C": {str(hl): qC[b["fid"]][hl][0] for hl in DEMI_VIES},
            "okC": {str(hl): qC[b["fid"]][hl][1] for hl in DEMI_VIES},
        } for b in base],
    }
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape3_data.json"), "w",
              encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)

    # ── RAPPORT MARKDOWN ─────────────────────────────────────────────────
    ecrire_rapport_md(data, resultats, precA, precB, precBp, crois_B, crois_Bp)
    # ── DASHBOARD HTML ───────────────────────────────────────────────────
    ecrire_dashboard(data)

    dire("\n" + "=" * 80)
    dire(" SENSIBILITÉ (faits changés) :")
    dire(f"   B (inerte daté)   : {precB['changé']:.0f} %   |   B′ (aveugle) : {precBp['changé']:.0f} %")
    for r in resultats:
        dire(f"   C @ demi-vie {r['demi_vie']:>3} j : {r['prec_C']['changé']:.0f} %   "
             f"(actifs {r['n_actifs']}, faux oublis {r['faux_oublis']})")
    dire(f"   Croisement C>B  : {crois_B}")
    dire(f"   Croisement C>B′ : {crois_Bp}")
    dire("=" * 80)
    dire(f"\n Rapport   : resultats/etape3_rapport.md")
    dire(f" Dashboard : resultats/etape3_dashboard.html")
    dire(f" Données   : resultats/etape3_data.json")
    dire(f" Journal   : {J.chemin}")
    J.fermer()


# ──────────────────────────────────────────────────────────────────────────
def ecrire_rapport_md(data, resultats, precA, precB, precBp, crois_B, crois_Bp):
    R = []
    w = R.append
    p = data["params"]
    w("# Étape 3 — Run de sensibilité (demi-vie) + baseline B′ aveugle\n")
    w("## Paramètres\n")
    w(f"- Répondeur `{p['repondeur']}` · Juge `{p['juge']}` (prompt découplé simple V1).")
    w(f"- Gain +{p['gain']} · Perte −{p['perte']} · Seuil archivage {p['seuil_archivage']}.")
    w(f"- **Demi-vie balayée : {', '.join(str(r['demi_vie']) for r in resultats)} jours** "
      f"(seul curseur modifié).")
    w(f"- Chronologie {p['chronologie']} · {p['n_faits']} faits ({p['n_changes']} changés) · "
      f"{p['n_questions']} questions · ~{p['consult_par_mois']} consultations/mois.\n")

    w("## Note méthodologique — contamination de B par les dates textuelles\n")
    w("Dans l'étape 2, le RAG inerte **B** s'est révélé étonnamment fort (70 % sur les faits "
      "changés). La raison : les énoncés de mise à jour contiennent la date **dans le texte** "
      "(« *Depuis mai 2026*, le PDG est… »). Même sans métadonnées, le modèle lit donc la récence "
      "et choisit souvent le bon fait. **B n'est donc pas un baseline réellement « aveugle ».**\n")
    w("On ajoute ici **B′**, identique à B mais dont le texte injecté est *débarrassé de toute "
      "date* (« Le PDG est X » pour l'ancienne ET la nouvelle valeur). B′ est le vrai « entrepôt "
      "inerte qui ressort l'ancien et le nouveau en vrac », sans aucun indice de récence. "
      "**L'écart C − B′ mesure le véritable apport des métadonnées datées de la mémoire qui trie.**\n")

    w("## Résultats — précision sur les faits CHANGÉS (métrique décisive)\n")
    w("| Configuration | Faits changés | Faits stables | Globale |")
    w("|---|---|---|---|")
    w(f"| A — modèle seul | {precA['changé']:.0f} % | {precA['stable']:.0f} % | {precA['global']:.0f} % |")
    w(f"| B — RAG inerte **daté** | {precB['changé']:.0f} % | {precB['stable']:.0f} % | {precB['global']:.0f} % |")
    w(f"| B′ — RAG inerte **aveugle** | {precBp['changé']:.0f} % | {precBp['stable']:.0f} % | {precBp['global']:.0f} % |")
    for r in resultats:
        c = r["prec_C"]
        w(f"| **C — mémoire qui trie (demi-vie {r['demi_vie']} j)** | **{c['changé']:.0f} %** | "
          f"{c['stable']:.0f} % | {c['global']:.0f} % |")
    w("")

    w("## Sensibilité : précision-C vs faux oublis, au fil de la demi-vie\n")
    w("| Demi-vie | C (changés) | C (stables) | C (global) | Souvenirs actifs | "
      "Faux oublis (faits vrais perdus) |")
    w("|---|---|---|---|---|---|")
    for r in resultats:
        c = r["prec_C"]
        w(f"| {r['demi_vie']} j | {c['changé']:.0f} % | {c['stable']:.0f} % | {c['global']:.0f} % | "
          f"{r['n_actifs']} / {r['n_faits']*1} | {r['faux_oublis']} / {r['n_faits']} |")
    w("\n*Lecture : une demi-vie plus longue garde plus de souvenirs vivants (moins de faux "
      "oublis) et fait monter la précision de C — au prix d'une mémoire qui « oublie » moins, "
      "donc potentiellement plus encombrée d'anciens faits.*\n")

    w("## Point de croisement (sur les faits changés)\n")
    w(f"- **C dépasse B (inerte daté)** : {crois_B}.")
    w(f"- **C dépasse B′ (inerte aveugle)** : {crois_Bp}.")
    w("")
    cmax = max(r["prec_C"]["changé"] for r in resultats)
    if cmax > precBp["changé"]:
        w("➡️ **Contre B′ (la vraie comparaison équitable), la mémoire qui trie démontre son "
          "avantage** dès que la demi-vie laisse sa mémoire respirer : dater et hiérarchiser les "
          "souvenirs bat l'entrepôt aveugle qui ressort l'ancien et le nouveau en vrac.")
    else:
        w("➡️ Même contre B′, C ne prend pas l'avantage sur la plage testée — voir la limite du "
          "juge ci-dessous et l'encombrement de la mémoire par les anciens faits non contredits.")
    if cmax <= precB["changé"]:
        w("\n⚠️ **Contre B (daté), C ne passe pas devant** : tant que les énoncés portent la date "
          "dans le texte, l'entrepôt inerte profite gratuitement de la récence. C'est précisément "
          "ce que B′ neutralise.")
    w("")

    w("## Limite connue (non retouchée pendant le balayage) — faillibilité du juge\n")
    tot = sum(r["juge_total"] for r in resultats)
    fau = sum(r["juge_faux"] for r in resultats)
    taux = 100.0 * fau / tot if tot else 0
    w(f"- Sur l'ensemble des reconstructions, le juge a émis {tot} verdicts conséquents, dont "
      f"**{fau} faux ({taux:.0f} %)** vs vérité-terrain.")
    w("- Conformément à l'étape 1, **ces erreurs sont des fausses contradictions de faits "
      "ACTUELS** (le juge contredit parfois le récent). Cette limite est **documentée et "
      "laissée telle quelle** pendant le balayage, pour ne pas confondre l'effet de la demi-vie "
      "avec un changement de juge.\n")

    w("## Courbes de confiance (vrais vs périmés) — résumé\n")
    for r in resultats:
        snaps = data["hls"]
        courbe = next(h["courbe"] for h in snaps if h["demi_vie"] == r["demi_vie"])
        fin = courbe[-1]
        w(f"- **Demi-vie {r['demi_vie']} j** : à la fin, confiance moyenne VRAIS = "
          f"{fin['vrais']}, PÉRIMÉS = {fin['perimes']} "
          f"(CSV : `resultats/etape3_courbe_hl{r['demi_vie']}.csv`). "
          f"Détail visuel dans le dashboard.")
    w("")

    w("## Tableau de bord interactif\n")
    w("Ouvrir **`resultats/etape3_dashboard.html`** dans un navigateur : courbes de confiance "
      "par demi-vie, et explorateur question-par-question des réponses A / B / B′ / C.\n")

    w("## Annexe — l'échec du juge scindé (rappel)\n")
    w("Pour mémoire : un juge scindé (conflits ⟂ usage, règle « le conflit bat l'usage ») a été "
      "testé et **a échoué** (6 verdicts catastrophiques vs 1 pour le juge combiné simple), car le "
      "détecteur de conflits, privé de contexte, devient incohérent sur les dates. La config "
      "retenue reste le **juge combiné simple (V1) + souvenirs datés**. Un résultat, pas un détour.\n")

    with open(os.path.join(config.DOSSIER_RESULTATS, "etape3_rapport.md"),
              "w", encoding="utf-8") as fp:
        fp.write("\n".join(R))


# ──────────────────────────────────────────────────────────────────────────
def ecrire_dashboard(data):
    """Dashboard HTML statique, autonome (données JSON embarquées)."""
    js_data = json.dumps(data, ensure_ascii=False)
    html = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>La mémoire qui trie — Tableau de bord (étape 3)</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#0f1117;color:#e6e6e6}
 header{padding:18px 28px;background:#161a23;border-bottom:1px solid #262c3a}
 h1{margin:0;font-size:20px} h2{font-size:16px;color:#9fb4ff;margin:26px 0 10px}
 main{max-width:1100px;margin:0 auto;padding:20px 28px 60px}
 table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 18px}
 th,td{border:1px solid #2a3142;padding:6px 9px;text-align:left}
 th{background:#1b2030;color:#cdd6f4} tr:nth-child(even){background:#141824}
 .ok{color:#86efac;font-weight:600}.ko{color:#fca5a5}
 .pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;background:#22304a;color:#9fb4ff}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
 .card{background:#141824;border:1px solid #262c3a;border-radius:10px;padding:12px}
 select,input{background:#1b2030;color:#e6e6e6;border:1px solid #2a3142;border-radius:6px;padding:5px 8px}
 .muted{color:#8a93a6;font-size:12px} svg{background:#0c0e14;border-radius:8px}
 .leg{font-size:11px} .leg b{font-weight:700}
</style></head><body>
<header><h1>🔥 La mémoire qui trie — tableau de bord (étape 3)</h1>
<div class="muted" id="sub"></div></header>
<main>
 <h2>1 · Précision sur les faits changés (métrique décisive)</h2>
 <table id="tprec"></table>
 <div class="muted" id="crois"></div>

 <h2>2 · Courbes de confiance — VRAIS vs PÉRIMÉS, par demi-vie</h2>
 <div class="leg">Légende : <b style="color:#86efac">vrais</b> · <b style="color:#fca5a5">périmés</b> · ligne pointillée = seuil d'archivage 0.15</div>
 <div class="grid" id="curves"></div>

 <h2>3 · Explorateur question par question</h2>
 <div class="muted">Colonne C pour la demi-vie :
   <select id="hlSel"></select>
   &nbsp; Filtre : <select id="catSel"><option value="">toutes</option><option value="changé">changées</option><option value="stable">stables</option></select>
 </div>
 <table id="tq"></table>
</main>
<script>
const D = __DATA__;
const tick = b => b ? '<span class="ok">✓</span>' : '<span class="ko">✗</span>';
document.getElementById('sub').textContent =
  `Répondeur ${D.params.repondeur} · Juge ${D.params.juge} · ${D.params.n_faits} faits (${D.params.n_changes} changés) · ${D.params.n_questions} questions · chronologie ${D.params.chronologie}`;

// 1 · table précision
(()=>{
 let h='<tr><th>Configuration</th><th>Faits changés</th><th>Stables</th><th>Globale</th></tr>';
 const row=(n,p)=>`<tr><td>${n}</td><td><b>${p['changé'].toFixed(0)}%</b></td><td>${p.stable.toFixed(0)}%</td><td>${p.global.toFixed(0)}%</td></tr>`;
 h+=row('A — modèle seul',D.baselines.A);
 h+=row('B — RAG inerte <i>daté</i>',D.baselines.B);
 h+=row('B′ — RAG inerte <i>aveugle</i>',D.baselines.Bprime);
 D.hls.forEach(x=>h+=row(`<b>C — mémoire qui trie · demi-vie ${x.demi_vie} j</b>`,x.prec_C));
 document.getElementById('tprec').innerHTML=h;
 document.getElementById('crois').innerHTML=
   `Croisement C &gt; B : <b>${D.croisement_B}</b> &nbsp;·&nbsp; C &gt; B′ : <b>${D.croisement_Bprime}</b>`;
})();

// 2 · courbes SVG
(()=>{
 const W=320,H=150,pad=26;
 const draw=(c)=>{
   const pts=c.courbe;
   const xs=(i)=>pad+(W-2*pad)*i/(pts.length-1);
   const ys=(v)=>H-pad-(H-2*pad)*Math.max(0,Math.min(0.7,v||0))/0.7;
   const line=(key,col)=>{
     let d='';pts.forEach((p,i)=>{const v=p[key];if(v==null)return;d+=(d?'L':'M')+xs(i).toFixed(1)+' '+ys(v).toFixed(1)+' ';});
     return `<path d="${d}" fill="none" stroke="${col}" stroke-width="2"/>`;};
   const seuil=ys(0.15);
   const ticks=pts.map((p,i)=>i%2?'':`<text x="${xs(i)}" y="${H-8}" fill="#6b7280" font-size="9" text-anchor="middle">${p.date.slice(5)}</text>`).join('');
   return `<div class="card"><b>Demi-vie ${c.demi_vie} j</b> <span class="pill">${c.n_actifs} actifs · ${c.faux_oublis} faux oublis</span>
     <svg viewBox="0 0 ${W} ${H}" width="100%">
      <line x1="${pad}" y1="${seuil}" x2="${W-pad}" y2="${seuil}" stroke="#fbbf24" stroke-dasharray="4 3" stroke-width="1"/>
      <text x="${W-pad}" y="${seuil-3}" fill="#fbbf24" font-size="9" text-anchor="end">seuil 0.15</text>
      ${line('vrais','#86efac')}${line('perimes','#fca5a5')}
      <text x="4" y="14" fill="#8a93a6" font-size="9">conf</text>${ticks}
     </svg></div>`;};
 document.getElementById('curves').innerHTML=D.hls.map(draw).join('');
})();

// 3 · explorateur
(()=>{
 const hlSel=document.getElementById('hlSel');
 D.hls.forEach(x=>{const o=document.createElement('option');o.value=x.demi_vie;o.textContent=x.demi_vie+' j';hlSel.appendChild(o);});
 hlSel.value=D.hls[Math.floor(D.hls.length/2)].demi_vie;
 const catSel=document.getElementById('catSel');
 const render=()=>{
   const hl=hlSel.value, cat=catSel.value;
   let h='<tr><th>Question</th><th>cat.</th><th>Vérité</th><th>A</th><th>B (daté)</th><th>B′ (aveugle)</th><th>C ('+hl+'j)</th></tr>';
   D.questions.filter(q=>!cat||q.categorie===cat).forEach(q=>{
     h+=`<tr><td>${q.question}</td><td><span class="pill">${q.categorie}</span></td><td>${q.attendu}</td>
       <td>${tick(q.okA)}</td><td>${tick(q.okB)}</td><td>${tick(q.okBp)}</td><td>${tick(q.okC[hl])}</td></tr>`;});
   document.getElementById('tq').innerHTML=h;};
 hlSel.onchange=render;catSel.onchange=render;render();
})();
</script></body></html>"""
    html = html.replace("__DATA__", js_data)
    with open(os.path.join(config.DOSSIER_RESULTATS, "etape3_dashboard.html"),
              "w", encoding="utf-8") as fp:
        fp.write(html)


if __name__ == "__main__":
    main()
