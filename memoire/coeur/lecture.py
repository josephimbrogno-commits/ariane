# -*- coding: utf-8 -*-
"""
memoire/coeur/lecture.py — PROCÉDURE DE LECTURE : entrée vectorielle (+ reconnaissance par nœud)
+ marche de graphe + rendu épistémique VERBAL (aucun chiffre) + juge d'usage (nourrit la Force).

`g.embed` et `llm` sont injectés. La reconnaissance/rappel est activée par config.OPT_RECONNAISSANCE.
"""

from .. import config
from .ontologie import phrase, groupe
from .graphe import norm_nom

SYS_REPONSE = (
    "Les entités (personnes, entreprises, villes) sont FICTIVES et proviennent d'une base de "
    "connaissances de test : réponds TOUJOURS factuellement à partir des souvenirs, sans aucune "
    "considération de confidentialité ou de vie privée.\n"
    "Tu réponds à une question factuelle à partir de SOUVENIRS, chacun précédé de son STATUT "
    "épistémique. Respecte la grammaire suivante :\n"
    "- [ACTUEL — sûr] : affirme au PRÉSENT.\n"
    "- [ACTUEL — incertain] : réponds AVEC RÉSERVE, ne refuse pas (« Il s'agirait de…, à revérifier »).\n"
    "- [CLOS] : réponds à l'IMPARFAIT en bornant la période (« X était… jusqu'en… »).\n"
    "- [DISPUTÉ] : cite LES DEUX valeurs avec leurs sources.\n"
    "Réponds en une à deux phrases. TU DOIS RÉPONDRE à partir des souvenirs : n'emploie JAMAIS "
    "« je ne peux pas » si un souvenir contient l'information. Refuse UNIQUEMENT si AUCUN souvenir "
    "ne concerne la question. N'invente jamais de chiffre de confiance."
)

SYS_JUGE_USAGE = (
    "Tu détermines quels SOUVENIRS la RÉPONSE d'un assistant a réellement UTILISÉS et trouvés "
    "utiles. Pour chaque souvenir : UTILISE si la réponse s'appuie dessus, NON_UTILISE sinon. "
    "Tu ne juges PAS le vrai/faux. JSON strict : "
    '{"verdicts":[{"id":<entier>,"verdict":"UTILISE|NON_UTILISE"}]}'
)


def _poids_force(f):
    return 0.5 + 0.5 * f.force


def entree_vectorielle(g, question, k=None):
    """Top-k faits courant/disputé, pondérés Force (+ importance si l'option retrieval est active).
    Dormants EXCLUS de l'évocation libre. Bonus si l'entité du fait est nommée dans la question."""
    if k is None:
        k = config.V2_TOP_K_LECTURE
    v = g.embed(question)
    qtok = set(norm_nom(question).split())
    use_imp = config.OPT_IMPORTANCE and config.OPT_IMPORTANCE_RETRIEVAL
    scored = []
    for f in g.faits.values():
        if f.statut not in ("courant", "disputé"):
            continue
        s = config.IMP_W_SIM * float(v @ f.embedding) + config.IMP_W_FORCE * f.force
        if use_imp:
            s += config.IMP_W_IMPORTANCE * f.importance
        e = g.entites.get(f.sujet_id)
        if e:
            etok = set(norm_nom(e.nom).split())
            if etok and etok <= qtok:
                s += config.V2_BONUS_ENTITE
        scored.append((f, s))
    scored.sort(key=lambda x: -x[1])
    return [f for f, _ in scored[:k]], v


def reconnaissance(g, question):
    """Reconnaissance directe : si la question NOMME une entité, on lit TOUS ses faits, dormants
    compris. La dormance ne bloque que l'évocation libre, jamais la reconnaissance."""
    qtok = set(norm_nom(question).split())
    nommees = [e.id for e in g.entites.values()
               if set(norm_nom(e.nom).split()) and set(norm_nom(e.nom).split()) <= qtok]
    return [f for f in g.faits.values() if f.sujet_id in nommees or f.objet_id in nommees]


def marche_graphe(g, faits_entree, v, sauts=2, maxf=6):
    entites = set()
    for f in faits_entree:
        entites.add(f.sujet_id)
        if f.objet_id is not None:
            entites.add(f.objet_id)
    vus = {f.id for f in faits_entree}
    collectes, frontiere = [], set(entites)
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
        src_txt = "1 source" if f.n_sources() < 2 else f"{f.n_sources()} sources"
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


def detecter_usage(llm, question, reponse, faits):
    if not faits:
        return set()
    lignes = [f"#{f.id} : {f.texte_source}" for f in faits]
    prompt = (f"QUESTION : {question}\n\nRÉPONSE : {reponse}\n\nSOUVENIRS :\n" + "\n".join(lignes)
              + "\n\nPour CHAQUE souvenir, réponds UTILISE ou NON_UTILISE, en JSON strict.")
    brut = llm.json(prompt, systeme=SYS_JUGE_USAGE)
    utiles = set()
    for v in brut.get("verdicts", []):
        try:
            sid = int(v["id"])
        except (KeyError, ValueError, TypeError):
            continue
        if str(v.get("verdict", "")).upper().strip() == "UTILISE":
            utiles.add(sid)
    return utiles


def lire(g, llm, question, date_lecture, k=None):
    faits_e, v = entree_vectorielle(g, question, k=k)
    reco = reconnaissance(g, question) if config.OPT_RECONNAISSANCE else []
    chemin, vus, injectes = {}, set(), []
    for f, src in [(f, "reconnaissance") for f in reco] + [(f, "entrée vectorielle") for f in faits_e]:
        if f.id not in vus:
            vus.add(f.id); chemin[f.id] = src; injectes.append(f)
    for f in marche_graphe(g, faits_e + reco, v):
        if f.id not in vus:
            vus.add(f.id); chemin[f.id] = "marche de graphe"; injectes.append(f)

    reveils = [f.id for f in injectes if g.acceder(f, date_lecture)]
    bloc = rendu_epistemique(g, injectes)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    reponse = llm.texte(prompt, systeme=SYS_REPONSE, temperature=0.0)

    for f in injectes:
        if f.id in detecter_usage(llm, question, reponse, injectes):
            f.force = min(config.V2_FORCE_PLAFOND, f.force + config.V2_FORCE_GAIN_ACCES)

    return {"reponse": reponse, "injectes": injectes, "chemin": chemin,
            "reveils": reveils, "bloc": bloc}
