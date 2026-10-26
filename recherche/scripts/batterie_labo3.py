#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batterie_labo3.py -- valeur statique d'une batterie de Tours selon la PROTECTION et la DISTANCE d'un obstacle sur la colonne d.
Meme dispositif que batterie_labo2.py (evaluation statique NNUE de Stockfish ; Tours doublees d1+d2, cote a cote d1+e1, dispersees a1+h1).
Pions blancs : a2 b2 f2 g2 h2 (aucun pion blanc n'attaque d3, d4...). Pions noirs de base : f7 g7 h7.
Obstacle = pion noir en dk (k = 3..6) ; soutiens possibles : pions noirs en c(k+1) et e(k+1).
Parties : (A) protection de l'obstacle d5 : 0, 1 (c6), 2 (c6 et e6) ; (B) distance, protection 2 : d3, d4, d5, d6.
Indicateurs : alignement = eval(doublees) - eval(cote a cote) ; activite = eval(cote a cote) - eval(dispersees) ; gain de la batterie = eval(doublees) - eval(dispersees).
LIMITES : valeurs d'un reseau de neurones ; positions artificielles ; differences faibles ; une seule famille de structures.
USAGE : python3 batterie_labo3.py <chemin_stockfish>
"""
import sys, re, subprocess, chess
def construire(rooks, sup=()):
    b=chess.Board(None)
    b.set_piece_at(chess.parse_square('g1'),chess.Piece.from_symbol('K'))
    for c in ['a2','b2','f2','g2','h2']: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('P'))
    for c in rooks: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('R'))
    b.set_piece_at(chess.parse_square('g8'),chess.Piece.from_symbol('k'))
    for c in ['f7','g7','h7']+list(sup): b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('p'))
    for c in ['a8','h8']: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('r'))
    b.turn=chess.WHITE; return b
def statique(sf,fen):
    r=subprocess.run([sf],input=f"uci\nposition fen {fen}\neval\nquit\n",capture_output=True,text=True,timeout=60)
    m=re.search(r"Final evaluation\s+([+-]?\d+\.\d+)",r.stdout) or re.search(r"NNUE evaluation\s+([+-]?\d+\.\d+)",r.stdout)
    return float(m.group(1)) if m else float('nan')
CONF=[['d1','d2'],['d1','e1'],['a1','h1']]
def ligne(sf,nom,sup):
    ev=[]
    for rk in CONF:
        b=construire(rk,sup)
        if not b.is_valid(): ev.append(float('nan')); continue
        ev.append(statique(sf,b.fen()))
    d,c,s=ev
    print(f"  {nom:46}{d:+9.2f}{c:+9.2f}{s:+9.2f}{d-c:+13.2f}{c-s:+10.2f}{d-s:+13.2f}")
sf=sys.argv[1]
ent=f"  {'':46}{'doublées':>9}{'côte':>9}{'dispers.':>9}{'alignement':>13}{'activité':>10}{'gain batterie':>13}"
print("(A) PROTECTION de l'obstacle d5"); print(ent)
ligne(sf,"aucun obstacle",())
ligne(sf,"d5 seul (0 soutien, prenable)",('d5',))
ligne(sf,"d5 + c6 (1 soutien)",('d5','c6'))
ligne(sf,"d5 + c6 + e6 (2 soutiens, imprenable)",('d5','c6','e6'))
print("\n(B) DISTANCE de l'obstacle imprenable (2 soutiens)"); print(ent)
ligne(sf,"d3 (collé à la Tour d2)",('d3','c4','e4'))
ligne(sf,"d4",('d4','c5','e5'))
ligne(sf,"d5",('d5','c6','e6'))
ligne(sf,"d6",('d6','c7','e7'))
