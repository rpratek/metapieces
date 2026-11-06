# Partie commentée de la section 8.5 — mesures reproductibles

*Dossier d'exemple, comme `carlsen_nakamura/` et `fontaine_mvl/` : la partie (PGN), les deux scripts qui la mesurent, et ce guide. Voir la section 8.5 du livre.*

Partie : Vachier-Lagrave – Nepomniachtchi, Julius Baer Generation Cup 2024 (Division I, perdants), ronde 1.1, chess.com, 28 septembre 2024, partie rapide (10 minutes + 2 secondes par coup).

Pour reproduire ces mesures :

    python3 analyse_partie_metapieces.py vachier_lagrave_nepomniachtchi_2024.pgn --profondeur 22 --sortie resultat
    python3 variantes_partie_8_5.py vachier_lagrave_nepomniachtchi_2024.pgn --profondeur 22

Stockfish, un seul fil, profondeur 22, mémoire du moteur vidée avant chaque analyse (python-chess, Stockfish 16). Dans cette séquence tactique, les valeurs varient encore d'environ un pion d'une recherche à l'autre : seuls les ordres de grandeur et le sens du mouvement sont fiables. Un résultat sans sa profondeur n'est pas une mesure.

---


Julius Baer Generation Cup 2024, Division I, Losers · 2024.09.28 · résultat annoncé 1-0 · 65 coups · moteur Stockfish, un seul fil, profondeur 22.

## Événements repérés

- coup 23. Rfb1 : Tours doublées Blancs b1-b5
- coup 23... Re6 : Tour levée sur la 3e/6e rangée
- coup 25. Rbb5 : Tours doublées Blancs a5-b5
- coup 27. Rba5 : Tours doublées Blancs a5-a6

## Unités qui visent le Roi adverse (définition de la section 10.5 : neuf cases)

| coup | unités du camp qui vient de jouer |
|---|---|
| 20... Rfe8 | 1 |
| 21. Qd3 | 1 |
| 21... Bf8 | 1 |
| 22. Kg2 | 1 |
| 22... Rad8 | 1 |
| 23. Rfb1 | 1 |
| 23... Re6 | 1 |
| 24. Ra5 | 1 |
| 24... Rd7 | 1 |
| 25. Rbb5 | 1 |
| 25... Qd8 | 0 |
| 26. Ra6 | 1 |
| 26... Qc8 | 0 |
| 27. Rba5 | 1 |
| 27... Nc4 | 0 |
| 28. Rxe6 | 1 |
| 28... Nxa5 | 0 |
| 29. Ng5 | 2 |
| 29... Rd6 | 0 |
| 30. Qg3 | 2 |
| 30... Qd8 | 0 |
| 31. Re8 | 3 |
| 31... Qxe8 | 0 |
| 32. Qh4 | 3 |
| 32... Qe4+ | 1 |
| 33. Kg3 | 3 |

## Seuil A ≥ 3 (Livre III, § 6.3 du livre)

- Roi noir : première fois à A ≥ 3 : coup 28 ; maximum 4 (Roi roqué seulement).
- Roi blanc : première fois à A ≥ 3 : jamais ; maximum 2 (Roi roqué seulement).

## Plus fortes bascules d'évaluation (Cahier n° 17)

- après 31... Qxe8 : +3.38 → +99.94
- après 33. Kg3 : +3.41 → +99.95
- après 32... Qe4+ : +99.94 → +3.41
- après 29... Rd6 : +3.68 → +5.41
- après 27... Nc4 : +1.21 → +2.82

## Réserve de défenses (positions décidées, camp au trait = défenseur)

| coup | au trait | coups légaux | coups qui évitent le mat forcé | meilleure défense (éval., point de vue du défenseur) |
|---|---|---|---|---|
| 28... | Noirs | 34 | 33 | Nxa5 (-3.3) |
| 29... | Noirs | 30 | 26 | f6 (-3.8) |
| 30... | Noirs | 29 | 4 | Qd8 (-4.5) |
| 31... | Noirs | 24 | 6 | Qe7 (-6.8) |
| 32... | Noirs | 30 | 0 | Qe4+ (-100.0) |
| 33... | Noirs | 32 | 0 | Qd3+ (-100.0) |

Point de non-retour (au plus 20 % des coups légaux évitent le mat ET meilleure défense à − 3 pions ou moins, soit environ la Dame) : coup 30.
