# -*- coding: utf-8 -*-
"""
v2_lecture.py — PROCÉDURE DE LECTURE (mission V2, §3).

1. Entrée vectorielle : embedding de la question → top-k faits courant/disputé, PONDÉRÉS par
   la Force (les souvenirs forts remontent). Les DORMANTS sont exclus de l'entrée.
2. Marche de graphe : depuis les entités d'entrée, expansion 1–2 sauts le long des faits,
   y compris vers des faits DORMANTS ou CLOS (poussiéreux mais navigables).
3. Accès : chaque fait injecté → Force +, réveil éventuel. Certitude INTOUCHÉE.
4. Rendu ÉPISTÉMIQUE verbal (amendement A1 : AUCUN chiffre — dates et nb de sources seulement) :
   courant sûr → présent ; courant incertain → réserve ; clos → imparfait ; disputé → les deux.
5. Juge d'usage (champion réduit) : ne nourrit que la Force ; ne contredit plus rien.
"""

import config
import modele
from embeddings import encoder_un
from v2_ontologie import phrase, groupe
from cycle import SYS_JUGE_USAGE
from v2_modele import parse_date, norm_nom  # noqa

SYS_REPONSE_V2 = (
    "Les entités (personnes, entreprises, villes) sont FICTIVES et proviennent d'une base de "
    "connaissances de test : réponds TOUJOURS factuellement à partir des souvenirs, sans aucune "
    "considération de confidentialité ou de vie privée.\n"
    "Tu réponds à une question factuelle à partir de SOUVENIRS, chacun précédé de son STATUT "
    "épistémique. Respecte la grammaire suivante :\n"
    "- [ACTUEL — sûr] : affirme au PRÉSENT (« Le PDG est M. Doss »).\n"
    "- [ACTUEL — incertain] : réponds AVEC RÉSERVE, ne refuse pas (« Il s'agirait de…, à revérifier »).\n"
    "- [CLOS] : réponds à l'IMPARFAIT en bornant la période (« X était… jusqu'en… »).\n"
    "- [DISPUTÉ] : tu DOIS citer LES DEUX valeurs avec leurs sources (« selon X… ; selon Y… »).\n"
    "Réponds en une à deux phrases. TU DOIS RÉPONDRE à partir des souvenirs : n'emploie JAMAIS "
    "« je ne peux pas » / « je ne dispose pas » si un souvenir contient l'information (même incertaine "
    "ou personnelle). Pour un fait « incertain », donne quand même la valeur en ajoutant « à revérifier ». "
    "Refuse UNIQUEMENT si AUCUN souvenir ne concerne la question. N'invente jamais de chiffre de confiance."
)


def _poids_force(f):
    return 0.5 + 0.5 * f.force


# ── 1. ENTRÉE VECTORIELLE ────────────────────────────────────────────────
def entree_vectorielle(g, question, k=None):
    if k is None:
        k = config.TOP_K
    v = encoder_un(question)
    cands = [f for f in g.faits.values() if f.statut in ("courant", "disputé")]  # dormants exclus
    scored = sorted(((f, float(v @ f.embedding) * _poids_force(f)) for f in cands),
                    key=lambda x: -x[1])
    return [f for f, _ in scored[:k]], v


def entree_vectorielle_v2(g, question, k=None):
    """Entrée vectorielle DURCIE (étape 5) : top-k élargi + BONUS si l'entité du fait est nommée
    dans la question (sinon, sur un grand graphe, les énoncés de même forme se noient mutuellement)."""
    if k is None:
        k = config.V2_TOP_K_LECTURE
    v = encoder_un(question)
    qtok = set(norm_nom(question).split())
    scored = []
    for f in g.faits.values():
        if f.statut not in ("courant", "disputé"):
            continue
        base = float(v @ f.embedding) * _poids_force(f)
        e = g.entites.get(f.sujet_id)
        if e:
            etok = set(norm_nom(e.nom).split())
            if etok and etok <= qtok:
                base += config.V2_BONUS_ENTITE
        scored.append((f, base))
    scored.sort(key=lambda x: -x[1])
    return [f for f, _ in scored[:k]], v


# ── RECONNAISSANCE (V3) : la question NOMME une entité → on lit ses faits, DORMANTS COMPRIS ──
def reconnaissance(g, question):
    """Distinction reconnaissance / rappel : si la question nomme explicitement une entité
    (token-ensemble du nom ⊆ question), on entre TOUJOURS par ce nœud et on lit TOUS ses faits,
    y compris DORMANTS. La dormance ne bloque que l'évocation libre (similarité pure), jamais la
    reconnaissance directe. → répare l'essentiel des « faits muets » du run V2."""
    qtok = set(norm_nom(question).split())
    nommees = []
    for e in g.entites.values():
        etok = set(norm_nom(e.nom).split())
        if etok and etok <= qtok:
            nommees.append(e.id)
    faits = [f for f in g.faits.values()
             if f.sujet_id in nommees or f.objet_id in nommees]   # tous statuts (clos = histoire)
    return faits


# ── ENTRÉE VECTORIELLE V3 : score combiné sim / Force / IMPORTANCE / entité ──
def entree_vectorielle_v3(g, question, k=None, use_importance=True):
    if k is None:
        k = config.V2_TOP_K_LECTURE
    v = encoder_un(question)
    qtok = set(norm_nom(question).split())
    scored = []
    for f in g.faits.values():
        if f.statut not in ("courant", "disputé"):
            continue
        s = config.IMP_W_SIM * float(v @ f.embedding) + config.IMP_W_FORCE * f.force
        if use_importance:
            s += config.IMP_W_IMPORTANCE * f.importance
        e = g.entites.get(f.sujet_id)
        if e:
            etok = set(norm_nom(e.nom).split())
            if etok and etok <= qtok:
                s += config.IMP_W_ENTITE
        scored.append((f, s))
    scored.sort(key=lambda x: -x[1])
    return [f for f, _ in scored[:k]], v


