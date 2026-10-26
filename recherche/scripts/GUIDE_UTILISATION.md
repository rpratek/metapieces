# Détecteur de Métapièces — Guide d'utilisation

Ce script extrait automatiquement les Métapièces d'une archive de parties d'échecs (format PGN), en s'appuyant sur le catalogue actuel du livre. Vous pouvez l'utiliser seul, sans moi, pour constituer et enrichir votre propre archive au fil du temps.

## Installation (une seule fois)

Il vous faut Python 3 et la bibliothèque `python-chess` :

```
pip install python-chess
```

*(Sur certains systèmes Linux/Mac récents, il faudra ajouter `--break-system-packages` à la fin de cette commande.)*

## Où récupérer les archives

The Week in Chess (TWIC) publie une archive hebdomadaire de parties de haut niveau, gratuitement :
**https://theweekinchess.com/twic**

Chaque semaine propose un fichier `.pgn` (parfois zippé). Pour une archive personnelle solide sans y passer vos soirées, un rythme **mensuel** (télécharger 4-5 semaines d'un coup) ou **annuel** (un cumul en fin d'année) suffit largement — scanner chaque semaine individuellement n'apporte rien de plus qu'un cumul périodique, puisque les parties ne changent pas rétroactivement.

## Utilisation de base

```bash
python3 detecteur_metapieces.py monfichier.pgn --out resultats.csv
```

Le script affiche un résumé à l'écran (combien de parties par catégorie) et écrit le détail dans le fichier CSV indiqué — une ligne par partie trouvée, avec les deux joueurs, leurs Elo, l'événement, la date, le résultat, et la position FEN finale.

## Options utiles

**Limiter pour un test rapide** (utile sur un très gros fichier, pour voir si tout fonctionne avant de lancer le scan complet) :
```bash
python3 detecteur_metapieces.py monfichier.pgn --out test.csv --max 1000
```

**Ne garder qu'une seule catégorie** (par exemple si vous cherchez spécifiquement des T4, qui sont rares) :
```bash
python3 detecteur_metapieces.py monfichier.pgn --out t4_seuls.csv --categorie T4
```

## Vérifier un mat en détail

Une fois que vous avez une FEN intéressante dans votre CSV, vous pouvez voir précisément quelle pièce couvre quelle case — utile pour repérer si une pièce est vraiment nécessaire au mat ou seulement redondante (comme on l'a vu avec le pion qui ne faisait rien dans l'exemple "Duo de Fous") :

```bash
python3 -c "from detecteur_metapieces import detail_case; detail_case('VOTRE_FEN_ICI')"
```

## Les catégories reconnues

| Code | Pièces | Code | Pièces |
|---|---|---|---|
| B1 | Fou + Cavalier | T1 | Dame + Fou + Cavalier |
| B2 | Dame + Fou | T2 | Dame + Tour + Fou |
| B3 | Dame + Tour | T3 | 2 Cavaliers + Pion |
| B4 | Tour + Tour | T4 | Roi + Cavalier + Fou |
| B5 | Fou + Fou | T6 | Dame + Tour + Cavalier |
| B6 | Cavalier + Pion | T7 | Dame + Fou + Fou |
| B7 | Pion + Roi | T8 | Dame + Tour + Pion |
| B8 | Tour + Fou (mat de Mayet) | | |
| B9 | Dame + Cavalier | | |
| B10 | Tour + Cavalier | | |

*(B8 = Tour + Fou. Toutes les paires Tour + Fou ne sont pas des mats de Mayet : pour le test strict, `from detecteur_metapieces import est_mayet`.)*

Au-delà de 3 pièces contributrices, le script indique `Quadrinome?` ou `Pentanome?` — ce sont des **candidats**, pas des catégories officiellement validées : à vérifier à la main avant de les retenir.

## Limites honnêtes à garder en tête

- **B7** (Pion+Roi) et un motif comme les **pions liés** sont des configurations *structurelles*, pas des motifs de mat — ce script, qui ne regarde que les positions de mat, ne peut pas les trouver par construction. Ce n'est pas une absence du jeu réel, juste une limite de la méthode.
- **B2, B5, B6, T3** ressortent très rarement, voire jamais, même sur de grands échantillons. Dans la pratique, une pièce supplémentaire incidente (souvent un pion) vient presque toujours s'ajouter au duo/trio théorique, faisant basculer le classement vers une catégorie à cardinalité supérieure. C'est exactement ce qui s'est passé avec votre partie « Duo de Fous », reclassée en T7 après vérification — la Dame y jouait un rôle silencieux mais réel.
- Le classement repose sur la **position finale uniquement** — il ne juge pas si la partie qui y mène est belle, intéressante ou pédagogique. Le tri humain reste nécessaire après l'extraction automatique.

## Exemple de session complète

```bash
# 1. Récupérer quelques semaines de TWIC, les assembler dans un seul fichier si besoin
cat twic1700.pgn twic1701.pgn twic1702.pgn > mon_archive_mensuelle.pgn

# 2. Lancer le scan complet
python3 detecteur_metapieces.py mon_archive_mensuelle.pgn --out resultats_mensuels.csv

# 3. Ouvrir resultats_mensuels.csv dans Excel ou un tableur, trier par catégorie,
#    repérer les joueurs connus ou les Elo élevés pour prioriser l'examen

# 4. Pour une FEN qui vous intéresse, vérifier le détail avant de la retenir
python3 -c "from detecteur_metapieces import detail_case; detail_case('la_fen_trouvee_dans_le_csv')"
```


## Statistiques par période (nouveau)

```bash
python3 stats_metapieces.py twic1700.pgn twic1701.pgn twic1702.pgn --out stats_mensuelles.csv
python3 stats_metapieces.py twic*.pgn --par annee --out stats_annuelles.csv
```

Le script classe chaque partie selon la **date inscrite dans la partie** (pas la date du fichier), exclut les doublons
(deux parties aux coups identiques comptent pour une) et écrit, par période : nombre de parties, de mats, de mats classés,
le détail par catégorie, et le taux **pour 1000 parties**.

À savoir : (1) ces chiffres mesurent les Métapièces **visibles dans un mat final**, pas leur fréquence réelle dans le jeu ;
(2) un fichier hebdomadaire (≈ 6 000 parties) ne donne que 0 à 3 occurrences pour les catégories rares (B1, T4, B4) :
visez le mois ou l'année ; (3) comparez les taux entre périodes plutôt que les effectifs bruts.


## Correctif important (octobre 2026)

Une version antérieure du détecteur confondait certaines catégories : le catalogue était indexé par des ensembles, qui
**suppriment les doublons**. Résultat : « Dame + Fou » était étiqueté T7, « Tour + Tour » et « Fou + Fou » étaient comptés
comme des mats d'une seule pièce, et B6/T3 se confondaient. **Corrigé** : les catégories sont désormais indexées par la liste
triée des pièces (les doublons comptent). Si vous avez des résultats produits avant ce correctif, relancez-les.
