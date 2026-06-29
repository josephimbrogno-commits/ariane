# -*- coding: utf-8 -*-
"""
memoire/api.py — l'API publique : les gestes de la bibliothèque.

Registre CONTENU (nourrir la mémoire par le monde) : ecrire / lire / consolider.
Registre STRUCTURE (parcourir la toile, tisser des liens) : parcourir / lier / retoucher.
Inspection : inspecter.

Règle d'or : on LIT la toile librement ; on ne TISSE jamais un fil sans dire d'où il vient.
Le LLM et l'embedding sont INJECTÉS (bibliothèque agnostique du modèle).
"""

import re
from datetime import datetime

from . import config
from .coeur.graphe import GrapheMemoire, parse_date, norm_valeur, _famille
from .coeur.ontologie import PREDICATS, spec_predicat
from .coeur import extraction, lecture, promotion


# ── BRIQUE 3 — APPEL MÉMOIRE : ressources de détection d'une référence DISTANTE à résoudre ────
_TITRES_REF = {"m", "mr", "mme", "mlle", "monsieur", "madame", "mademoiselle", "dr", "pr", "me", "sieur"}
_DESC_PREFIXES = ("le ", "la ", "l'", "les ", "mon ", "ma ", "mes ", "ton ", "ta ", "tes ",
                  "son ", "sa ", "ses ", "notre ", "nos ", "votre ", "vos ", "leur ", "leurs ")
_RELATIONNELS = {"papa", "maman", "pere", "mere", "fils", "fille", "frere", "soeur", "oncle", "tante",
                 "mari", "femme", "epoux", "epouse", "voisin", "voisine", "patron", "patronne", "chef",
                 "cousin", "cousine", "grand-pere", "grand-mere", "beau-pere", "belle-mere"}

SYS_APPEL_MEMOIRE = (
    "Tu résous l'IDENTITÉ d'une référence : QUI est-ce, parmi des entités CONNUES. Tu ne décides JAMAIS "
    "du contenu d'un fait (le « quoi »), seulement l'identité (le « qui »). On te donne une RÉFÉRENCE et "
    "une liste d'ENTITÉS CONNUES avec ce que la mémoire atteste d'elles.\n"
    "La référence désigne-t-elle UNE de ces entités, de façon UNIQUE et CERTAINE ?\n"
    "- Réponds par le NOM EXACT d'une entité de la liste SEULEMENT si c'est sûr et unique.\n"
    "- Si plusieurs entités pourraient convenir → « ambigu ». Si aucune ne correspond → « aucun ».\n"
    "- Ne choisis jamais par défaut ni par simple ressemblance. Dans le doute : « aucun ».\n"
    'Réponds UNIQUEMENT en JSON strict : {"entite":"<nom exact ou null>","statut":"resolu|ambigu|aucun"}'
)


