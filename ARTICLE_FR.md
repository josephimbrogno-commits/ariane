# Ariane — une mémoire qui trie le périmé

*Ce que six échecs et un test sur le monde réel m'ont appris sur la mémoire des machines.*

---

## Le problème : se tromper avec assurance

Les modèles de langage savent beaucoup de choses, mais leur savoir est **figé**. Une fois entraînés, ils ne savent plus que le monde a changé. On greffe alors sur eux une *mémoire externe* — le plus souvent un système de récupération (RAG) qui stocke des notes et les ressort par similarité. Cela règle l'oubli, mais pas le pire défaut.

Le pire défaut, le domaine lui a donné un nom en 2026 : **« confidently wrong »** — se tromper avec assurance. Un souvenir très consulté reste pertinent jusqu'au jour où il devient faux ; à ce moment, l'agent le sert toujours avec aplomb, sans le moindre signal d'alerte. Les chiffres publiés sont parlants : environ **un tiers des faits stockés dans une mémoire d'agent deviennent incorrects en 90 jours**, et la péremption des souvenirs *à haute pertinence* est explicitement classée parmi les problèmes **ouverts** les plus durs du domaine (aux côtés de l'identité inter-sessions et de l'abstraction temporelle à l'échelle). Un agent sans mémoire qui redemande « quel est votre poste ? » est simplement agaçant. Un agent avec une mémoire périmée *affirme* l'ancien poste comme un fait établi. C'est pire.

Ce projet attaque ce point précis. Pas l'oubli — le **tri du périmé**.

---

## L'idée : le souvenir est dans le fil, pas dans le nœud

Le point de départ est une image. La mémoire humaine ne range pas des faits isolés : elle tisse des *liens*. On voit un visage, on retrouve un nom, puis un métier, puis une relation — on suit des fils, comme sur une toile. Et ces fils ne sont pas tous égaux : certains sont vifs, d'autres poussiéreux ; certains sont sûrs, d'autres douteux ; certains comptent, d'autres sont triviaux.

De là, trois principes simples, qui sont devenus les lois du système :

1. **Seul le faux se réécrit.** Une information confirmée ne change pas — elle se renforce. Seule une *contradiction* déclenche une mise à jour. Et cette mise à jour n'efface jamais : elle **clôt**. « Karel *était* PDG jusqu'en mai 2026 » reste vrai pour toujours, comme fait historique, pendant que « Doss *est* PDG » prend le présent.
2. **La réponse nourrit la flamme, seul le monde l'éteint.** Consulter un souvenir le ravive (il reste retrouvable) ; mais seule une *source indépendante* qui le corrobore augmente sa **certitude**. Répéter cent fois une rumeur ne la rend pas vraie : une source unique reste plafonnée, quoi qu'elle martèle.
3. **Ce que le monde atteste résiste à l'oubli.** Un fait capital mais rarement consulté ne doit pas mourir de négligence. L'importance d'un lien se lit dans la *structure* : ce vers quoi convergent beaucoup d'autres liens compte plus que ce qui aboutit à une impasse.

Concrètement, chaque fait porte trois axes **indépendants** — sa *force* (m'en souviens-je ?), sa *certitude* (est-ce encore vrai ?), son *importance* (cela compte-t-il ?) — et une **grammaire épistémique** au moment de répondre : présent pour le sûr, imparfait pour le clos (« était… jusqu'à »), conditionnel pour l'incertain (« serait… à revérifier »), et « je ne sais pas » quand c'est vrai.

---

## La méthode : garder les échecs comme des résultats

Ce système n'est pas né d'un plan. Il est né d'une série d'échecs, chacun compris et transformé. C'est la partie la plus utile à raconter, parce que chaque mur a livré un principe.

**Le suicide du mois 3.** La première version effaçait les faits sous un seuil de confiance. Résultat : en trois mois simulés, elle a tué 94 faits vrais sur 95. Leçon : *ne plus être sûr n'est pas ne plus savoir*. On ne détruit pas — on déclasse. C'est la naissance de la distinction force/certitude.

**Le prompt durci.** Face à un juge qui se trompait, le réflexe a été d'alourdir ses consignes. Ça a *empiré* les choses (une catastrophe est devenue quatre). Leçon : *l'intelligence va dans les données, pas dans les instructions*. On ne répare pas un système en empilant des règles.

**Le juge scindé.** Pour isoler une décision, on a séparé un module en deux appels plus « purs ». Pire encore. Leçon : *un modèle de langage juge mieux avec le contexte entier qu'isolé* — la pureté architecturale peut coûter plus que la contamination qu'elle évite.

**Le hedging.** Une métrique trop indulgente récompensait les réponses qui ne tranchaient pas. En la durcissant, un faux champion s'est effondré. Leçon : *quand la mesure récompense l'esquive, elle cesse de mesurer*.

**Le menteur.** Une source unique, par le seul jeu de la fraîcheur, finissait par paraître plus certaine qu'une vérité ancienne. Leçon : il faut un **plancher de certitude** pour ce que le monde a corroboré, sinon le neuf supplante le vrai.

**L'importance non vindiquée — puis vindiquée.** Un troisième axe (l'importance, calculée par la structure du graphe) ne montrait aucun gain sur les premiers bancs. Plutôt que de le déclarer utile par principe, on a construit un banc *exprès* pour le mettre à l'épreuve — « Ariane », du nom de la fusée : ça passe ou ça casse au décollage. Verdict : l'importance sert sur son vrai terrain (retrouver un fait capital jamais consulté), *et* le banc a révélé une limite plus profonde ailleurs (l'oubli binaire). Le système a même corrigé son propre verdict initial, trop indulgent. *(Cet oubli binaire a depuis été corrigé : la dormance n'est plus un interrupteur muet/présent mais une pente — un fait rare bien corroboré redevient audible en rang bas malgré des mois sans consultation, tandis que le fait fragile reste en bas. La même leçon — remplacer un couperet par un dégradé — appliquée une fois de plus.)*

