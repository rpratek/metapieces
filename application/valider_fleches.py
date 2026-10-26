#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE : python3 valider_fleches.py partie.pgn   (a lancer dans le dossier de metapiece_territoire.py)
# Controle : pour chaque case et chaque demi-coup, la variation du nombre de pieces d'un camp qui la controlent doit etre
# exactement la somme des gains moins la somme des pertes des fleches de ce camp.
import sys, random, collections, chess, chess.pgn
sys.path.insert(0,'.'); import metapiece_territoire as T
def verifie(prev,cur,coup):
    mauvais=0; tot=0
    for col in (chess.WHITE,chess.BLACK):
        A0=T.attaques_pieces(prev,col); A1=T.attaques_pieces(cur,col)
        c0=collections.Counter(t for _,a in A0.values() for t in a); c1=collections.Counter(t for _,a in A1.values() for t in a)
        fl,pg,pp=T.fleches_coup(prev,cur,coup,col,complet=True)
        g=collections.Counter(); l=collections.Counter()
        for e in fl:
            for t in e['g']: g[t]+=1
            for t in e['l']: l[t]+=1
        for sq in chess.SQUARES:
            tot+=1
            if c1[sq]-c0[sq]!=g[sq]-l[sq]: mauvais+=1
    return mauvais,tot
n=t=0
g=chess.pgn.read_game(open(sys.argv[1] if len(sys.argv)>1 else 'carlsen-nakamura-2023.pgn')); b=g.board()
for m in g.mainline_moves():
    prec=b.copy(); b.push(m); x,y=verifie(prec,b,m); n+=x; t+=y
print(f"partie fournie : {n} désaccords sur {t} contrôles de cases")
random.seed(11); n2=t2=0
for _ in range(60):
    b=chess.Board()
    for _ in range(random.randint(20,150)):
        if b.is_game_over(): break
        m=random.choice(list(b.legal_moves)); prec=b.copy(); b.push(m); x,y=verifie(prec,b,m); n2+=x; t2+=y
print(f"60 parties aléatoires : {n2} désaccords sur {t2} contrôles de cases")
