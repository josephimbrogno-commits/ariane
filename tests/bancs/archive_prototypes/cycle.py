# -*- coding: utf-8 -*-
"""
cycle.py — l'orchestration d'UNE question.

Réutilisé par l'étape 1 (micro-démo) et l'étape 2 (expérience complète).
Définit aussi les prompts des trois configurations comparées :

  • Config A — modèle seul      : aucune mémoire.
  • Config B — RAG classique    : souvenirs injectés SANS date ni confiance,
                                  aucune mise à jour (entrepôt inerte).
  • Config C — mémoire qui trie : souvenirs datés + confiance, juge + mises à jour.
"""

import config
import modele

VERDICTS_VALIDES = {"CONFIRME", "CONTREDIT", "NON_UTILISE", "INCERTAIN"}

# ── Prompts système ──────────────────────────────────────────────────────
SYS_REPONSE_C = (
    "Tu réponds à des questions factuelles en t'appuyant sur des SOUVENIRS fournis. "
    "Chaque souvenir indique sa confiance (0 à 1) et sa date de mise à jour. "
    "En cas de CONFLIT entre souvenirs sur un même fait, privilégie la confiance la "
    "plus haute ET la date la plus récente. Réponds de façon brève et précise (une "
    "phrase). Si l'information n'est pas dans les souvenirs, dis-le clairement."
)

SYS_REPONSE_C_VERBAL = (
    "Tu réponds à des questions factuelles en t'appuyant sur des SOUVENIRS fournis, chacun avec "
    "sa date de mise à jour. Certains portent la mention « à confirmer » (confirmation ancienne) : "
    "tu peux quand même t'en servir pour répondre, en restant prudent. En cas de CONFLIT entre "
    "souvenirs sur un même fait, privilégie la date la plus RÉCENTE. Réponds de façon brève et "
    "précise (une phrase). Ne refuse de répondre QUE si l'information est réellement ABSENTE des "
    "souvenirs (sinon, donne ta meilleure réponse même si un souvenir est « à confirmer »)."
)

SYS_REPONSE_B = (
    "Tu réponds à des questions factuelles en t'appuyant sur les informations fournies. "
    "Réponds de façon brève et précise (une phrase). Si l'information n'est pas fournie, "
    "dis-le clairement."
)

SYS_REPONSE_A = (
    "Tu réponds à des questions factuelles à partir de tes connaissances. "
    "Réponds de façon brève et précise (une phrase). Si tu ne sais pas, dis-le."
)

# ── Juge DÉCOUPLÉ : deux versions, pour l'ablation (V1 original vs V2 durci) ──
_JUGE_INTRO = (
    "Tu es un VÉRIFICATEUR de faits rigoureux et impartial. On te donne une question, "
    "une liste de SOUVENIRS numérotés (chacun avec sa date de mise à jour), et la réponse "
    "qu'un assistant a produite. Tu attribues à CHAQUE souvenir exactement UN verdict, en "
    "suivant cette procédure DANS L'ORDRE :\n\n"
)

# ÉTAPE 1, version ORIGINALE (V1)
_JUGE_ETAPE1_V1 = (
    "ÉTAPE 1 — CONTRADICTION (priorité absolue, décidée UNIQUEMENT par les faits entre souvenirs).\n"
    "Deux souvenirs se contredisent quand ils affirment des valeurs INCOMPATIBLES sur le MÊME "
    "attribut de la MÊME entité (ex. deux dirigeants différents pour la même entreprise, deux "
    "prix différents pour le même produit, deux horaires différents pour le même lieu). Dans ce "
    "cas, le souvenir le plus ANCIEN (le fait dépassé) reçoit CONTREDIT ; le plus RÉCENT ne reçoit "
    "PAS CONTREDIT. Pour savoir lequel est le plus récent, utilise sa date de mise à jour et les "
    "indices temporels du texte (« depuis 2026 », « depuis mars 2026 », « nouveau »…).\n"
    "INTERDICTIONS STRICTES :\n"
    "  • NE JAMAIS décider une contradiction à partir de la réponse de l'assistant.\n"
    "  • NE JAMAIS te baser sur un niveau de confiance (il ne t'est d'ailleurs pas fourni).\n"
    "  • Un souvenir SEUL, sans autre souvenir qui le contredise factuellement, ne peut PAS être "
    "CONTREDIT, même s'il a l'air faux ou hors-sujet.\n\n"
)

