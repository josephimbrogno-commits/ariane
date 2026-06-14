# 🔗 Typologie des liens par la structure

*Extension du projet mémoire (V1→V3 + Ariane). Née de la limite révélée par Ariane (l'oubli binaire
ampute les faits rares) : si la mémoire savait quels liens sont **durables** et lesquels sont
**éphémères**, elle saurait quels fils protéger de l'oubli — sans ontologie écrite d'avance.*

> **La structure seule du graphe peut-elle deviner la nature d'un lien — durable vs éphémère —
> sans qu'on la déclare ? Et de combien manque-t-il ?**

Méthode (les mêmes garde-fous qu'Ariane) : vérité-terrain **mécanique** posée par le générateur au
moment de créer chaque lien, **jamais** donnée au prédicteur ; banc **gelé** avant le premier score
(graine 42) ; et surtout des **cas-pièges** qui cassent volontairement la corrélation facile
connectivité↔nature — *le verdict se lit sur eux, jamais sur la moyenne*.

---

## Les quatre découvertes, dans l'ordre où elles sont tombées

### 1. Le renversement S1 / S2 — l'intuition de départ était le mauvais signal

Deux signaux structurels étaient candidats :
- **S1 — connectivité** : un lien entre deux nœuds riches en branches serait « fort » ; un lien vers
  un cul-de-sac (degré 1) serait « faible ». *C'était l'intuition de départ.*
- **S2 — temps + réciprocité** : un lien réciproque et sans date de fin serait durable ; une
  occurrence unique datée serait éphémère.

Sur les cas-pièges, le résultat est sans appel :

| | S1 (connectivité) | S2 (temps + réciprocité) |
|---|---|---|
| Cas-pièges (P-A à P-D + C-E) | **0 / 14** | **14 / 14** |
| Précision globale | 52 % | 73 % |

**La connectivité échoue 100 % des cas durs.** Le vrai discriminant n'est pas *combien de branches*,
mais *la forme temporelle et la réciprocité*. L'intuition s'est inversée : **S1 est le signal faible,
S2 le signal fort.** Mais S1 n'est pas inutile (cf. découverte 4) — il sert en *complément*.

**Lecture par faux positifs / négatifs (le cœur du renversement) :**

| Mode | FP (éphémère pris pour durable) | FN (durable manqué) | Ce qu'il apporte |
|---|---|---|---|
| S1 | **18** | 14 | du **rappel** (attrape des durables) mais aucune **rigueur** (inonde de faux positifs) |
| S2 | **0** | 18 | de la **rigueur** (0 FP : quand il dit durable, il a raison) mais manque des durables |
| S1+S2 | **0** | 6 | la rigueur de S2 **+** le rappel de S1 dans la zone ambiguë |

**S2 apporte la rigueur (0 FP), S1 apporte le rappel.** Les combiner garde le 0 FP de S2 et récupère
les durables que S2 seul manquait — sans jamais réintroduire un faux positif.

### 2. La hiérarchie « date d'abord » — prouvée par P-B et la réciprocité polluée

Dans S2, dans quel ORDRE lire les signaux ? Le cas-piège **P-B** (« j'ai mangé avec Maman ») tranche :
la détection de réciprocité y renvoie **oui** — non parce que « manger » serait réciproque, mais
parce que Maman est *aussi* ma mère (un lien `parent_de` en sens inverse existe). **La réciprocité
est polluée dès que deux entités partagent plusieurs relations.**

```
   P-B (éphémère) : réciproque=oui (pollué), occurrence=oui
      réciprocité AVANT date → DURABLE   ✗ FAUX
      date AVANT réciprocité → ÉPHÉMÈRE  ✓ JUSTE
```

D'où la hiérarchie interne de S2 : **(1) occurrence datée → éphémère (prime sur tout) ; (2) sinon
réciprocité → durable ; (3) sinon → éphémère.** La date d'abord, la réciprocité ensuite.

### 3. La distinction occurrence / début — prouvée par C-E

« Porter une date » ne suffit pas : un durable peut porter une date de **début** (« marié *depuis*
2015 »). Le contre-exemple **C-E** le montre — sans la distinction, « a une date » deviendrait un
faux signal qui condamnerait tous les durables datés :

```
   C-E « marié depuis 2015 » (durable) : porte_date=oui, occurrence=non (début ≠ fin)
      « porte une date » (naïf)  → ÉPHÉMÈRE  ✗ FAUX
      « occurrence ponctuelle »  → DURABLE   ✓ JUSTE
```

Le signal propre n'est pas *la présence d'une date* mais **la présence des DEUX bornes** (début ET
fin proches = occurrence ponctuelle). Un « depuis » (début, fin ouverte) reste durable.

### 4. Le chiffrage — 91 % par la structure, une frange de 13 % circonscrite et comblable sans bruit

Sur le grand monde gelé (49 entités, 66 liens, 12 pièges + 2 contre-exemples) :

| Mode | Précision |
|---|---|
| S1 (connectivité) | 52 % |
| S2 (temps + réciprocité) | 73 % |
| **S1 + S2** | **91 %** |
| **S1 + S2 + déclaration ciblée** | **100 %** |

**La structure suffit pour 91 % des liens, et 100 % des cas-pièges canoniques.** La frange aveugle
est **circonscrite et nommée** : **13 % des durables, EXCLUSIVEMENT des durables ASYMÉTRIQUES NON
DATÉS pointant vers un cul-de-sac** (diriger, appartenir, posséder, travailler-pour). Ni réciproques
(donc S2 ne les sauve pas), ni datés, ni entre deux carrefours (donc S1 non plus).

Une **déclaration minimale** — quatre types de prédicats déclarés durables — comble cette frange :
**6 / 6 récupérés, 0 bruit** (aucun éphémère basculé à tort), précision **91 % → 100 %**.

> *Détail révélateur : `S1+S2 (91 %) > S2 seul (73 %)`. La connectivité n'est donc pas inutile —
> elle récupère les durables asymétriques tendus entre **deux nœuds connectés**. Il ne reste aveugle
> que ceux qui pointent vers un **cul-de-sac**. C'est là, et seulement là, que la déclaration sert.*

---

## Verdict

**Oui, presque entièrement, la structure suffit.** Le temps (occurrence vs début) et la réciprocité
classent durable/éphémère à **91 %** et récupèrent **100 % des pièges** que la connectivité naïve
rate. Le reste — **13 % de durables, exactement les relations asymétriques non datées vers un
cul-de-sac** — échappe à toute topologie, et c'est honnête de le dire : pour ceux-là, une **béquille
ciblée de 4 types déclarés** suffit, sans aucun bruit.

**L'intelligence est donc bien, en grande partie, dans la structure — pas dans les déclarations.**
Et la mémoire peut désormais deviner, presque seule, quels fils protéger de l'oubli : les réciproques
et les ongoing, oui ; les occurrences datées, non. La limite d'Ariane (l'oubli binaire) trouve ici
sa boussole.

## Fichiers

```
structure_monde.py       générateur déterministe : 4 familles de pièges + contre-exemple, features
                         structurelles (degrés, réciprocité, forme temporelle), vérité-terrain
structure_predicteur.py  S1 / S2 (hiérarchie date-d'abord) / S1+S2 / + ablations
etape_structure_1        affichage de la vérité-terrain (les pièges trompent-ils bien S1 ?)
etape_structure_2        prédicteur + ablation sur mini-monde (la hiérarchie, le contre-exemple)
etape_structure_3        grand monde : confusion, score par famille, frange chiffrée, déclaration
resultats/structure_3_*  rapport + données
```

---

*L'intuition de départ (la connectivité) était le signal faible ; on l'a su en cassant la corrélation
facile avec des pièges, et en lisant le verdict sur eux seuls. La structure voit presque tout — et on
sait nommer exactement les 13 % qu'elle ne voit pas.*
