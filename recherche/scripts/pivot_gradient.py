#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pivot_gradient.py -- le "pivotement" des cases de l'echiquier, calcule sur echiquier vide.

Pour chaque case et chaque type de piece (Cavalier, Roi, Dame, Tour), on calcule :
  - la PORTEE : le nombre de cases qu'elle attaque d'un seul coup ;
  - le TEMPS DE BASCULE : le nombre moyen de coups qu'elle met pour atteindre une case d'aile
    (colonnes a, b, g, h), par parcours en largeur (plus court chemin) sur l'echiquier vide.
Les cases sont regroupees en quatre anneaux a partir du centre :
  coeur (d4 e4 d5 e5) / zone connexe (c3-f6) / anneau b2-g7 / peripherie (bord).

C'est un calcul exact et reproductible : il ne depend d'aucune base de parties.
LIMITE : echiquier vide (aucun obstacle). Le Fou n'est pas calcule (il est lie a sa couleur de cases).

USAGE :  python3 pivot_gradient.py
"""
import collections
import chess

NOMS = {0.5: "coeur (d4 e4 d5 e5)", 1.5: "zone connexe (c3-f6)", 2.5: "anneau b2-g7", 3.5: "peripherie (bord)"}
PIECES = (("Cavalier", chess.KNIGHT), ("Roi", chess.KING), ("Dame", chess.QUEEN), ("Tour", chess.ROOK))
AILES = [s for s in chess.SQUARES if chess.square_file(s) in (0, 1, 6, 7)]

def anneau(sq):
    """Distance au centre de l'echiquier (0.5 = coeur ... 3.5 = bord)."""
    return max(abs(chess.square_file(sq) - 3.5), abs(chess.square_rank(sq) - 3.5))

def attaques(typ, sq):
    b = chess.Board.empty(); b.set_piece_at(sq, chess.Piece(typ, True)); return list(b.attacks(sq))

def distances(typ, sq):
    """Plus courts chemins (en coups) depuis sq, echiquier vide."""
    d = {sq: 0}; file_ = collections.deque([sq])
    while file_:
        s = file_.popleft()
        for t in attaques(typ, s):
            if t not in d: d[t] = d[s] + 1; file_.append(t)
    return d

def calcule():
    res = {}
    for nom, typ in PIECES:
        temps, portee = collections.defaultdict(list), collections.defaultdict(list)
        for sq in chess.SQUARES:
            d = distances(typ, sq); xs = [d[s] for s in AILES if s != sq and s in d]
            temps[anneau(sq)].append(sum(xs) / len(xs)); portee[anneau(sq)].append(len(attaques(typ, sq)))
        res[nom] = ({k: sum(v) / len(v) for k, v in temps.items()}, {k: sum(v) / len(v) for k, v in portee.items()})
    return res

if __name__ == "__main__":
    res = calcule()
    print("TEMPS MOYEN (en coups) pour atteindre une case d'aile, selon l'anneau de depart\n")
    print(f"{'anneau':24} " + ' '.join(f"{n:>10}" for n in res))
    for k in sorted(NOMS): print(f"{NOMS[k]:24} " + ' '.join(f"{res[n][0][k]:10.2f}" for n in res))
    print("\nPORTEE MOYENNE (cases attaquees d'un coup)\n")
    for k in sorted(NOMS): print(f"{NOMS[k]:24} " + ' '.join(f"{res[n][1][k]:10.1f}" for n in res))
    print("\nEcart relatif du temps moyen par rapport au coeur :")
    for n in ('Cavalier', 'Roi'):
        c0 = res[n][0][0.5]
        print(f"  {n:9}", ' | '.join(f"{NOMS[k].split(' (')[0]} +{(res[n][0][k] / c0 - 1) * 100:.0f}%" for k in (1.5, 2.5, 3.5)))