Six murs, six principes. Aucun n'a été caché ; chacun est documenté dans le dépôt.

---

## Le test : face au monde réel

Tous les bancs ci-dessus étaient synthétiques. Restait l'épreuve : des faits **réels, datés, vérifiables par quiconque**. On a branché la mémoire sur un vrai agent (le framework OpenClaw, en local), et on l'a testée sur deux terrains opposés au 14 juin 2026 : la composition du CAC 40 (entrées/sorties datées) et les qualifications de la Coupe du monde 2026 — plus un piège (le cours de l'indice, qui dérive en continu) et un menteur (de faux faits à source unique).

Quatre configurations, mêmes questions, vérité-terrain établie à la main (jamais par un modèle) :

| Configuration | Bonnes réponses | « Confidently wrong » |
|---|---|---|
| Agent nu | ~57 % | 2-3 — affirme des faits périmés (Scholz chancelier, Alstom au CAC) |
| RAG, notes bien tenues | 93 % | 0 |
| Notre mémoire (tri) | 93 % | 0 |
| RAG, notes naïves | 40 % | 3/3 — sert le périmé et les menteurs avec aplomb |

Le résultat est honnête, et il dérange : **un RAG bien nourri, avec un bon modèle, trie aussi bien que nous — à égalité sur la justesse brute (93 % chacun).** Quand chaque note porte sa date en clair, le modèle lit « sortie en septembre 2025, on est en juin 2026 » et conclut seul. La thèse naïve « le tri bat le rappel » ne tient pas dans ce cas. Sur ce qui compte vraiment, les deux sont à égalité : **zéro erreur d'assurance** sur les quatorze questions.

Une précision honnête s'impose ici, car elle nuance le tableau : l'agent nu n'est pas si démuni qu'on pourrait le croire. Le modèle local connaît déjà certains faits récents (il sait que Merz est chancelier — sa coupure d'entraînement est récente). Le contraste n'éclate donc pas partout : il éclate sur l'**obscur vérifiable**, les faits qu'aucun modèle n'a en mémoire — les sorties du CAC 40 de 2025, par exemple. C'est là, sur ce que le monde a changé sans que personne de célèbre en parle, que la mémoire fait la différence.

Mais regardez la dernière ligne. Dès que les notes ne sont **pas** disciplinées — le cas réel le plus fréquent — le RAG s'effondre : il ressort l'ancien et le nouveau sans les départager, et sert le menteur comme la vérité. Notre mémoire, elle, n'a produit **aucune** erreur d'assurance sur tout le test.

La vraie valeur n'est donc pas d'être *plus maligne* que le RAG. C'est de rendre la correction **structurelle** :

> Chez nous, la clôture datée, le plafond du menteur et le « à revérifier » du volatil sont des **garanties du moteur** — pas des espoirs suspendus à la qualité des notes et à la bonne volonté du modèle.

Un RAG trie *si* on l'a bien nourri. Une mémoire structurée trie *parce que* l'architecture l'impose. En production, où les données arrivent sales, c'est toute la différence.

---

## Les limites, mesurées

Un labo honnête publie ses fissures.

- **Extraction sur langage réel : refondue.** Le module qui transforme une phrase en fait structuré était le goulot du système (~40 % sur le langage réel au départ). Il a été reconstruit en quatre axes indépendants — polarité, modalité, temporalité, rôle/direction — sur le modèle de la mémoire elle-même (des axes séparés plutôt qu'une décision unique). Résultat sur un banc à l'aveugle de six domaines : **zéro faux positif de polarité**, inversions de rôle corrigées (4 → 0 par dérivation des types), et une couverture portée à **~90 %** grâce à une ontologie *induite des textes* (un modèle propose, un autre retranche, l'humain valide). La résolution d'entités, désignée alors comme prochain chantier, a depuis été traitée sur ses deux faces : la **collision** (deux entités fondues à tort, « France » et « Business France ») par une fusion conditionnée à la compatibilité de type ; la **fragmentation** (une entité éclatée en plusieurs nœuds, « MSFT » et « Microsoft ») par une réunion fondée sur la structure des liens pondérée par la rareté, et non sur l'embedding (mesuré non fiable ici). Reste un résidu mineur nommé : la fusion d'acronymes très courts, traitée par normalisation et un malus de brièveté sur l'embedding.
- **Le rendu n'expose pas la date de début de validité** des faits courants — d'où un échec sur « qui est entré dans l'indice en 2025 ? ». Limite d'affichage, pas de fond.
- **Le cours continu** n'est pas du ressort d'une mémoire de faits : un prix qui change chaque seconde n'a pas de « date de bascule ». Le bon comportement est de le reconnaître et de ne pas l'affirmer — pas de le trancher.

---

## Où ça se situe

Ce projet n'est pas seul sur ce terrain, et c'est tant mieux : le « confidently wrong » est un problème activement travaillé. Mem0 le nomme dans son état de l'art ; des outils comme MemGuard ajoutent une couche de validation à côté de la mémoire ; Zep construit un graphe de connaissances temporel. La plupart valident *après coup* (re-vérifier périodiquement) ou trient *à la lecture*. L'angle de ce projet est différent : rendre le tri **structurel à l'écriture** — la contradiction se résout au moment où le fait entre, fait contre fait, dates contre dates, sans modèle dans la boucle de décision. La grammaire épistémique (« était / serait / je ne sais pas ») et la règle d'or (on lit la toile librement, on ne tisse jamais un fil sans dire d'où il vient) en sont les deux signatures.

---

## Pour finir

Le résultat tient en une phrase : **une mémoire structurée n'est pas plus intelligente qu'un bon RAG — elle est plus fiable quand le monde est sale.** Et l'agent nu, qui affirme encore le périmé sur les faits que son entraînement n'a pas vus — des sorties d'indice, des bascules discrètes que chacun peut pourtant vérifier — rappelle pourquoi la question mérite qu'on s'y arrête.

---

### Post-scriptum

Ce projet a été mené par quelqu'un sans formation en apprentissage automatique. Je n'ai pas écrit le code ni manié les mathématiques : j'ai travaillé les **concepts**, l'architecture, les décisions, et confié l'implémentation à un assistant. Je n'ai volontairement pas cherché ce qui existait avant d'avoir terminé — le projet est né du raisonnement, pas de la littérature. J'en mesure la limite, et elle est probablement importante : il est vraisemblable que des pans entiers recoupent des travaux existants, et la confrontation à l'état de l'art (Mem0, MemGuard, Zep) n'est venue qu'à la fin. Ce n'est pas un produit ni une publication scientifique. C'est un **laboratoire** — une idée poussée jusqu'au bout pour voir où elle casse.

— Joseph Imbrogno