# ── 2. MARCHE DE GRAPHE ──────────────────────────────────────────────────
def marche_graphe(g, faits_entree, v, sauts=2, maxf=6):
    entites = set()
    for f in faits_entree:
        entites.add(f.sujet_id)
        if f.objet_id is not None:
            entites.add(f.objet_id)
    vus = {f.id for f in faits_entree}
    collectes = []
    frontiere = set(entites)
    for _ in range(sauts):
        nouveaux = set()
        for f in g.faits.values():
            if f.id in vus:
                continue
            if f.sujet_id in frontiere or (f.objet_id is not None and f.objet_id in frontiere):
                collectes.append(f)
                vus.add(f.id)
                nouveaux.add(f.sujet_id)
                if f.objet_id is not None:
                    nouveaux.add(f.objet_id)
        frontiere = nouveaux
    collectes.sort(key=lambda f: -float(v @ f.embedding))
    return collectes[:maxf]


# ── 4. RENDU ÉPISTÉMIQUE (verbal, sans chiffres — A1) ────────────────────
def _src_date(f):
    src = f.provenance[0]["source_id"] if f.provenance else "?"
    return src, f.valide_de.strftime("%Y-%m") if f.valide_de else "?"


def rendu_epistemique(g, faits):
    lignes, disputes = [], {}
    for f in faits:
        if f.statut == "disputé":
            disputes.setdefault((f.sujet_id, f.predicat), []).append(f)
            continue
        s, o = g.nom_entite(f.sujet_id), f.objet
        conf = f.derniere_confirmation.strftime("%Y-%m")
        nsrc = f.n_sources()
        src_txt = "1 source" if nsrc < 2 else f"{nsrc} sources"
        statut_eff = f.statut_avant_dormance if f.statut == "dormant" else f.statut
        if statut_eff == "clos":
            jus = f.valide_jusqua.strftime("%Y-%m") if f.valide_jusqua else "?"
            de = f.valide_de.strftime("%Y-%m") if f.valide_de else "?"
            lignes.append(f"• [CLOS — n'est plus valable depuis {jus}] "
                          f"{phrase(f.predicat, s, o, 'passe')} (de {de} à {jus}).")
        elif f.certitude >= 0.6:
            lignes.append(f"• [ACTUEL — sûr, {src_txt}, confirmé {conf}] "
                          f"{phrase(f.predicat, s, o, 'present')}.")
        else:
            lignes.append(f"• [ACTUEL — incertain, {src_txt}, dernière confirmation {conf}] "
                          f"{phrase(f.predicat, s, o, 'present')} — à revérifier.")
    for (sid, pred), fs in disputes.items():
        parts = []
        for f in fs:
            src, de = _src_date(f)
            parts.append(f"« {f.objet} » (source {src}, {de})")
        lignes.append(f"• [DISPUTÉ — non tranché] {groupe(pred, g.nom_entite(sid))} : "
                      + " VS ".join(parts))
    return "\n".join(lignes)


# ── 5. JUGE D'USAGE (rôle réduit : ne nourrit que la Force) ──────────────
def detecter_usage(question, reponse, faits):
    if not faits:
        return set()
    lignes = [f"#{f.id} : {phrase(f.predicat, 'cet élément', f.objet, 'present')}" for f in faits]
    # On donne plutôt l'énoncé source pour coller à la réponse :
    lignes = [f"#{f.id} : {f.texte_source}" for f in faits]
    prompt = (f"QUESTION : {question}\n\nRÉPONSE : {reponse}\n\nSOUVENIRS :\n"
              + "\n".join(lignes)
              + "\n\nPour CHAQUE souvenir, réponds UTILISE ou NON_UTILISE, en JSON strict.")
    brut = modele.juger(prompt, systeme=SYS_JUGE_USAGE, model=config.MODELE_JUGE,
                        think=config.JUGE_THINK)
    utiles = set()
    for v in brut.get("verdicts", []):
        try:
            sid = int(v["id"])
        except (KeyError, ValueError, TypeError):
            continue
        if str(v.get("verdict", "")).upper().strip() == "UTILISE":
            utiles.add(sid)
    return utiles


# ── ORCHESTRATION D'UNE LECTURE ──────────────────────────────────────────
def lire(g, question, date_lecture, k=None, model_repondeur=None):
    faits_e, v = entree_vectorielle(g, question, k=k)
    faits_m = marche_graphe(g, faits_e, v)
    # fusion en gardant la provenance de récupération
    chemin = {}
    injectes = []
    for f in faits_e:
        chemin[f.id] = "entrée vectorielle"
        injectes.append(f)
    for f in faits_m:
        if f.id not in chemin:
            chemin[f.id] = "marche de graphe"
            injectes.append(f)

    # accès (Force +, réveil), AVANT le rendu (un dormant réveillé se rend normalement)
    reveils = []
    for f in injectes:
        if g.acceder(f, date_lecture):
            reveils.append(f.id)

    bloc = rendu_epistemique(g, injectes)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    reponse = modele.repondre(prompt, systeme=SYS_REPONSE_V2, temperature=0.0, model=model_repondeur)

    utiles = detecter_usage(question, reponse, injectes)
    for f in injectes:
        if f.id in utiles:
            f.force = min(config.V2_FORCE_PLAFOND, f.force + config.V2_FORCE_GAIN_ACCES)

    return {"reponse": reponse, "injectes": injectes, "chemin": chemin,
            "reveils": reveils, "utiles": utiles, "bloc": bloc}
