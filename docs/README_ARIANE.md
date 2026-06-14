# 🧵 Ariane — le banc de rappel libre (le crash test de l'axe Importance)

*Extension du projet mémoire (V1→V3). Son unique but : trancher, mécaniquement et honnêtement, la
question que le grand run V3 avait laissée ouverte (« importance NON TESTÉE »).*

> **Sur des questions de RAPPEL LIBRE (où l'entité cible n'est jamais nommée), après un long
> silence, l'axe importance fait-il remonter les faits CAPITAUX que la porte seule laisse
> s'endormir et disparaître ? À quel coût en pureté ?**

---

## 1. Règles de méthode (non négociables, posées AVANT le run)

- **Vérité mécanique** : la vérité-terrain (quel fait doit remonter à quelle question, avec quel
  statut) est produite par le GÉNÉRATEUR en code déterministe. **Jamais** par un LLM. La notation
  aussi est mécanique (contre la vérité). *Aucun LLM dans la boucle de score.*
- **Banc gelé avant observation (anti-Goodhart)** : monde + questions + vérité générés et figés,
  **graine loguée** (42), AVANT de lancer la moindre config. Aucune question retouchée après coup.
- **Petit d'abord** : générateur et notation validés sur un mini-monde (étapes 1-2) avant le grand run.

> Note d'honnêteté : le script produisait un verdict automatique « l'axe a gagné » dont le seuil
> s'est révélé **trop indulgent** (il comparait la pureté de l'axe à celle de la porte, déjà cassée).
> Le verdict ci-dessous est la **lecture corrigée** des chiffres, pas l'étiquette automatique.

## 2. Le monde (contrasté par construction)

50 entités, 104 faits, horizon 24 mois. Chaque fait porte un profil :

| Profil | n | Rôle |
|---|---|---|
| **P1** Capital & **jamais consulté** | 38 | la CIBLE : Force basse, Importance haute → sans l'axe, s'endort |
| **P2** Trivial & récent | 12 | distracteur (Force haute) |
| **P3** Capital & **périmé** (clos) | 14 | piège : ne doit remonter qu'à l'imparfait |
| **P4** Moyen | 40 | bruit (professions, sièges…) |

30 questions de **rappel libre** : **T1** par attribut (« qui est médecin ? »), **T2** par relation
indirecte autour d'une entité nommée, **T3** « bout de la langue » (un capital jamais consulté,
évoqué sans nommer l'entité — *la* question qui justifie l'axe).

## 3. La notation (mécanique)

