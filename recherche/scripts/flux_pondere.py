#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flux_pondere.py -- flux des pieces pondere par la valeur des cases attaquees (gradient du Pivot).
Poids d'une case : coeur (d4 e4 d5 e5) = 4 ; reste de la zone pivot c3-f6 = 3 ; couronne b2-g7 = 2 ; bord = 1.
Flux pondere d'une piece (C, F, T, D) = somme des poids des cases attaquees non occupees par son camp.
Reprend la mesure du « choix » : coup joue vs toutes les alternatives de la meme piece depuis la meme case (1er deplacement),
et la part des coups qui arrivent dans la zone pivot c3-f6.
USAGE : python3 flux_pondere.py
"""
import re, io, random, chess, chess.pgn, collections, statistics, time
random.seed(5)
def poids(s):
    f,r=s%8,s//8
    if f in (3,4) and r in (3,4): return 4
    if 2<=f<=5 and 2<=r<=5: return 3
    if 1<=f<=6 and 1<=r<=6: return 2
    return 1
W=[poids(s) for s in range(64)]
PIVOT={s for s in range(64) if 2<=s%8<=5 and 2<=s//8<=5}
PIECES=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def fp(b,s,own): 
    m=b.attacks_mask(s)&~own; return sum(W[q] for q in chess.scan_forward(m))
def flux(b,col):
    own=b.occupied_co[col]; return {s:fp(b,s,own) for s,p in b.piece_map().items() if p.color==col and p.piece_type in PIECES}
HOME={chess.WHITE:{chess.KNIGHT:{1,6},chess.BISHOP:{2,5},chess.ROOK:{0,7},chess.QUEEN:{3}},chess.BLACK:{chess.KNIGHT:{57,62},chess.BISHOP:{58,61},chess.ROOK:{56,63},chess.QUEEN:{59}}}
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
random.shuffle(blocs)
NOM={chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.QUEEN:'Dame'}
traj=collections.defaultdict(list); CH=collections.defaultdict(list); PV=collections.defaultdict(list); ng=0; t0=time.time()
for bloc in blocs:
    if time.time()-t0>200: break
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<26: continue
    ng+=1; nb={chess.WHITE:0,chess.BLACK:0}
    for c0 in (chess.WHITE,chess.BLACK): traj[(0,c0)].append(sum(flux(b,c0).values()))
    for i,m in enumerate(mv[:26]):
        col=b.turn; t=b.piece_type_at(m.from_square); F0=flux(b,col)
        prem=(t in PIECES and m.from_square in HOME[col][t])
        if prem and t in NOM and i<20 and ng<=2500:
            vals=[]; piv=[]
            for m2 in b.legal_moves:
                if m2.from_square!=m.from_square: continue
                b.push(m2); vals.append(flux(b,col).get(m2.to_square,0)-F0.get(m.from_square,0)); piv.append(1 if m2.to_square in PIVOT else 0); b.pop()
            b.push(m); dm=flux(b,col).get(m.to_square,0)-F0.get(m.from_square,0); b.pop()
            if len(vals)>=3:
                CH[NOM[t]].append((dm,statistics.mean(vals))); PV[NOM[t]].append((1 if m.to_square in PIVOT else 0,statistics.mean(piv)))
        b.push(m); nb[col]+=1
        if nb[col]<=12: traj[(nb[col],col)].append(sum(flux(b,col).values()))
print(f"{ng} parties ; {time.time()-t0:.0f} s\n")
print("A. FLUX PONDÉRÉ TOTAL D'UN CAMP APRÈS SON k-IÈME COUP")
print("   k :    "+' '.join(f"{k:5d}" for k in range(0,13)))
print("   flux:  "+' '.join(f"{statistics.mean(traj[(k,chess.WHITE)]+traj[(k,chess.BLACK)]):5.1f}" for k in range(0,13)))
print("\nC. VALEUR DU CHOIX, FLUX PONDÉRÉ (1er déplacement)")
for t in ('Cavalier','Fou','Dame'):
    v=CH.get(t,[])
    if len(v)>30: print(f"   {t:9} n={len(v):5} coup joué {statistics.mean(x[0] for x in v):+6.2f} | alternatives {statistics.mean(x[1] for x in v):+6.2f} | avantage du choix {statistics.mean(x[0]-x[1] for x in v):+5.2f}")
print("\nD. ARRIVÉE DANS LA ZONE PIVOT (c3-f6) : coup joué vs moyenne des alternatives")
for t in ('Cavalier','Fou','Dame'):
    v=PV.get(t,[])
    if len(v)>30: print(f"   {t:9} coup joué {statistics.mean(x[0] for x in v)*100:5.1f} % | alternatives {statistics.mean(x[1] for x in v)*100:5.1f} %")