# ÉTAPE 1, version DURCIE (V2) : récence par date, réponse faillible, et surtout ANCIEN ≠ PÉRIMÉ
_JUGE_ETAPE1_V2 = (
    "ÉTAPE 1 — CONTRADICTION (priorité absolue, décidée UNIQUEMENT par les faits entre souvenirs).\n"
    "Deux souvenirs se contredisent quand ils affirment des valeurs INCOMPATIBLES sur le MÊME "
    "attribut de la MÊME entité (ex. deux dirigeants différents pour la même entreprise, deux "
    "prix différents pour le même produit, deux horaires différents pour le même lieu). Dans ce "
    "cas, le souvenir dont la DATE de mise à jour est la plus RÉCENTE l'emporte : le souvenir le "
    "plus ANCIEN (le fait dépassé) reçoit CONTREDIT, le plus récent ne reçoit PAS CONTREDIT. "
    "Compare d'abord les dates de mise à jour ; en cas d'égalité, sers-toi des indices du texte "
    "(« depuis 2026 », « depuis mars 2026 », « nouveau »…).\n"
    "ATTENTION — ANCIEN n'est PAS PÉRIMÉ : un fait ancien (ex. une date de fondation, un fait "
    "historique) qui n'est contredit par AUCUN souvenir plus récent portant sur le MÊME attribut "
    "reste VALIDE. Ne le contredis pas à cause de sa seule ancienneté. La règle « le récent gagne » "
    "ne s'applique qu'ENTRE deux souvenirs qui parlent du MÊME attribut de la MÊME entité.\n"
    "INTERDICTIONS STRICTES :\n"
    "  • La réponse de l'assistant peut être FAUSSE ou être un refus. NE JAMAIS contredire un "
    "souvenir au motif qu'il diffère de la réponse. Un souvenir ne peut être contredit QUE par un "
    "AUTRE souvenir plus récent portant sur le même fait.\n"
    "  • NE JAMAIS te baser sur un niveau de confiance (il ne t'est d'ailleurs pas fourni).\n"
    "  • Un souvenir SEUL, sans autre souvenir plus récent qui le contredise factuellement, ne "
    "peut PAS être CONTREDIT, même s'il a l'air faux ou hors-sujet.\n"
    "EXEMPLE : « #5 (màj 2024-01-01) : le produit coûte 120€ » et « #6 (màj 2026-01-01) : depuis "
    "2026 le produit coûte 95€ ». Même si la réponse dit « je ne sais pas » ou « 120€ », le verdict "
    "correct est #5 → CONTREDIT (plus ancien) et #6 → PAS contredit (plus récent).\n\n"
)

_JUGE_TAIL = (
    "ÉTAPE 2 — CONFIRMATION (seulement pour les souvenirs NON contredits à l'étape 1).\n"
    "Un souvenir reçoit CONFIRME UNIQUEMENT si la réponse de l'assistant s'est APPUYÉE dessus et "
    "qu'il a été UTILE pour répondre (le souvenir a réellement servi). Si la réponse est un refus "
    "ou n'utilise pas ce souvenir, il ne peut PAS être CONFIRME.\n\n"
    "ÉTAPE 3 — sinon :\n"
    "  • NON_UTILISE : le souvenir n'a pas servi à répondre (hors-sujet, ou non utilisé), même s'il "
    "est vrai et récent.\n"
    "  • INCERTAIN : seulement si tu ne peux honnêtement pas trancher.\n\n"
    "Réponds UNIQUEMENT en JSON strict : "
    '{"verdicts":[{"id":<entier>,"verdict":"<CONFIRME|CONTREDIT|NON_UTILISE|INCERTAIN>",'
    '"justification":"<courte phrase factuelle>"}]}'
)

