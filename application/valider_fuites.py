#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE : python3 valider_fuites.py partie.pgn   (a lancer dans le dossier de metapiece_territoire.py)
# Validation : les fuites « libres » doivent etre exactement les coups legaux du Roi adverse vers une case voisine (hors roque)
import sys, random, io, chess, chess.pgn
sys.path.insert(0,'.'); import metapiece_territoire as T
def ecarts(board):
    n=0; tot=0; ex=[]
    for couleur in (chess.WHITE,chess.BLACK):
        ennemi=not couleur; K=board.king(ennemi)
        if K is None: continue
        a=T.analyser(board,couleur); libres=set(a['fuites']['libres'])
        b=board.copy(); b.turn=ennemi
        legaux={chess.square_name(m.to_square) for m in b.legal_moves if m.from_square==K and chess.square_distance(m.from_square,m.to_square)==1}
        tot+=1
        if libres!=legaux: n+=1; ex.append((board.fen(),'B' if couleur else 'N',sorted(libres),sorted(legaux)))
    return n,tot,ex
n=t=0; exs=[]
g=chess.pgn.read_game(open(sys.argv[1] if len(sys.argv)>1 else 'carlsen-nakamura-2023.pgn')); b=g.board()
for m in g.mainline_moves():
    b.push(m); x,y,e=ecarts(b); n+=x; t+=y; exs+=e
print(f"partie fournie : {n} désaccords sur {t} contrôles")
random.seed(5); n2=t2=0; ex2=[]
for _ in range(60):
    b=chess.Board()
    for _ in range(random.randint(20,140)):
        if b.is_game_over(): break
        b.push(random.choice(list(b.legal_moves))); x,y,e=ecarts(b); n2+=x; t2+=y; ex2+=e
print(f"60 parties aléatoires : {n2} désaccords sur {t2} contrôles")
for f in (exs+ex2)[:3]: print("  exemple :",f)
