#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tour_horizontal.py -- les coups de Tour horizontaux (le long de la rangee) font-ils plus croitre le flux que les coups verticaux (le long de la colonne) ?
Flux pondere d'une piece (C, F, T, D) = somme des poids (coeur 4, zone pivot 3, couronne 2, bord 1) des cases attaquees non occupees par son camp.
Pour chaque coup de Tour entre les demi-coups 10 et 60 : variation du flux de la Tour (arrivee - depart), des autres pieces, et total.
On separe : coup horizontal / vertical ; Tour alignee avec une autre Tour ou la Dame (batterie) avant le coup, ou non.
LIMITES : flux = mobilite brute ; correlation ; l'interpretation en « dimensions » est une lecture, non une demonstration.
USAGE : python3 tour_horizontal.py
"""
import re, io, random, chess, chess.pgn, collections, statistics, time
import numpy as np
def poids(s):
    f,r=s%8,s//8
    if f in (3,4) and r in (3,4): return 4
    if 2<=f<=5 and 2<=r<=5: return 3
    if 1<=f<=6 and 1<=r<=6: return 2
    return 1
W=[poids(s) for s in range(64)]
PIECES=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def flux(b,col):
    own=b.occupied_co[col]; r={}
    for s,p in b.piece_map().items():
        if p.color==col and p.piece_type in PIECES: r[s]=sum(W[q] for q in chess.scan_forward(b.attacks_mask(s)&~own))
    return r
def en_batterie(b,col,s):
    for t,p in b.piece_map().items():
        if t!=s and p.color==col and p.piece_type in (chess.ROOK,chess.QUEEN):
            if (t%8==s%8 or t//8==s//8) and not (b.occupied & chess.between(s,t)): return True
    return False
blocs=[]; vus=set()
def fichiers_pgn(defaut=('twic1637.pgn','twic1662.pgn')):
    """Fichiers PGN à analyser : ceux donnés en arguments (jokers acceptés, par exemple parties*.pgn),
    sinon les deux numéros TWIC par défaut, placés dans le dossier courant."""
    import sys, glob
    demandes=[a for a in sys.argv[1:] if a.lower().endswith('.pgn') or ('*' in a and '.pgn' in a.lower())]
    liste=[]
    for a in demandes: liste+=sorted(glob.glob(a)) or [a]
    return liste or list(defaut)

for fn in fichiers_pgn():
    c=open(fn,encoding='utf-8',errors='ignore').read()
    for bloc in re.split(r'\n\n(?=\[Event)',c):
        cle=re.sub(r'\s+',' ',bloc.split('\n\n',1)[-1])
        if cle in vus: continue
        vus.add(cle); blocs.append(bloc)
R=collections.defaultdict(list); t0=time.time(); ng=0
for bloc in blocs:
    if time.time()-t0>200: break
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<30: continue
    ng+=1
    for i,m in enumerate(mv[:60]):
        col=b.turn
        if i>=10 and b.piece_type_at(m.from_square)==chess.ROOK and not b.is_capture(m) and not b.is_castling(m):
            horiz=(m.from_square//8==m.to_square//8); bat=en_batterie(b,col,m.from_square)
            F0=flux(b,col); b.push(m); F1=flux(b,col)
            dm=F1.get(m.to_square,0)-F0.get(m.from_square,0)
            do=sum(v for s,v in F1.items() if s!=m.to_square)-sum(v for s,v in F0.items() if s!=m.from_square)
            R[('horizontal' if horiz else 'vertical','en batterie' if bat else 'seule')].append((dm,do,dm+do))
        else: b.push(m)
print(f"{ng} parties, {time.time()-t0:.0f} s\n")
print(f"{'coup de Tour':14}{'Tour avant le coup':20}{'coups':>8}{'flux de la Tour':>17}{'flux des autres':>17}{'flux total':>12}")
for d in ('horizontal','vertical'):
    for e in ('en batterie','seule'):
        v=np.array(R[(d,e)])
        if len(v)>30: print(f"{d:14}{e:20}{len(v):8}{v[:,0].mean():+13.2f} ±{v[:,0].std()/len(v)**0.5:3.2f}{v[:,1].mean():+13.2f}{v[:,2].mean():+12.2f}")
for e in ('en batterie','seule'):
    h=np.array(R[('horizontal',e)]); v=np.array(R[('vertical',e)])
    if len(h)>30 and len(v)>30:
        d=h[:,2].mean()-v[:,2].mean(); se=np.sqrt(h[:,2].var()/len(h)+v[:,2].var()/len(v)); print(f"\n{e}: flux total horizontal - vertical = {d:+.2f} (erreur type {se:.2f}, t = {d/se:+.1f})")
