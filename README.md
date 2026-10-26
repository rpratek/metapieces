# Les Métapièces — la théorie, les mesures et l'application

*English summary.* Companion repository for the book **Les Métapièces** (Richard Pratek, in preparation). The book argues that a chess piece has no fixed value: what counts is what it produces in cooperation with the others (a *Metapiece*, from a single piece to groups of five). This repository holds (1) an application that turns any PGN game into an interactive page showing, move by move, the squares each piece controls, the king's flight squares and what each move gains or loses; (2) two worked examples, Carlsen – Nakamura (the book's running example) and Fontaine – Vachier-Lagrave; (3) the Python scripts and the research report behind the measurements quoted in the book; (4) the diagram tools. The measurements are correlations on real games, not proofs. **Redo these measurements, contradict them, propose better, and share.**

## Le livre en quelques lignes
**Les Métapièces** est un livre en trois parties :
- **Livre I, les origines** : le jeu et ses pièces dans l'histoire, de Jacques de Cessoles (vers 1300) à la montée en puissance de la Dame ;
- **Livre II, nouveau traité de stratégie** : un catalogue de Métapièces, 59 parties commentées, des chapitres sur le temps, le chunking et la gestion des flux, et un cahier d'entraînement (le système Obi) ;
- **Livre III, la Métapiècité** : la même idée hors de l'échiquier (nature, famille, sport collectif, entreprise, jeux de cartes, arts martiaux, mathématiques).

Son idée centrale : **une pièce n'a pas de valeur fixe**. L'échelle 1-3-5-9 dit ce qu'une pièce vaut sur le papier ; le livre propose de regarder ce qu'elle **produit** dans une configuration donnée. Un groupe de pièces qui coopèrent est une **Métapièce**, du Monôme au Pentanôme. Trois notions la portent :
- le **Couple Moteur** de la Métapièce : **puissance × coopération × embrayage**. Une grande puissance ne sert à rien si la défense empêche de la transmettre (la Ferrari et la tondeuse) ;
- le **Territoire** et le **flux** : l'ensemble des cases que les pièces contrôlent, et ce que chaque coup gagne ou perd ;
- l'**unification de la stratégie et de la tactique** (§ 2.6, « le chaînon manquant »).

L'image du livre est celle d'une **salle de bal** : chaque pièce de la Métapièce est un lustre qui éclaire les cases qu'elle contrôle ; là où les lumières convergent, le Roi adverse n'a plus que des zones d'ombre pour fuir. L'application met cette image en mouvement.

## À quoi sert ce dépôt
Le livre cite des mesures sur des parties réelles et un exemple fil rouge (§ 5.1). Ce dépôt permet de **refaire ces mesures** et d'**essayer l'idée sur n'importe quelle partie**, sans rien croire sur parole.

**Refaites ces mesures, contredisez-les, proposez mieux, et partagez.**

## Le fil rouge : Carlsen – Nakamura
Partie du Speed Chess Championship 2023, résultat ½-½ selon le fichier. Aux coups 40 à 44, les Blancs sacrifient deux Tours : 40.Txc5+ bxc5 41.Tc7+ Rxc7 42.Dxc5+ Rb7 43.Dd5+ Rb8 44.Fe5+. Le dossier `exemples/carlsen_nakamura/` contient la partie, la **page de l'application** (à ouvrir d'un double-clic), le script qui reproduit le tableau et les trois diagrammes du livre, et une page d'explication. Un second exemple, Fontaine – Vachier-Lagrave (championnat de France 2007), est dans `exemples/fontaine_mvl/`.

## Contenu du dépôt
- **`application/`** : le programme `metapiece_territoire.py` et ses deux tests de validation (`valider_fuites.py`, `valider_fleches.py`).
- **`exemples/`** : les deux parties, leurs pages HTML et leurs explications.
- **`recherche/`** : le dossier de recherche (version 2, PDF et Word) et les scripts des mesures, avec leur guide d'utilisation.
- **`outils/`** : l'outil de dessin des diagrammes du livre.
- **`donnees/`** : à remplir par vous (voir `donnees/LISEZMOI.md`).

## Démarrage rapide
1. Python 3.9 ou plus récent ; puis, une seule fois : `pip install -r requirements.txt`
2. `python3 application/metapiece_territoire.py votre_partie.pgn` crée `votre_partie_territoire.html`.
3. Double-cliquez sur le fichier HTML : choisissez le camp, l'affichage (salle de bal ou analyse), ce que fait le coup (rien, cases, flèches), et cochez « avec les pions » si vous le souhaitez.