SYS_JUGE_DECOUPLE_V1 = _JUGE_INTRO + _JUGE_ETAPE1_V1 + _JUGE_TAIL
SYS_JUGE_DECOUPLE_V2 = _JUGE_INTRO + _JUGE_ETAPE1_V2 + _JUGE_TAIL
SYS_JUGE_DECOUPLE = SYS_JUGE_DECOUPLE_V1  # alias : version retenue (la simple bat la durcie)


# ── JUGE SCINDÉ : deux détecteurs ÉTANCHES + règle « le conflit bat l'usage » ──
# Détecteur de CONFLITS : ne voit QUE les souvenirs (ni question ni réponse) → il ne
# peut donc PAS hériter d'une réponse fausse. C'est lui SEUL qui produit les CONTREDIT.
SYS_JUGE_CONFLITS = (
    "Tu es un DÉTECTEUR de contradictions factuelles ENTRE SOUVENIRS. On te donne UNIQUEMENT "
    "une liste de souvenirs numérotés, chacun avec sa date de mise à jour. Rien d'autre.\n"
    "Deux souvenirs se CONTREDISENT quand ils affirment des valeurs INCOMPATIBLES sur le MÊME "
    "attribut de la MÊME entité (le même dirigeant, le même prix, le même horaire, le même lieu "
    "d'une même chose). Dans une telle paire, le souvenir dont la DATE est la plus ANCIENNE est "
    "le fait DÉPASSÉ → CONTREDIT ; le plus récent → RAS.\n"
    "Un souvenir qu'AUCUN autre souvenir plus récent ne contredit sur le MÊME attribut n'est PAS "
    "contredit, MÊME s'il est très ancien (ex. une date de fondation, un fait historique). "
    "L'ancienneté seule ne contredit jamais.\n"
    "Pour CHAQUE souvenir, réponds CONTREDIT ou RAS. JSON strict : "
    '{"verdicts":[{"id":<entier>,"verdict":"CONTREDIT|RAS","justification":"<courte phrase>"}]}'
)

# Détecteur d'USAGE : voit la question + la réponse → dit seulement si le souvenir a SERVI.
# Il ne juge JAMAIS le vrai/faux. C'est lui SEUL qui produit les CONFIRME (via l'usage).
SYS_JUGE_USAGE = (
    "Tu détermines quels SOUVENIRS la RÉPONSE d'un assistant a réellement UTILISÉS et trouvés "
    "utiles pour répondre. On te donne la question, la réponse, et des souvenirs numérotés.\n"
    "Pour chaque souvenir : UTILISE si la réponse s'appuie dessus ou en reprend l'information ; "
    "NON_UTILISE sinon. Si la réponse est un refus (« je ne sais pas ») ou n'utilise pas le "
    "souvenir, c'est NON_UTILISE. Tu ne juges PAS si le souvenir est vrai ou faux, seulement s'il "
    "a SERVI. JSON strict : "
    '{"verdicts":[{"id":<entier>,"verdict":"UTILISE|NON_UTILISE","justification":"<courte phrase>"}]}'
)


def _normaliser(brut, autorises, defaut):
    """Transforme la sortie JSON du juge en {id: {verdict, justification}}."""
    res = {}
    for v in brut.get("verdicts", []):
        try:
            sid = int(v["id"])
        except (KeyError, ValueError, TypeError):
            continue
        verdict = str(v.get("verdict", "")).upper().strip()
        if verdict not in autorises:
            verdict = defaut
        res[sid] = {"verdict": verdict, "justification": str(v.get("justification", "")).strip()}
    return res


