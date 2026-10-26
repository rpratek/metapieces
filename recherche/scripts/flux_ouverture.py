#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flux_ouverture.py -- « puissance du flux acquis » par un coup d'ouverture.
Flux d'une piece (Cavalier, Fou, Tour, Dame) = nombre de cases qu'elle attaque et qui ne sont pas occupees par une piece de son camp.
Pour chaque coup des 10 premiers coups de chaque camp, on mesure :
  - dF_piece  : flux de la piece jouee sur sa case d'arrivee - flux sur sa case de depart ;
  - dF_autres : variation du flux des AUTRES pieces du camp (pieces « liberees » ou gênées par le coup) ;
  - dF_total  : somme des deux.
LIMITES : le flux est une mobilite brute (pas de valeur des cases attaquees) ; description, pas une preuve.
USAGE : python3 flux_ouverture.py
"""
import re, io, random, chess, chess.pgn, collections, statistics
random.seed(3)
def pc(x): return bin(x).count('1')
def flux_pieces(b,col):
    own=b.occupied_co[col]; res={}
    for s,p in b.piece_map().items():
        if p.color==col and p.piece_type in (chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN):
            res[s]=pc(b.attacks_mask(s)&~own)
    return res
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
NOM={chess.PAWN:'Pion',chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame',chess.KING:'Roi (dont roque)'}
agr=collections.defaultdict(list); ng=0
for bloc in blocs:
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<20: continue
    ng+=1
    for i,m in enumerate(mv[:20]):
        col=b.turn; t=b.piece_type_at(m.from_square); cap=b.is_capture(m)
        F0=flux_pieces(b,col); b.push(m); F1=flux_pieces(b,col)
        tot0=sum(F0.values()); tot1=sum(F1.values())
        if t in (chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN):
            dm=F1.get(m.to_square,0)-F0.get(m.from_square,0)
        else: dm=0
        # catégorie : pions centraux (d,e) / de flanc
        cat=NOM[t]
        if t==chess.PAWN: cat='Pion central (d, e)' if chess.square_file(m.from_square) in (3,4) else 'Pion de flanc'
        agr[cat].append((dm,(tot1-tot0)-dm,tot1-tot0))
print(f"{ng} parties ; 10 premiers coups de chaque camp\n")
print(f"{'pièce jouée':22}{'coups':>9}{'flux de la pièce':>18}{'flux des autres':>17}{'flux total':>12}")
for cat,v in sorted(agr.items(),key=lambda kv:-statistics.mean(x[2] for x in kv[1])):
    print(f"{cat:22}{len(v):9}{statistics.mean(x[0] for x in v):+18.2f}{statistics.mean(x[1] for x in v):+17.2f}{statistics.mean(x[2] for x in v):+12.2f}")