## Rejouer nos mesures
1. Téléchargez les deux numéros de **The Week in Chess** (n° 1637 et n° 1662) et placez-les dans `donnees/` (voir `donnees/LISEZMOI.md`).
2. Pour voir tout de suite le Couple Moteur sur trois exemples, sans aucune donnée : `python3 recherche/scripts/couple_moteur_exemple.py`. Pour refaire la mesure complète, depuis `donnees/` : `python3 ../recherche/scripts/couple_moteur_v2.py`.
3. **Vos propres parties.** Chaque script de mesure accepte un ou plusieurs fichiers PGN en argument (les jokers sont permis) : `python3 ../recherche/scripts/mat_necessaire.py mes_parties.pgn`. Sans argument, il lit `twic1637.pgn` et `twic1662.pgn` dans le dossier courant. Toutes les parties libres de droits conviennent, par exemple la base ouverte de Lichess (licence CC0 ; les fichiers sont à décompresser avant usage). Les trois scripts qui font appel à un moteur d'échecs (`audit_epreuve.py`, `couple_moteur.py`, `synergie_paires.py`) lisent le fichier désigné par la variable d'environnement `PGN`.
4. Le fichier `recherche/scripts/INDEX_DES_MESURES.md` dit, pour chaque mesure, quel script la produit et ce qu'elle dit.

## Comment lire nos chiffres
Les chiffres décrivent de **bonnes parties, souvent du blitz en ligne** : ce qui se passe en moyenne, pas ce qui arrivera dans votre partie. Trois niveaux de confiance :
- **Établi** : retrouvé sur deux séries de parties, ou sur des parties que la mesure n'avait jamais vues ;
- **Mesuré** : trouvé sur une seule série, à confirmer ;
- **Observation** : une idée de l'auteur, non mesurée.
Un chiffre ne prouve jamais une cause : il propose une lecture.

## Questions ouvertes
Ce que nous aimerions voir testé par d'autres :
- la **convergence** (deux pièces qui visent les mêmes cases) tient-elle dans les **parties de club** et en **cadence longue** ?
- le **Couple Moteur** s'applique-t-il aux **Rois non roqués** ?
- la **règle de dimensionnement** (la Métapièce recrute des pièces tant que la défense tient) se retrouve-t-elle sur d'autres bases ?
- les **exécutants du mat** (la Dame et la Tour, dans 88 % des mats de nos données) sont-ils les mêmes ailleurs ?
- côté sciences du mouvement : la **latéralité manuelle** et le style de jeu (Annexe A du livre) : une piste que l'auteur dit lui-même « à établir ».

## Proposer une contre-épreuve
Ouvrez une *Issue* ou une *Pull request* sur GitHub. Dites sur quelles parties, avec quel script (le vôtre ou le nôtre) et ce que vous avez trouvé. **Un résultat qui contredit le nôtre est une contribution, pas une attaque ; un résultat négatif aussi.** Et partagez : vos jeux de parties, s'ils sont libres de droits, et vos scripts.

## Ce que ce dépôt ne prétend pas
- La Métapièce est ici une **définition opérationnelle** (des territoires qui convergent), pas la seule possible.
- Les mesures portent sur deux numéros de TWIC : ce sont des **corrélations**, pas des preuves de causalité.
- Le flux **n'est pas une évaluation** de la position : il ne remplace pas un moteur.
- Le Couple Moteur de la Métapièce est une **proposition de lecture mesurée**, pas une loi : calé sur deux numéros de TWIC, des Rois roqués et un mat dans les dix demi-coups, il reste à éprouver ailleurs. Une première formule, par pièce, a été essayée et **n'a pas résisté** : son script (`couple_moteur.py`) est publié par transparence.
Voir le dossier de recherche, section 4 (« ce qui est établi, ce qui ne l'est pas »).

## Licences
Le code est publié sous licence **GNU GPL v3** (voir `LICENSE`), parce qu'il utilise la bibliothèque `python-chess` (GPL-3.0+). Les textes (dossier de recherche, guides) sont publiés sous licence **Creative Commons BY 4.0** : réutilisation libre avec mention de l'auteur. Les coups des parties sont des faits ; les fichiers de parties sont fournis comme exemples.

## Remerciements et sources
`python-chess` (Niklas Fiekas) ; jeu de pièces « cburnett » (Colin M. L. Burnett), distribué avec `python-chess` ; revue **The Week in Chess** (parties non redistribuées) ; moteur **Stockfish** pour les mesures avec évaluation.

## Transparence sur l'aide de l'IA
Ce dépôt a été réalisé avec l'aide d'assistants d'intelligence artificielle (Claude, Anthropic ; Gemini, Google, pour la formalisation de l'idée du couple moteur), notamment pour écrire et vérifier le code et les mesures. Les idées, la conception, la thèse, la structure et les décisions sont celles de l'auteur.
