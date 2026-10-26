# Métapièce et Territoire — la salle de bal

Une page HTML5 interactive, tirée d'un fichier PGN par un programme Python 3.

## Ce que l'application montre
Pour chaque demi-coup de la partie, et pour le camp choisi (Blancs, Noirs, ou les deux à la fois) :
- **le territoire de chaque pièce** (Cavalier, Fou, Tour, Dame) : les cases qu'elle attaque ou protège ;
- **la Métapièce en cours de création** : les pièces dont les territoires convergent (au moins une case attaquée par deux d'entre elles). Si aucune ne converge, la pièce la plus active est affichée comme un Monôme. La taille est nommée : Binôme, Trinôme, Quadrinôme, Pentanôme ;
- **les cases de fuite du Roi adverse** : libres (aucune pièce du camp ne les attaque : ce sont les « zones d'ombre »), fermées (attaquées), ou occupées par ses propres pièces ;
- **ce que fait le coup** : les cases qui viennent de s'éclairer (contour vert, « + ») et celles qui viennent de s'éteindre (pointillé rouge, « − »), par ce coup ou parce qu'une pièce adverse a coupé le rayon (case à cocher) ;
- **les flèches du coup** (idée d'origine de l'auteur, dès les premières versions de ChessBase) : à chaque demi-coup, une flèche pleine verte de chaque pièce vers les cases qu'elle vient de **gagner** (la case la plus éloignée de chaque ligne ouverte), et une flèche en tirets rouges vers celles qu'elle vient de **perdre**, partant de son ancienne case ; un ✕ marque une pièce prise. Le solde pondéré est écrit : au coup 1.e4, +22 gagné, −6 perdu, solde +16 (Fou f1 vers a6, Dame d1 vers h5, pion e4 vers d5 et f5). Se choisit avec « Ce que fait le coup » (rien, cases, flèches).
- **la continuité du territoire** : une seule zone éclairée d'un seul tenant, ou plusieurs zones séparées (avec la taille de la plus grande) ;
- **le flux** : la somme des poids des cases du territoire (4 cœur, 3 zone c3-f6, 2 couronne, 1 bord), en courbe sur toute la partie.

Deux affichages :
- **Salle de bal** (par défaut) : chaque pièce de la Métapièce est un lustre. Les cases qu'elle contrôle sont éclairées, les lumières s'additionnent (or pour les Blancs, bleu pour les Noirs), les cases où plusieurs lustres convergent ont un cadre lumineux et un chiffre, les fuites libres du Roi sont des zones d'ombre cerclées de rose.
- **Analyse** : une couleur par type de pièce.

## Installation et utilisation
1. Python 3.8 ou plus récent, puis, une seule fois : `pip install chess`
2. `python3 metapiece_territoire.py partie.pgn`  → crée `partie_territoire.html`
3. Double-cliquer sur le fichier HTML : il s'ouvre dans le navigateur, sans serveur ni connexion.

Options : `-o sortie.html` pour choisir le nom ; `--partie N` pour prendre la N-ième partie d'un fichier qui en contient plusieurs.

## Commandes de la page
Boutons début / précédent / lecture automatique / suivant / fin, curseur, flèches du clavier ← →, clic sur un coup de la liste, clic sur la courbe du flux. La case « Ne parcourir que les coups du camp choisi » fait sauter les coups de l'autre camp.

## Lien avec les principes du livre (D — Le Territoire)
| Principe | Ce que l'on voit |
|---|---|
| 26. Une Métapièce ne prend sa valeur que dans un territoire (lignes d'action qui convergent) | les cases cerclées d'un chiffre : plusieurs pièces y convergent |
| 27. Une pièce hors de tout territoire est une particule sans masse | les pièces qui n'appartiennent pas à la Métapièce n'éclairent rien |
| 32. Une pièce seule éclaire un secteur, une Métapièce éclaire un territoire | un Monôme éclaire peu de cases ; un Trinôme ou un Quadrinôme illumine une zone continue |
| 33-35. Le territoire continu, la liberté redistribuée, les cases fermées au Roi adverse | les fuites : zones d'ombre libres, croix sur les fuites fermées |

## Contrôle de qualité
`python3 valider_fuites.py partie.pgn` compare, à chaque demi-coup, les cases de fuite libres calculées par l'application aux coups légaux du Roi adverse. Résultat sur la partie fournie et sur 60 parties aléatoires : 0 désaccord sur 8 580 contrôles. Le calcul retire le Roi adverse de l'échiquier pour les attaques : une pièce qui lui donne échec contrôle aussi la case située derrière lui sur la même ligne (le Roi ne peut pas fuir en restant sur la ligne de l'échec).

`python3 valider_fleches.py partie.pgn` vérifie, pour chaque case et chaque demi-coup, que la variation du nombre de pièces qui la contrôlent est exactement la somme des gains moins la somme des pertes des flèches. Résultat : 0 désaccord sur 625 000 contrôles de cases (la partie fournie et 60 parties aléatoires).

## Les pions
La case **Avec les pions** (dans « Affichage ») élargit la Métapièce aux pions avancés. Sur la partie fournie, au coup 37...Ta1, elle retrouve le Pentanôme Dc3, Td6, Tg5, Ff6, Pe6 (flux 62 au lieu de 60) ; elle ne change la Métapièce que dans 16 demi-coups sur 88. Sans cette règle, tous les pions qui convergent avec une pièce entreraient dans la Métapièce (8 pièces au même coup). Les fuites ne changent jamais.

## Limites
Définition opérationnelle de la Métapièce (convergence des territoires) ; par défaut les pions ne forment pas de territoire ; la case « Avec les pions » y ajoute les **pions avancés** (au-delà de la 4e rangée pour les Blancs, symétriquement pour les Noirs), règle modifiable dans la fonction `avance` ; les clouages et les échecs sont ignorés pour les cases de fuite ; le flux n'est pas une évaluation de la position. C'est un outil de lecture, qui montre un lien, il ne le démontre pas.

Testé avec python-chess 1.11.2 et un navigateur récent (Chromium). Exemples : voir le dossier `../exemples/` (Carlsen – Nakamura et Fontaine – Vachier-Lagrave).