def detecter_conflits(trouves, model=None, think=None):
    """Détecteur de CONFLITS : NE voit QUE les souvenirs. Renvoie {id: CONTREDIT|RAS}."""
    if not trouves:
        return {}
    lignes = [
        f"#{s.id} (màj {s.date_derniere_confirmation.strftime('%Y-%m-%d')}) : {s.contenu}"
        for s, _ in trouves
    ]
    prompt = ("SOUVENIRS :\n" + "\n".join(lignes)
              + "\n\nPour CHAQUE souvenir, réponds CONTREDIT ou RAS, en JSON strict.")
    brut = modele.juger(prompt, systeme=SYS_JUGE_CONFLITS, model=model, think=think)
    return _normaliser(brut, {"CONTREDIT", "RAS"}, "RAS")


def detecter_usage(question, reponse, trouves, model=None, think=None):
    """Détecteur d'USAGE : voit question + réponse. Renvoie {id: UTILISE|NON_UTILISE}."""
    if not trouves:
        return {}
    lignes = [f"#{s.id} : {s.contenu}" for s, _ in trouves]
    prompt = (f"QUESTION : {question}\n\nRÉPONSE : {reponse}\n\nSOUVENIRS :\n"
              + "\n".join(lignes)
              + "\n\nPour CHAQUE souvenir, réponds UTILISE ou NON_UTILISE, en JSON strict.")
    brut = modele.juger(prompt, systeme=SYS_JUGE_USAGE, model=model, think=think)
    return _normaliser(brut, {"UTILISE", "NON_UTILISE"}, "NON_UTILISE")


def juger_champion(question, reponse, trouves):
    """
    Le JUGE retenu après l'étape 1 (config championne) :
    qwen3:30b-a3b + prompt découplé SIMPLE (V1) + confiance MASQUÉE (anti-boucle).
    Renvoie {id: {verdict, justification}}.
    """
    return juger(
        question, reponse, trouves,
        model=config.MODELE_JUGE, think=config.JUGE_THINK,
        systeme=SYS_JUGE_DECOUPLE_V1, montrer_confiance=False,
    )


def juger_scinde(question, reponse, trouves, model=None, think=None):
    """
    Juge en DEUX appels étanches, combinés par la règle « LE CONFLIT BAT L'USAGE » :
      - CONTREDIT  si le détecteur de conflits le marque CONTREDIT (le monde tranche) ;
      - sinon CONFIRME si le détecteur d'usage le marque UTILISE (l'opinion confirme) ;
      - sinon NON_UTILISE.
    Renvoie {id: {verdict, conflit, usage, justification}} (détail inclus pour la transparence).
    """
    conflits = detecter_conflits(trouves, model=model, think=think)
    usages = detecter_usage(question, reponse, trouves, model=model, think=think)
    res = {}
    for s, _ in trouves:
        c = conflits.get(s.id, {}).get("verdict", "RAS")
        u = usages.get(s.id, {}).get("verdict", "NON_UTILISE")
        if c == "CONTREDIT":
            verdict = "CONTREDIT"
            just = conflits.get(s.id, {}).get("justification", "contredit par un souvenir plus récent")
        elif u == "UTILISE":
            verdict = "CONFIRME"
            just = usages.get(s.id, {}).get("justification", "utilisé et utile pour la réponse")
        else:
            verdict = "NON_UTILISE"
            just = "ni contredit ni utilisé"
        res[s.id] = {"verdict": verdict, "conflit": c, "usage": u, "justification": just}
    return res

SYS_JUGE = (
    "Tu es un VÉRIFICATEUR de faits rigoureux et impartial. On te donne une question, "
    "la réponse qui a été fournie, et une liste de SOUVENIRS numérotés (chacun avec sa "
    "date et sa confiance). Pour CHAQUE souvenir, rends exactement un verdict :\n"
    "- CONFIRME   : le souvenir est juste et cohérent avec la meilleure information disponible.\n"
    "- CONTREDIT  : le souvenir est faux ou PÉRIMÉ ; il entre en conflit avec un souvenir "
    "plus récent / plus fiable, ou avec la réalité.\n"
    "- NON_UTILISE: le souvenir est hors-sujet, il n'a pas servi à répondre.\n"
    "- INCERTAIN  : impossible de trancher.\n"
    "RÈGLE DE CONFLIT : si deux souvenirs se contredisent sur le MÊME fait, le plus RÉCENT "
    "(date) et le plus CONFIANT est CONFIRME, l'autre est CONTREDIT. On ne pénalise pas les "
    "deux. Réponds UNIQUEMENT en JSON strict de la forme : "
    '{"verdicts":[{"id":<entier>,"verdict":"<CONFIRME|CONTREDIT|NON_UTILISE|INCERTAIN>",'
    '"justification":"<courte phrase>"}]}'
)


