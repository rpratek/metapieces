#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batterie_labo2.py -- valeur STATIQUE d'une batterie de Tours, avec et sans obstacle sur la colonne d (positions de laboratoire).
Evaluation statique du reseau NNUE de Stockfish (commande 'eval'), sans recherche : isole la valeur de la configuration, sans combinaison.
Configurations des Tours blanches : doublees (d1,d2) ; cote a cote (d1,e1) ; dispersees (a1,h1).
Obstacles : aucun ; pion noir d5 non protege ; pion d5 protege par c6 et e6 (imprenable) ; pion d5 imprenable + Cavalier d6 (protege par c7 et e7).
Les pions de soutien sont presents dans les trois configurations de Tours : les differences annulent leur materiel.
Valeur de l'alignement = eval(doublees) - eval(cote a cote) ; valeur de l'activite = eval(cote a cote) - eval(dispersees).
LIMITES : valeurs d'un reseau de neurones, pas verite ; positions artificielles ; une famille de structures ; le moteur n'est pas neutre (il a deja « appris » ce qui gagne).
USAGE : python3 batterie_labo2.py <chemin_stockfish>
"""
import sys, re, subprocess, chess
def construire(rooks, noirs_sup=(), noir_cavalier=None):
    b=chess.Board(None)
    for c in ['g1']: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('K'))
    for c in ['a2','b2','c2','f2','g2','h2']: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('P'))
    for c in rooks: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('R'))
    b.set_piece_at(chess.parse_square('g8'),chess.Piece.from_symbol('k'))
    for c in ['c7','f7','g7','h7']+list(noirs_sup): b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('p'))
    for c in ['a8','h8']: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol('r'))
    if noir_cavalier: b.set_piece_at(chess.parse_square(noir_cavalier),chess.Piece.from_symbol('n'))
    b.turn=chess.WHITE; return b
def statique(sf,fen):
    r=subprocess.run([sf],input=f"uci\nposition fen {fen}\neval\nquit\n",capture_output=True,text=True,timeout=60)
    m=re.search(r"Final evaluation\s+([+-]?\d+\.\d+)",r.stdout)
    if not m: m=re.search(r"NNUE evaluation\s+([+-]?\d+\.\d+)",r.stdout)
    return float(m.group(1)) if m else None
CAS=[("aucun obstacle",(),None),
     ("pion noir d5 non protégé (prenable)",('d5',),None),
     ("pion noir d5 protégé par c6 et e6 (imprenable)",('d5','c6','e6'),None),
     ("pion d5 imprenable + Cavalier noir d6 (soutenu par c7, e7)",('d5','c6','e6','e7'),'d6')]
CONF=[("doublées d1+d2",['d1','d2']),("côte à côte d1+e1",['d1','e1']),("dispersées a1+h1",['a1','h1'])]
sf=sys.argv[1]
print(f"{'obstacles sur la colonne d':60}"+''.join(f"{n:>20}" for n,_ in CONF)+f"{'alignement':>13}{'activité':>11}")
for nom,sup,cav in CAS:
    ev=[]; 
    for cn,rk in CONF:
        b=construire(rk,sup,cav)
        if not b.is_valid(): print("  position invalide :",nom,cn,b.status()); ev.append(float('nan')); continue
        ev.append(statique(sf,b.fen()))
    d,c,s=ev
    print(f"{nom:60}"+''.join(f"{e:+20.2f}" for e in ev)+f"{d-c:+13.2f}{c-s:+11.2f}")
