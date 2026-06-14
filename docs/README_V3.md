# 🧭 La mémoire qui trie — V3 : l'axe IMPORTANCE (et ce que l'ablation a vraiment montré)

*Extension de la V2 (cf. `README_V2.md`). Un troisième axe — l'**Importance** — ajouté SANS refonte.
Et un résultat d'ablation honnête : sur ce banc, **l'idée simple a battu l'idée riche**.*

---

## 1. L'idée : protéger ce qui COMPTE, pas ce qui est récent

Le grand run V2 a montré que 16 des 17 erreurs venaient du retrieval : des faits **vrais mais peu
consultés** tombaient en dormance et devenaient **muets** (introuvables de face). Le correctif n'est
pas de protéger le *certain* (un fait trivial peut être très certain), mais ce qui **compte**. D'où
un troisième axe, **orthogonal** aux deux autres :

```
 Force      = m'en souviens-je facilement ?  (érode avec le temps, monte à la consultation)
 Certitude  = est-ce encore vrai ?            (érode avec le temps, monte à la corroboration)
 IMPORTANCE = combien cela compte-t-il ?      (NE décroît PAS ; dérivée de la STRUCTURE du graphe)   ← NOUVEAU
```

Exemple fondateur : « **le nom d'un proche** » (rarement consulté → Force basse, mais Importance
maximale) doit SURVIVRE, tandis que « **le repas de mardi** » (consulté il y a 4 jours → Force haute,
Importance nulle) doit pouvoir s'effacer. La V2 faisait l'inverse.

---

## 2. Comment l'importance se calcule (`v3_importance.py`)

- **Importance des entités** : PageRank pondéré (« la rivière »). Une entité est importante si elle
  est reliée à des entités elles-mêmes importantes. Arêtes = faits à objet-entité, pondérées par le
  **poids de relation** (ontologie) ET la **Certitude** du fait porteur. Amorçage (seeds) par : degré,
  nombre de **sources indépendantes**, et bonus de **catégorie** (personne / organisation / …).
  Recalculé au **sommeil** (pas à chaque écriture).
- **Importance d'un fait** : `poids_relation × max(imp_sujet, imp_objet)^α`. C'est le **croisement** :
  la relation peut écraser l'entité.

Les trois cas tombent juste *automatiquement* (micro-test étape 1) :

| Fait | Importance | Pourquoi |
|---|---|---|
| nom de ma mère | **1.00** (CAPITAL) | relation forte × entité capitale |
| M. Inconnu parent de Mlle Obscure | 0.40 (MOYEN-FAIBLE) | relation forte × entités sans importance |
| repas de ma mère | 0.05 (FAIBLE) | relation triviale qui écrase l'entité |

---

## 3. Ce que l'importance modifie (et la reconnaissance/rappel)

- **Dormance modulée** : `seuil = base × (1 − β·importance)`. Importance ≈ 1 → seuil ≈ 0.015
  (ne dort quasiment jamais) ; importance ≈ 0 → seuil ≈ 0.15 (comportement V2).
- **Reconnaissance / rappel** (le mécanisme décisif) : quand la question **NOMME** une entité, on
  entre TOUJOURS par ce nœud et on lit ses faits **dormants compris**. La dormance ne bloque que
  l'évocation *libre* (similarité pure), jamais la reconnaissance *directe*.
- **Retrieval** : terme d'importance ajoutable au score (`w·sim + w·Force + w·importance + w·entité`).

Micro-tests (étapes 1-2), tous ✅ :
- l'inversion proche/repas est réparée (à Force égale 0.05, le nom survit, le repas s'efface) ;
- un fait dormant redevient lisible dès qu'on **nomme** son entité ;
- **un fait capital contredit est CLOS et rendu à l'imparfait** comme n'importe quel fait —
  l'importance protège de l'OUBLI, **jamais** de la CONTRADICTION.

---

## 4. Le grand run + l'ABLATION — le verdict honnête

Quatre lectures sur le **même graphe** (donc même « greffier ») : C-v2 (V2) · C-v3-β0 (porte seule,
sans importance) · C-v3-dorm (porte + importance en dormance, hors retrieval) · C-v3 (axe complet).

| | C-v2 | **C-v3-β0 (porte)** | C-v3-dorm | C-v3 (axe) |
|---|---|---|---|---|
| **Faits muets** | 16 | **6** | 8 | 8 |
| Faits changés | 70 % | 80 % | 75 % | 75 % |
| Faits stables | 45 % | **85 %** | 80 % | 80 % |
| Global (strict) | 58 % | **82 %** | 78 % | 78 % |
| Non-régression | — | menteur 5/5 · rumeur OK · Dupont 3/3 | | |