# ── RÉPONSE selon la configuration ───────────────────────────────────────
def repondre_A(question):
    """Config A : le modèle seul, sans mémoire."""
    return modele.repondre(question, systeme=SYS_REPONSE_A)


def repondre_B(memoire, question):
    """Config B : RAG inerte (injection sans date/confiance, aucune mise à jour)."""
    trouves = memoire.rechercher(question)
    bloc = memoire.texte_injection(trouves, avec_meta=False)
    prompt = f"Informations :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    reponse = modele.repondre(prompt, systeme=SYS_REPONSE_B)
    return reponse, trouves


def repondre_C(memoire, question):
    """Config C : injection AVEC date + confiance (chiffrée)."""
    trouves = memoire.rechercher(question)
    bloc = memoire.texte_injection(trouves, avec_meta=True)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    reponse = modele.repondre(prompt, systeme=SYS_REPONSE_C)
    return reponse, trouves


def repondre_C_verbal(memoire, question):
    """Config C, variante : confiance rendue VERBALEMENT (date + « à confirmer » si basse)."""
    trouves = memoire.rechercher(question)
    bloc = memoire.texte_injection_verbale(trouves)
    prompt = f"Souvenirs :\n{bloc}\n\nQuestion : {question}\nRéponse :"
    reponse = modele.repondre(prompt, systeme=SYS_REPONSE_C_VERBAL)
    return reponse, trouves


# ── LE JUGE ──────────────────────────────────────────────────────────────
def juger(question, reponse, trouves, model=None, think=None,
          systeme=None, montrer_confiance=True):
    """
    Demande au modèle-juge un verdict par souvenir injecté.
    Retourne un dict {id_souvenir: {"verdict":..., "justification":...}}.

    model/think       : permettent de tester un autre juge (ex. qwen3:30b-a3b, think=False).
    systeme           : prompt système du juge (par défaut SYS_JUGE ; utiliser
                        SYS_JUGE_DECOUPLE pour le juge découplé).
    montrer_confiance : si False, la confiance n'est PAS montrée au juge (pour interdire
                        mécaniquement qu'elle serve de critère → évite la boucle auto-renforçante).
    """
    if not trouves:
        return {}
    if systeme is None:
        systeme = SYS_JUGE

    lignes = []
    for s, _ in trouves:
        date = s.date_derniere_confirmation.strftime("%Y-%m-%d")
        if montrer_confiance:
            meta = f"confiance {s.confiance:.2f}, màj {date}"
        else:
            meta = f"màj {date}"
        lignes.append(f"#{s.id} ({meta}) : {s.contenu}")
    bloc = "\n".join(lignes)

    prompt = (
        f"QUESTION : {question}\n\n"
        f"RÉPONSE FOURNIE : {reponse}\n\n"
        f"SOUVENIRS À VÉRIFIER :\n{bloc}\n\n"
        "Rends ton verdict pour chaque souvenir, en JSON strict."
    )
    brut = modele.juger(prompt, systeme=systeme, model=model, think=think)

    resultat = {}
    for v in brut.get("verdicts", []):
        try:
            sid = int(v["id"])
        except (KeyError, ValueError, TypeError):
            continue
        verdict = str(v.get("verdict", "")).upper().strip()
        if verdict not in VERDICTS_VALIDES:
            verdict = "INCERTAIN"
        resultat[sid] = {
            "verdict": verdict,
            "justification": str(v.get("justification", "")).strip(),
        }
    return resultat
