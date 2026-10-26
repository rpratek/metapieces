# Index des mesures

Pour chaque mesure du livre : le script qui la produit, ce qu'elle dit, et son niveau de confiance **proposé** (Établi / Mesuré / Observation : voir le README). *Ces niveaux sont proposés par l'auteur et son assistant et restent à valider ; un résultat négatif est publié au même titre qu'un résultat positif.*

| Mesure | Script(s) | Ce qu'elle dit | Niveau proposé |
|---|---|---|---|
| Couple Moteur de la Métapièce | `couple_moteur_v2.py`, `couple_moteur_v2_croise.py`, `couple_moteur_exemple.py` | Sur 297 709 positions de roque, la formule distingue les positions qui finissent par un mat dans les dix coups de celles qui n'en finissent pas : 0,875 sur des parties non vues ; 0,884 et 0,864 d'un numéro de TWIC à l'autre (contre 0,833 pour un simple solde de pièces et de pions) | Établi |
| Convergence à nombre de pièces égal | `metapiece_vs_isolees.py` | Deux pièces qui convergent mettent un Roi roqué en danger de mat 2,6 fois plus souvent que deux pièces isolées (2,07 % contre 0,79 % ; fourchette 2,2 à 3,0) | Mesuré |
| Mats qui exigent une Métapièce | `mat_necessaire.py` | Dans 82 % des mats, au moins deux pièces sont nécessaires (Binôme 56,6 %, Trinôme 20,9 %, Monôme 17,9 %) | Mesuré |
| Grille attaque et défense | `seuil_roque_v2.py` | Le danger de mat va de 0,09 % à 9,81 % selon le rapport entre l'attaque et la défense | Mesuré |
| Dimensionnement à la résistance | `resistance_coalition.py` | Plus la défense est nombreuse, plus la coalition qui mate est grande (corrélation +0,26) | Mesuré, à confirmer |
| Nombre de Métapièces construites | `combien_metapieces.py` | 61 % des parties comptent au moins une Métapièce ; médiane : 1 pour le camp qui mate, 0 pour l'autre | Mesuré |
| Qui donne le mat | `estocade_executants.py` | La Dame (58,7 %) et la Tour (28,9 %) donnent le mat ; dans les Binômes, Dame + Tour est la paire la plus fréquente (22,4 %) | Mesuré |
| La trajectoire n'ajoute rien | `strategie_trajectoire.py` | Connaître la trajectoire de la partie n'améliore pas la prévision faite sur la configuration (résultat négatif) | Mesuré |
| Synergie de paires | `synergie_paires.py` | Le chevauchement des territoires de deux pièces n'a aucun effet mesurable (résultat négatif) | Mesuré |
| Connexité du groupe attaquant | `mat_connexe.py` | Mesure le plus grand groupe de pièces attaquantes reliées au moment du mat | Mesuré |
| Formules du Couple Moteur par pièce | `couple_moteur.py`, `audit_epreuve.py` | Essai négatif : la valeur sur le papier (corrélation +0,35) fait mieux que les formules par pièce (valeur × mobilité +0,30 ; puissance × adhérence +0,17) | Mesuré (échec publié) |

Les scripts se lancent depuis le dossier `donnees/` (voir `donnees/LISEZMOI.md`), sauf `couple_moteur_exemple.py`, qui n'a besoin d'aucune donnée.


## Comment lancer chaque script
**Règle générale** : `python3 nom_du_script.py mes_parties.pgn` (un ou plusieurs fichiers, jokers permis). Sans argument, le script lit `twic1637.pgn` et `twic1662.pgn` dans le dossier courant. **36 scripts** se lancent ainsi, sans moteur d'échecs. Un test de fumée sur 150 parties a été fait le 26 octobre 2026.

**Cas particuliers** (ils affichent leur mode d'emploi en tête du fichier) :

| Script | Commande | Prérequis |
|---|---|---|
| `batterie_labo2.py`, `batterie_labo3.py` | `... <chemin_stockfish>` | Stockfish ; pas de fichier PGN |
| `batterie_dame_fou.py`, `batteries_aleatoires.py` | `... <chemin_stockfish> <nb_structures>` | Stockfish ; pas de fichier PGN |
| `binome_formation.py`, `flux_vs_moteur.py`, `syn_reelle.py` | `... <chemin_stockfish> <secondes> [fichiers.pgn]` | Stockfish |
| `erreurs_config.py` | `... <configuration> <secondes> [nombre_max] [fichiers.pgn]` | Stockfish, dossier `donnees/` |
| `erreurs_fenetre_4_19.py`, `erreurs_fenetre_20_32.py`, `regle_controle_eval.py` | `... <secondes> [fichiers.pgn]` | Stockfish (chemin par défaut `/usr/games/stockfish`, modifiable par la variable d'environnement `STOCKFISH`) |
| `abandons_metapieces.py` | `... fichiers.pgn --moteur CHEMIN` | Stockfish |
| `audit_epreuve.py`, `couple_moteur.py`, `synergie_paires.py` | `PGN=mes_parties.pgn python3 ... <chemin_stockfish> ...` | Stockfish |
| `inertie.py` | `... <secondes> <nombre_de_parties> [fichiers.pgn]` | selon le script |
| `famille_mat2.py` | `... <secondes>` | pas de fichier PGN |
| `couple_moteur_v2_croise.py` | après `couple_moteur_v2.py` | lit `couple_v2_donnees.npy`, produit par `couple_moteur_v2.py` |
| `etouffe_composition.py` | `... fichiers.pgn` | suffisamment de parties (sur un très petit fichier, une division par zéro est normale) |

Pour installer Stockfish : https://stockfishchess.org (le programme est libre).