### Le verdict en trois temps

1. **La porte d'entrée par nœud (reconnaissance/rappel) est le VRAI correctif.** Elle fait tomber les
   faits muets de **16 → 6** et remonter les stables de **45 % → 85 %**, à elle seule, sans aucune
   importance. **L'idée simple bat l'idée riche — et l'ablation le prouve**, en l'isolant.

2. **L'importance dans le RETRIEVAL est NEUTRE.** `C-v3-dorm` et `C-v3` sont *identiques* : ajouter le
   terme d'importance au score ne change rien. → **retirée** (complexité sans bénéfice).
   *(Honnêteté : nous avions d'abord soupçonné ce terme d'être la source du bruit. La variante de
   confirmation a réfuté cette hypothèse — c'est ailleurs que se loge le léger surcoût.)*

3. **L'importance en DORMANCE est conservée comme assurance — mais NON démontrée, et même légèrement
   coûteuse ici.** Passer de `β0` à `dorm` dégrade un peu (muets 6 → 8, stables 85 % → 80 %) :
   protéger les faits importants les garde *actifs*, donc ils encombrent l'évocation vectorielle et
   chassent parfois le bon fait. Le bénéfice attendu (faire survivre un fait capital pour qu'il reste
   navigable) ne se manifeste pas sur ce banc.

---

## 5. La limite du protocole (l'angle mort, documenté comme tel)

**Ce banc d'essai est aveugle au vrai métier de l'importance.** *Toutes* les questions d'évaluation
**nomment leur entité** → la reconnaissance suffit toujours, et la protection-dormance ne sert jamais
(la reconnaissance lit déjà les dormants). Il n'y a **aucune question de RAPPEL LIBRE** (« qui est la
personne la plus importante de mon entourage ? » sans la nommer), **aucune épreuve de survie à long
horizon** (un fait capital jamais consulté pendant des années, qu'il faut retrouver *ensuite*).

**Conséquence honnête : l'importance n'est pas réfutée — elle est NON TESTÉE.** Son terrain propre
(rappel sans nommer, survie pour navigation future) n'existe pas dans ce protocole. Conclure « l'axe
ne sert à rien » serait une faute : la bonne conclusion est « **ce banc ne sait pas le mesurer** ».
Le prochain pas n'est pas de retoucher l'axe, mais de **construire un banc de rappel libre**.

---

## 6. Ce qui est livré

- **Recommandation** : en production sur ce type de charge, activer **la porte (reconnaissance/rappel)
  seule** — config `C-v3-β0`. C'est le meilleur des quatre.
- **L'axe importance reste dans le code** (calculé au sommeil, disponible), **désactivé par défaut**
  pour le retrieval, et conservé en option pour la dormance — en attendant un banc qui lui rende
  justice.
- Le mécanisme de calcul (PageRank + croisement) est correct et intuitif (micro-tests), et le cas
  fondateur **proche / repas** reste l'exemple de référence de *pourquoi* l'importance devrait compter.

## 7. Fichiers V3

```
v3_importance.py        PageRank pondéré (entités) + croisement (faits) ; calculer() au sommeil
v2_ontologie.py         + POIDS_IMPORTANCE par prédicat ; prédicats nom_de / parent_de / repas_de
v2_modele.py            Entite.type/.importance, Fait.importance ; dormance modulée + recalculer_dormance(β)
v2_lecture.py           reconnaissance(), entree_vectorielle_v3 (score combiné)
etape_v3_1_importance   micro-test du calcul (mini-graphe familial, 3 cas de croisement)
etape_v3_2_dormance     micro-test dormance modulée + reconnaissance + contradiction d'un fait capital
etape_v3_3_grand_run    grand run + ABLATION à 4 modes
```

---

---

## Suite — le banc « Ariane » (le crash test promis)

Le protocole de rappel libre qui manquait a été construit (**`README_ARIANE.md`**). Verdict : sur son
terrain (rappel libre de faits capitaux jamais consultés), **l'axe importance est vindiqué** —
survie des capitaux 8/38 → **38/38**, complétude **25 % → 64 %**. Mais ce n'est pas une victoire
nette : le banc révèle que **la dormance elle-même** s'effondre en pureté sur le rappel par attribut,
là où ni la porte ni l'importance n'aident. *Usage démontré, coût mesuré, limite plus profonde mise
au jour.*

---

*L'idée simple a battu l'idée riche — et l'ablation a même corrigé notre hypothèse en cours de route.
Ce n'est pas l'axe importance qu'il faut retoucher, c'est le protocole qui doit apprendre à poser une
question de rappel libre. Garder ce qui marche, mesurer honnêtement ce qui reste à prouver.*