class Memoire:
    def __init__(self, llm, embed):
        """llm : objet avec .texte(prompt, systeme, temperature) et .json(prompt, systeme).
        embed : fonction texte -> vecteur numpy normalisé."""
        self.llm = llm
        self.embed = embed
        self.g = GrapheMemoire(embed)
        self.horloge = None        # date « maintenant » simulée optionnelle (sinon datetime.now())
        self._fenetre = []         # phrases récemment lues (fenêtre glissante pour la coréférence, brique 2)

    def _date(self, date):
        return parse_date(date) or self.horloge or datetime.now()

    def _promouvoir_apres(self, res, quand):
        """HOOK 2C — PROMOTION RÉTROACTIVE, gardé par NOYAU_PROMOTION (défaut OFF → no-op immédiat,
        iso-résultat byte-pour-byte). Après l'insertion d'un fait NEUF, déclenche la re-fouille
        ciblée bornée autour de son entité ; la promotion ne crée AUCUN fait neuf (elle réveille des
        dormants existants) → pas de récursion via ce hook. Une promotion ne casse jamais une écriture."""
        if not promotion.ACTIF or not isinstance(res, dict):
            return res
        sujet, touches = res.get("sujet"), res.get("touches")
        if sujet is None or not touches:
            return res
        try:
            promus = promotion.examiner(self.g, touches[-1], sujet.id, quand)
        except Exception:
            promus = []
        if promus:
            res = dict(res)
            res["promus_retro"] = promus
        return res

    def _hook_consolidation(self):
        try:                       # branché par le paquet d'options (étape 3) ; absent → cœur nu
            from .options import hook_consolidation
            return hook_consolidation
        except Exception:
            return None

    # ── REGISTRE CONTENU ─────────────────────────────────────────────────
    def ecrire(self, enonce, source_id, date=None):
        """Ingère un énoncé : extraction (LLM) → résolution → conflit/corroboration/clôture.
        Retourne un compte rendu auditable des faits touchés."""
        # FENÊTRE DE CORÉFÉRENCE (brique 2) : le contexte = les phrases précédentes (capturé AVANT
        # d'y verser l'énoncé courant). On alimente la fenêtre quel que soit le résultat — une phrase
        # sans fait (« Il faisait froid. ») reste un antécédent valide pour résoudre un pronom suivant.
        contexte = None
        if config.OPT_FENETRE_COREF and self._fenetre:
            contexte = "\n".join(self._fenetre[-config.FENETRE_COREF_MAX_PHRASES:])
        self._fenetre.append(enonce)
        self._fenetre = self._fenetre[-(config.FENETRE_COREF_MAX_PHRASES + 1):]  # borne la mémoire

        # MULTI-TRIPLETS (chantier AJOUTER) : une phrase peut porter PLUSIEURS faits. Chaque fait passe
        # par la MÊME finalisation (planchers, anti-pronom, coréférence) et le MÊME `_ecrire_un`.
        if config.OPT_MULTI_TRIPLETS:
            tris = extraction.extraire_liste(self.llm, enonce, contexte=contexte)
        else:
            t = extraction.extraire(self.llm, enonce, contexte=contexte)
            tris = [t] if t else []
        if not tris:
            return {"erreur": "extraction échouée", "enonce": enonce}
        quand = self._date(date)
        # VITESSE C+B : si activé, mutualiser la brique 3 (appel mémoire) à l'échelle de la PHRASE —
        # résoudre chaque référence distante DISTINCTE une seule fois (C), en parallèle (B) — AVANT les
        # écritures. Les écritures restent séquencées dans l'ordre (déterminisme). OFF = chemin historique.
        if config.OPT_APPEL_MEMOIRE and (config.OPT_GROUPER_MEMOIRE or config.OPT_PARALLELE_PHRASE):
            self._resoudre_refs_phrase(tris)
            rapports = [self._ecrire_un(tri, source_id, quand, deja_resolu=True) for tri in tris]
        else:
            rapports = [self._ecrire_un(tri, source_id, quand) for tri in tris]
        if len(rapports) == 1:
            return rapports[0]
        return {"action": " ; ".join(str(r.get("action") or r.get("erreur") or "") for r in rapports),
                "n_faits": len(rapports), "faits": rapports}

    def ecrire_lot(self, enonces):
        """VITESSE B — ingère une SÉQUENCE en parallélisant l'EXTRACTION (le coût dominant, ~98 % du
        temps mesuré) tout en gardant les ÉCRITURES séquencées DANS L'ORDRE. `enonces` = liste de
        (enonce, source_id, date). Équivaut à N appels `ecrire(...)` consécutifs, en plus rapide.

        Iso-résultat PAR CONSTRUCTION : l'extraction est PURE (LLM + texte + fenêtre de coréférence ; la
        fenêtre est du texte BRUT connu d'avance, indépendante de la toile) → chaque phrase reçoit
        EXACTEMENT le même (énoncé, contexte) qu'en séquentiel → mêmes triplets. Puis brique 3 +
        dérivation + ingestion s'exécutent DANS L'ORDRE, sur la même toile qu'en séquentiel → même
        résultat. Seul le TEMPS MUR change. OFF (séquentiel) reste disponible : appeler `ecrire` en boucle."""
        items = list(enonces)
        n = len(items)
        if n == 0:
            return []

        # 1) CONTEXTES de coréférence, déterministes, calculés d'avance (logique identique à ecrire()).
        contextes, fenetre = [], list(self._fenetre)
        K = config.FENETRE_COREF_MAX_PHRASES
        for enonce, _, _ in items:
            ctx = "\n".join(fenetre[-K:]) if (config.OPT_FENETRE_COREF and fenetre) else None
            contextes.append(ctx)
            fenetre.append(enonce)
            fenetre = fenetre[-(K + 1):]
        self._fenetre = fenetre                          # état final, comme après n appels ecrire()

        # 2) EXTRACTION (coût dominant) — en PARALLÈLE si demandé ; résultats ALIGNÉS sur l'ordre d'entrée.
        def _extraire(i):
            enonce, ctx = items[i][0], contextes[i]
            if config.OPT_MULTI_TRIPLETS:
                return extraction.extraire_liste(self.llm, enonce, contexte=ctx)
            t = extraction.extraire(self.llm, enonce, contexte=ctx)
            return [t] if t else []

        if config.OPT_PARALLELE_PHRASE and n > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(config.PARALLELE_MAX_WORKERS, n)) as ex:
                tris_phrase = list(ex.map(_extraire, range(n)))   # map PRÉSERVE l'ordre
        else:
            tris_phrase = [_extraire(i) for i in range(n)]

        # 3) ÉCRITURES séquencées DANS L'ORDRE — strictement comme la boucle de ecrire() (iso-résultat).
        rapports = []
        for i in range(n):
            enonce, src, d = items[i]
            tris = tris_phrase[i]
            if not tris:
                rapports.append({"erreur": "extraction échouée", "enonce": enonce})
                continue
            quand = self._date(d)
            if config.OPT_APPEL_MEMOIRE and config.OPT_GROUPER_MEMOIRE:
                self._resoudre_refs_phrase(tris)
                rs = [self._ecrire_un(t, src, quand, deja_resolu=True) for t in tris]
            else:
                rs = [self._ecrire_un(t, src, quand) for t in tris]
            rapports.append(rs[0] if len(rs) == 1 else
                            {"action": " ; ".join(str(r.get("action") or r.get("erreur") or "") for r in rs),
                             "n_faits": len(rs), "faits": rs})
        return rapports

    def _resoudre_refs_phrase(self, tris):
        """VITESSE C(+B) — BRIQUE 3 MUTUALISÉE par phrase. Résout chaque référence distante DISTINCTE
        (sujet, et objet si le prédicat porte une entité) UNE seule fois au lieu d'une fois par triplet,
        optionnellement EN PARALLÈLE, puis applique le « QUI » résolu à tous les triplets concernés.
        Lecture SEULE de la toile (aucune écriture ici → résolutions indépendantes, parallélisables) ;
        les écritures se feront ensuite, séquencées, dans l'ordre. Iso-résultat : mêmes (ref,type) →
        même résolution ; seul le NOMBRE d'appels et le TEMPS MUR changent, pas les sorties."""
        jobs = {}                                  # (ref, type) -> nom canonique ou None ; dédoublonné
        for tri in tris:
            jobs[(tri["sujet"], tri.get("type_sujet"))] = None
            if PREDICATS.get(tri["predicat"], {}).get("objet_entite"):
                jobs[(tri["objet"], tri.get("type_objet"))] = None
        cles = list(jobs)

        def _resoudre(cle):
            return cle, self._resoudre_memoire(cle[0], cle[1])

        if config.OPT_PARALLELE_PHRASE and len(cles) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(config.PARALLELE_MAX_WORKERS, len(cles))) as ex:
                for cle, cano in ex.map(_resoudre, cles):
                    jobs[cle] = cano
        else:
            for cle in cles:                       # C seul (sans B) : un seul appel par réf distincte
                jobs[cle] = self._resoudre_memoire(cle[0], cle[1])

        for tri in tris:                           # appliquer le QUI résolu (None = référence inchangée)
            cano = jobs.get((tri["sujet"], tri.get("type_sujet")))
            if cano:
                tri["sujet"] = cano
            if PREDICATS.get(tri["predicat"], {}).get("objet_entite"):
                cano_o = jobs.get((tri["objet"], tri.get("type_objet")))
                if cano_o:
                    tri["objet"] = cano_o

    def _ecrire_un(self, tri, source_id, quand, deja_resolu=False):
        """Ingère UN fait extrait : brique 3 (appel mémoire, qui-pas-quoi) → dérivation → exécution.
        `deja_resolu` : la brique 3 a déjà été faite en lot par `_resoudre_refs_phrase` (vitesse C+B)."""
        # BRIQUE 3 — APPEL MÉMOIRE : rattacher une référence DISTANTE à une entité CONNUE, AVANT d'écrire.
        # La mémoire répond QUI ; le QUOI reste celui du TEXTE (le texte prime). Match unique seulement.
        if config.OPT_APPEL_MEMOIRE and not deja_resolu:
            cano = self._resoudre_memoire(tri["sujet"], tri.get("type_sujet"))
            if cano:
                tri["sujet"] = cano
            if PREDICATS.get(tri["predicat"], {}).get("objet_entite"):
                cano_o = self._resoudre_memoire(tri["objet"], tri.get("type_objet"))
                if cano_o:
                    tri["objet"] = cano_o

        intention = extraction.deriver(tri)        # DÉRIVATION DÉTERMINISTE (V2)
        act = intention["action"]
        if act == "RIEN":
            return {"action": "RIEN — " + intention.get("raison", "doute"),
                    "relation": f'{tri["predicat"]}({tri["sujet"]})={tri["objet"]}'}
        if act == "CLOTURE_NIEE":
            return self._clore_par_extraction(tri, source_id, quand)
        if act == "FAIT_CLOS":
            return self._fait_clos(tri, source_id, quand, intention.get("debut"), intention.get("fin"))
        return self._promouvoir_apres(
            self.g.ingerer(tri["sujet"], tri["predicat"], tri["objet"], source_id=source_id,
                           date_obs=quand, date_validite=intention.get("debut"),
                           type_sujet=tri.get("type_sujet"), type_objet=tri.get("type_objet")),
            quand)

    def _resoudre_memoire(self, ref, type_ref):
        """BRIQUE 3 — APPEL MÉMOIRE. Rattacher une référence DISTANTE à une entité CONNUE de la toile.
        Renvoie le nom canonique sur match UNIQUE et confiant, sinon None (→ nœud distinct / abstention).
        QUI, jamais QUOI : ne touche que l'identité de la référence, pas le contenu du fait. Conservateur :
        dans le doute, on ne devine pas (un mauvais rattachement = collision déguisée + risque de boucle)."""
        if not ref:
            return None
        g = self.g
        fam = _famille(type_ref)
        cands = [e for e in g.entites.values()
                 if (fam is None or _famille(e.type) == fam) and norm_valeur(e.nom) != norm_valeur(ref)]
        if not cands:
            return None
        rn = extraction._norm(ref).strip()
        toks = rn.split()

        # 1) NOM / SURNOM via TITRE (structurel, sûr) : « M. Vasseur » → l'unique « … Vasseur » connu.
        #    Le titre (M./Mme/…) signale une personne désignée par son patronyme : le surnom (tokens ≥3
        #    après le titre) doit être inclus dans le nom d'UN SEUL candidat. 0 ou plusieurs → on n'ose pas.
        if toks and toks[0].strip(".") in _TITRES_REF:
            surnom = [t for t in toks[1:] if len(t) >= 3]
            if surnom:
                hits = [e for e in cands if set(surnom) <= set(extraction._norm(e.nom).split())]
                return hits[0].nom if len(hits) == 1 else None
            return None

        # 2) DESCRIPTION / RELATIONNEL via LLM (conservateur) : « le commandant », « papa ». Déclenché
        #    SEULEMENT si la référence en a la forme (article défini / mot de parenté) — sinon un nom
        #    propre neuf (« Bertrand Sorel ») ne déclenche RIEN (inerte, pas de coût LLM).
        head = toks[0] if toks else ""
        if not (rn.startswith(_DESC_PREFIXES) or head in _RELATIONNELS):
            return None
        cc = sorted(cands, key=lambda e: -sum(1 for f in g.faits.values()
                                              if f.sujet_id == e.id or f.objet_id == e.id))
        cc = cc[:config.APPEL_MEMOIRE_MAX_CANDIDATS]
        lignes = []
        for i, e in enumerate(cc, 1):
            att = [f"{f.predicat}={g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet}"
                   for f in g.faits.values() if f.sujet_id == e.id][:3]
            lignes.append(f"{i}. {e.nom} — {', '.join(att) if att else 'peu attesté'}")
        d = self.llm.json(f"RÉFÉRENCE : « {ref} »\n\nENTITÉS CONNUES :\n" + "\n".join(lignes) +
                          "\n\nÀ qui renvoie la référence, de façon unique et certaine ?",
                          systeme=SYS_APPEL_MEMOIRE)
        if not isinstance(d, dict) or extraction._norm(d.get("statut", "")).strip() != "resolu":
            return None
        ent = str(d.get("entite") or "").strip()
        return ent if ent in {e.nom for e in cc} else None     # anti-hallucination : un nom de la liste

    def _fait_clos(self, tri, source_id, date, debut, fin):
        """Intervalle fermé / fin déclarée (« de X à Y », « jusqu'en Y ») → fait DÉCLARÉ CLOS
        (« était… de [début] à [fin] »). Sûr : un clos n'est jamais servi au présent. Distinct de
        l'orphelin de polarité (« éliminé ») : ici l'intervalle est EXPLICITEMENT énoncé."""
        g = self.g
        d_obs = parse_date(debut) or date
        res = g.ingerer(tri["sujet"], tri["predicat"], tri["objet"], source_id=source_id,
                        date_obs=d_obs, date_validite=debut,
                        type_sujet=tri.get("type_sujet"), type_objet=tri.get("type_objet"))
        if not res.get("touches"):          # ingestion rejetée (ex. fait auto-référentiel) → rien à clore
            return res
        f = res["touches"][-1]
        g.clore_fait(f, source_id, parse_date(fin) or date)
        return {"action": "FAIT CLOS (intervalle/fin déclaré) — « était… jusqu'à »",
                "faits": [g.fait_court(f)]}

    def _clore_par_extraction(self, tri, source_id, date):
        """Polarité de fin → CLÔTURE du fait existant (« était… jusqu'à »), JAMAIS un fait positif.
        Si aucun fait courant ne correspond, comportement SÛR : créer un fait DÉJÀ CLOS, mono-source
        (donc incertain) — il préserve « était membre… » sans jamais affirmer une appartenance
        ACTUELLE. Un clos n'est jamais servi au présent : il ne peut pas être « confidently wrong »."""
        g = self.g
        sujet, predicat, objet = tri["sujet"], tri["predicat"], tri["objet"]
        e = g.trouver_entite(sujet)
        courants = ([f for f in g.faits_de(e.id, predicat) if f.statut in ("courant", "disputé")]
                    if e else [])

        def objet_de(f):
            return g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet

        cible = next((f for f in courants
                      if norm_valeur(objet_de(f)) == norm_valeur(objet)), None)
        if cible is None and spec_predicat(predicat)["fonctionnel"] and len(courants) == 1:
            cible = courants[0]              # fonctionnel : une seule valeur courante → on la clôt

        if cible is not None:
            g.clore_fait(cible, source_id, date)
            return {"action": f"CLÔTURE (polarité de fin) — #{cible.id} devient « était… jusqu'à »",
                    "polarite": "fin", "faits": [g.fait_court(cible)]}

        # Orphelin : on apprend une FIN sans avoir connu le fait. On ne crée RIEN — car créer un
        # « était… » serait affirmer un PASSÉ non vérifié. Contre-exemple décisif : « l'Italie est
        # éliminée » ne veut PAS dire qu'elle « était qualifiée » (elle ne l'a jamais été). Règle
        # d'or : mieux vaut rater proprement qu'affirmer le faux. → rien produit.
        return {"action": "POLARITÉ DE FIN — aucun fait courant à clore ; rien produit (sûr)",
                "polarite": "fin", "relation": f"{predicat}({sujet})={objet}"}

    def ecrire_triplet(self, sujet, predicat, objet, source_id, date=None, validite=None,
                       type_sujet=None, type_objet=None):
        """Ingère un triplet déjà structuré (sans LLM). Utile aux tests et au geste `lier`.
        type_sujet/type_objet optionnels (le socle type) : passés tels quels au nœud si fournis."""
        quand = self._date(date)
        return self._promouvoir_apres(
            self.g.ingerer(sujet, predicat, objet, source_id=source_id,
                           date_obs=quand, date_validite=validite,
                           type_sujet=type_sujet, type_objet=type_objet),
            quand)

    def lire(self, question, date=None):
        """Entrée vectorielle (+ reconnaissance par nœud nommé) + marche de graphe ; rendu verbal."""
        return lecture.lire(self.g, self.llm, question, self._date(date))

    def consolider(self, date=None):
        """Le « sommeil » : érosions, dormance, fusion, promotion noyau (+ options branchées)."""
        return self.g.consolider(self._date(date), avant_dormance=self._hook_consolidation())

    # ── REGISTRE STRUCTURE ───────────────────────────────────────────────
    # Règle d'or : `parcourir` LIT la toile librement (aucune croyance engagée) ;
    # `lier` et `retoucher` TISSENT, donc passent TOUJOURS par un fait sourcé via le pipeline
    # normal (plafond du menteur, conflit, statut). Pas de porte dérobée.

    def parcourir(self, entite, profondeur=1):
        """LECTURE LIBRE de la toile : voisinage, degrés, statuts des liens. N'engage AUCUNE
        croyance, ne crée aucun fait. C'est la moitié « on lit librement » de la règle d'or."""
        e = self.g.trouver_entite(entite)
        if not e:
            return None

        def liens_de(eid):
            out = []
            for f in self.g.faits.values():
                if f.sujet_id == eid:
                    autre = self.g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet
                    out.append({"fait_id": f.id, "sens": "→", "predicat": f.predicat,
                                "vers": autre, "vers_id": f.objet_id, "statut": f.statut})
                elif f.objet_id == eid:
                    out.append({"fait_id": f.id, "sens": "←", "predicat": f.predicat,
                                "vers": self.g.nom_entite(f.sujet_id), "vers_id": f.sujet_id,
                                "statut": f.statut})
            return out

        liens = liens_de(e.id)
        voisins_ids = {l["vers_id"] for l in liens if l["vers_id"] is not None}
        res = {"entite": e.nom, "type": e.type, "importance": round(e.importance, 3),
               "degre": len(voisins_ids), "liens": liens}
        if profondeur >= 2:
            res["voisinage"] = {self.g.nom_entite(vid): liens_de(vid) for vid in voisins_ids}
        return res

    def lier(self, entite_a, relation, entite_b, source_id=None, date=None, validite=None):
        """TISSE un lien — mais jamais sans source. En dessous, fabrique un fait sourcé qui passe
        par le pipeline normal : il est donc soumis au plafond du menteur (0.60 mono-source), au
        conflit et au statut. `lier` N'EST PAS une porte dérobée vers une vérité non auditable."""
        if not source_id:
            raise ValueError("Règle d'or : on ne tisse jamais un fil sans dire d'où il vient "
                             "(source_id requis).")
        if relation not in PREDICATS:
            raise ValueError(f"relation inconnue : {relation!r}")
        return self.g.ingerer(entite_a, relation, entite_b, source_id=source_id,
                              date_obs=self._date(date), date_validite=validite)

    def retoucher(self, fait_id, action, source_id=None, date=None):
        """Retouche SOURCÉE d'un fait existant. action ∈ {clore, contester, corroborer}.
        Toute retouche est une affirmation sur le monde : elle exige une source."""
        if not source_id:
            raise ValueError("Règle d'or : retoucher exige une source "
                             "(toute affirmation sur le monde est sourcée).")
        f = self.g.faits.get(fait_id)
        if not f:
            raise ValueError(f"fait inconnu : {fait_id}")

        if action == "clore":
            # Clôturer, c'est affirmer « ce fait a cessé d'être vrai à telle date ».
            # Sourcé ET daté, comme toute affirmation. Le fait devient « était… jusqu'à [date] ».
            d = parse_date(date)
            if d is None:
                raise ValueError("Clôturer est une affirmation datée : une date de fin "
                                 "(date=…) est requise.")
            self.g.clore_fait(f, source_id, d)
            return {"action": "clôture", "fait": f.id, "statut": f.statut,
                    "valide_jusqua": f.valide_jusqua, "source": source_id}

        if action == "contester":
            self.g.contester_fait(f, source_id, self._date(date))
            return {"action": "contestation", "fait": f.id, "statut": f.statut,
                    "certitude": round(f.certitude, 3), "source": source_id}

        if action == "corroborer":
            # Une corroboration n'est qu'un nouveau rapport de la même valeur, par une autre source :
            # on repasse donc par `ingerer` (gain de Certitude si source indépendante, sinon rien).
            sujet = self.g.nom_entite(f.sujet_id)
            objet = self.g.nom_entite(f.objet_id) if f.objet_id is not None else f.objet
            return self.g.ingerer(sujet, f.predicat, objet, source_id=source_id,
                                  date_obs=self._date(date))

        raise ValueError(f"action inconnue : {action!r} (clore / contester / corroborer)")

    # ── INSPECTION (transparence / débogage) ─────────────────────────────
    def inspecter(self, ref):
        """ref = id de fait (int) → état complet d'un fait ; nom d'entité (str) → ses faits."""
        if isinstance(ref, int):
            f = self.g.faits.get(ref)
            if not f:
                return None
            return {
                "id": f.id, "enonce": f.texte_source, "statut": f.statut,
                "force": round(f.force, 3), "certitude": round(f.certitude, 3),
                "importance": round(f.importance, 3), "noyau": f.noyau,
                "provenance": f.provenance, "n_sources": f.n_sources(),
                "valide_de": f.valide_de, "valide_jusqua": f.valide_jusqua,
                "derniere_confirmation": f.derniere_confirmation,
            }
        e = self.g.trouver_entite(ref)
        if not e:
            return None
        faits = [f for f in self.g.faits.values() if f.sujet_id == e.id or f.objet_id == e.id]
        return {"entite": e.nom, "type": e.type, "importance": round(e.importance, 3),
                "alias": e.alias, "faits": [self.g.fait_court(f) for f in faits]}