- **Complétude** = rappel@K : les faits-vérité sont-ils dans le top-K évoqué ?
- **Pureté** = précision@|vérité| : les pertinents arrivent-ils en tête, ou des capitaux hors-sujet
  les déplacent-ils ? (métrique adaptative — attrape l'inondation.)
- **Justesse de statut** : un P3 (clos) servi à l'imparfait = juste ; au présent = faux (distinct de
  l'absence, qui n'est qu'une perte de complétude).

Le banc se valide lui-même (étape 2) : la réponse « déverse-tout-le-capital » est **nettement
pénalisée en pureté (18 %)** — le garde-fou contre une importance trop agressive fonctionne.

## 4. Résultats (graine 42, banc gelé)

| Config | Survie des P1 | **Complétude P1 @ T3** | **Pureté @ Q8+T1** |
|---|---|---|---|
| **inerte** (similarité seule, n'oublie jamais) | — | 44 % | **87 %** |
| **porte** (reconnaissance, dormance β=0, sans importance) | 8 / 38 | 25 % | 8 % |
| **axe** (reconnaissance + importance, β=0.9) | **38 / 38** | **64 %** | **0 %** |

## 5. Le verdict — tranché, et nuancé

**1. L'importance FAIT son travail sur son terrain.** La dormance modulée garde **38/38** P1 vivants
(contre 8). En rappel libre « bout de la langue » (T3), la complétude des capitaux passe de
**25 % (porte) à 64 % (axe)** : **+39 points**. À la question « l'axe fait-il remonter les capitaux
que la porte laisse disparaître ? », la réponse mécanique est **OUI**. Ce que la V3 déclarait « non
testé », Ariane le **vindique** : le mécanisme fonctionne.

**2. Mais ce n'est PAS une victoire nette — et le banc révèle un ennemi plus grand que l'importance.**
- En isolant l'effet propre de l'axe (axe vs porte), la pureté ne baisse que de **−8 points**
  (inondation par le capital sur Q8 — le banc l'attrape, comme prévu). Petit coût.
- Mais la pureté *absolue* s'effondre pour **porte ET axe** (8 % / 0 %) face à l'inerte (**87 %**).
  La cause n'est PAS l'importance : c'est **la dormance elle-même**. Sur le rappel par **attribut**
  (T1, « qui est médecin ? »), les faits pertinents sont eux aussi rarement consultés → **dormants**,
  et T1 ne nomme aucune entité → la reconnaissance ne peut pas les sauver. Seul l'entrepôt qui
  **n'oublie jamais** les garde.

**Donc, selon la règle stricte (« gain de complétude SANS chute de pureté = gagné »), l'axe n'a pas
gagné proprement : il y a une chute de pureté.** La lecture honnête n'est ni « gagné » ni « réfuté » :

> **L'axe importance a un usage DÉMONTRÉ (le rappel libre de faits capitaux, son terrain propre), à
> un coût mesuré (légère inondation). Mais le crash test a surtout mis au jour une limite plus
> profonde : l'OUBLI lui-même (la dormance) coûte cher sur le rappel par attribut, là où ni la porte
> ni l'importance n'aident — seul un store sans oubli y tient.**

## 6. Ce que ça change pour le système

- **L'axe importance est justifié** pour les mémoires à très long horizon où des faits capitaux
  doivent survivre sans consultation et être évoqués librement plus tard. Sur ce besoin, il gagne.
- **Mais la dormance reste une arme à double tranchant** : elle réduit le bruit, mais ampute le
  rappel par attribut des faits rares. Piste : entrée vectorielle qui *inclut* les dormants avec une
  pénalité (au lieu de les exclure), pour que l'oubli baisse le rang sans rendre muet.
- **Pour une charge où l'on nomme toujours l'entité** (le cas du banc V3), la porte seule reste le
  meilleur choix — l'axe n'y apporte rien. Le bon réglage dépend du **type de rappel** attendu.

## 7. Fichiers

```
ariane_monde.py        générateur déterministe : 4 profils, questions T1/T2/T3, vérité-terrain
ariane_notation.py     complétude × pureté × F-mesure + justesse de statut (mécanique)
etape_ariane_1         affichage de la vérité-terrain (vérification à la main)
etape_ariane_2         test de la notation sur réponses factices (dont « déverse-le-capital »)
etape_ariane_3         le grand run mécanique : 4 configs, les deux chiffres décisifs, le verdict
resultats/ariane_3_*   rapport + données
```

---

---

## Suite — « Typologie des liens par la structure »

La limite révélée ici (l'oubli binaire ampute les faits rares) a ouvert une question : et si la
mémoire devinait, par la **seule structure du graphe**, quels liens sont *durables* (à protéger) et
lesquels sont *éphémères* (oubliables) ? Réponse mesurée (**`README_TYPOLOGIE.md`**) : **oui à 91 %**
— le temps (occurrence vs début) et la réciprocité suffisent et récupèrent 100 % des cas-pièges ; la
frange restante (13 %) est circonscrite aux durables asymétriques non datés, comblée sans bruit par
une déclaration ciblée. *L'intelligence est, en grande partie, dans la structure.*

---

*On cherchait la rupture, pas la confirmation. Le banc a donné les deux : l'axe prouve son usage
sur son terrain, et révèle que le vrai problème non résolu est le coût de l'oubli sur le rappel par
attribut. Un crash test réussi ne dit pas « ça marche » — il dit exactement où ça tient et où ça casse.*
