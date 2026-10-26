# Carlsen – Nakamura : le fil rouge du § 5.1

**Partie** : Magnus Carlsen – Hikaru Nakamura, Speed Chess Championship 2023 (le fichier ne précise ni la date ni la manche). **Résultat** selon le fichier : ½-½.

**La combinaison** (coups 40 à 44) : 40.Txc5+ bxc5 41.Tc7+ Rxc7 42.Dxc5+ Rb7 43.Dd5+ Rb8 44.Fe5+. Les Blancs sacrifient deux Tours, donnent échec à chaque coup, et la position finale ne contient pas de mat immédiat : le moteur voit un mat en 5 (44…Ta7 45.Fd4+ Rb8 46.Dd8+ Rb7 47.Dd7+ Ra6 48.Dc6+ Ra5 49.Fc3#).

## Le tableau du livre
| Coup | Fuites du Roi noir | Attaquants | Défenseurs | Moteur |
|---|---|---|---|---|
| Départ (avant 40.Txc5+) | 1 | 5 | 2 | mat en 11 |
| 40.Txc5+ | 0 | 5 | 2 | mat en 10 |
| 41.Tc7+ | 4 | 4 | 1 | mat en 9 |
| 42.Dxc5+ | 2 | 3 | 1 | mat en 8 |
| 43.Dd5+ | 6 | 1 | 3 | mat en 6 |
| 44.Fe5+ | 2 | 2 | 2 | mat en 5 |

## Ce que montre l'application sur cette partie
Ouvrez `Carlsen_Nakamura_territoire.html` (double-clic) et suivez les coups.
- **Coup 36…Df1** : les deux Métapièces ont le même flux, 50 contre 50.
- **Coup 37…Ta1** : la **menace** Df1–b1 mat naît à ce coup, la Tour a1 soutenant la case b1 ; avant, aucune menace de mat en un coup. Il y a ensuite **onze parades**, dont 38.Dc2 (ce n'est donc pas « le » coup forcé).
- **Avec les pions** (case à cocher) : après 37.fxe6, la Métapièce blanche est le Pentanôme Dc3, Td6, Tg5, Ff6, Pe6.
- **Coup 42.Dxc5+** : après la perte des deux Tours le territoire blanc s'était éclaté en plusieurs îlots ; il redevient d'un seul tenant (30 cases), et le Roi noir n'a plus que deux fuites libres, b7 et b8.
- **Position finale** : deux fuites restent, **a7 (case sombre)** et **c8 (case claire)** : il manque aux Blancs deux fermetures de nature différente, et la Dame, qui tient déjà b7 et a8, est surchargée.

## Reproduire le tableau et les diagrammes
Il faut Stockfish (le tableau a été calculé avec Stockfish 17.1) :
```
python3 carlsen.py chemin/vers/stockfish
```
Le script écrit les trois diagrammes et un fichier de résultats dans `resultats/` (environ une minute).

## Ce que cet exemple ne dit pas
Il ne juge ni les joueurs ni la partie : il montre ce que l'application calcule. Le flux n'est pas une évaluation, et une combinaison de blitz ne démontre pas une théorie.
