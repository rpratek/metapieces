#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batterie_dame_fou.py -- valeur statique (NNUE Stockfish) d'une batterie Dame + Fou visant h7, selon la fragilite de la cible, sur 120 structures aleatoires.
Diagonale b1-h7 : doublees = Fou d3 + Dame c2 (derriere) ; cote a cote = Fou d3 + Dame e2 ; dispersees = Dame d1 + Fou f1.
Cible h7 (pion noir) : defendue par 0 piece (Roi en f8) ; le Roi seul (g8) ; Roi + Tour h8 ; Roi + Tour + Cavalier f6.
Chaque cas est aussi evalue avec un obstacle sur la diagonale : pion noir f5 protege par e6.
Squelette : pions blancs sur a, b, f, g, h ; pions noirs de base f7 g7 h7, plus a7 b7 c7 tires au hasard.
Indicateurs : alignement = eval(doublees) - eval(cote a cote) ; activite = eval(cote a cote) - eval(dispersees) ; gain = eval(doublees) - eval(dispersees).
LIMITES : valeurs d'un reseau de neurones ; positions artificielles ; evaluation statique (pas de combinaison).
USAGE : python3 batterie_dame_fou.py <chemin_stockfish> <nb_structures>
"""
import sys, re, subprocess, random, statistics, chess
random.seed(77); sf=sys.argv[1]; N=int(sys.argv[2])
def squelette():
    bl=[f+str(random.choice([2,2,3,4])) for f in 'abfgh' if random.random()<0.85]
    nr=[f+str(random.choice([7,7,6,5])) for f in 'abc' if random.random()<0.85]
    return bl,nr
def poser(b,l,s):
    for c in l: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol(s))
CONF=[(['c2'],['d3']),(['e2'],['d3']),(['d1'],['f1'])]
DEF=[("h7 défendu par 0 pièce (Roi f8)",'f8',[],[]),("h7 défendu par le Roi (g8)",'g8',[],[]),
     ("h7 défendu par Roi + Tour h8",'g8',['h8'],[]),("h7 défendu par Roi + Tour + Cavalier f6",'g8',['h8'],['f6'])]
OBS=[("sans obstacle",[]),("obstacle f5 (protégé par e6)",['f5','e6'])]
def fabrique(bl,nr,conf,roi,tours,cav,obs):
    b=chess.Board(None); poser(b,['g1'],'K'); poser(b,bl,'P'); poser(b,conf[0],'Q'); poser(b,conf[1],'B')
    poser(b,[roi],'k'); poser(b,['f7','g7','h7'],'p'); poser(b,nr,'p'); poser(b,obs,'p'); poser(b,tours,'r'); poser(b,cav,'n'); b.turn=chess.WHITE; return b
def batch(fens):
    entree="uci\n"+''.join(f"position fen {f}\neval\nisready\n" for f in fens)+"quit\n"
    r=subprocess.run([sf],input=entree,capture_output=True,text=True,timeout=270)
    out=[]
    for bl in r.stdout.split("readyok")[:len(fens)]:
        m=re.search(r"Final evaluation\s+([+-]?\d+\.\d+)",bl) or re.search(r"NNUE evaluation\s+([+-]?\d+\.\d+)",bl)
        out.append(float(m.group(1)) if m else None)
    return out
fens=[]; idx=[]
for s in range(N):
    bl,nr=squelette()
    for di,(dn,roi,tours,cav) in enumerate(DEF):
        for oi,(on,obs) in enumerate(OBS):
            for ki,cf in enumerate(CONF):
                b=fabrique(bl,nr,cf,roi,tours,cav,obs)
                if b.is_valid() and not b.is_check() and len(b.pieces(chess.PAWN,chess.BLACK))<=8:
                    fens.append(b.fen()); idx.append((s,di,oi,ki))
ev=batch(fens); D={}
for (s,di,oi,ki),e in zip(idx,ev):
    if e is not None: D.setdefault((s,di,oi),{})[ki]=e
def st(v):
    return (statistics.mean(v),statistics.stdev(v)/len(v)**0.5,len(v)) if len(v)>2 else (float('nan'),float('nan'),len(v))
print(f"DAME + FOU visant h7 : {N} structures tirées ; {len(fens)} positions évaluées\n")
for oi,(on,obs) in enumerate(OBS):
    print(f"  {on}")
    print(f"    {'cible':46}{'alignement':>14}{'activité':>14}{'gain batterie':>16}   n")
    for di,(dn,roi,tours,cav) in enumerate(DEF):
        al=[];ac=[];ga=[]
        for s in range(N):
            d=D.get((s,di,oi))
            if d and len(d)==3: al.append(d[0]-d[1]); ac.append(d[1]-d[2]); ga.append(d[0]-d[2])
        a=st(al);c=st(ac);g=st(ga)
        print(f"    {dn:46}{a[0]:+8.2f} ±{a[1]:4.2f}{c[0]:+8.2f} ±{c[1]:4.2f}{g[0]:+10.2f} ±{g[1]:4.2f}  {a[2]}")
    print()
