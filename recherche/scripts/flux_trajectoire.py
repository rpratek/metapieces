#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flux_trajectoire.py -- trajectoire du flux dans une partie type, premier deplacement vs suivants, et valeur du CHOIX.
Flux d'une piece (C, F, T, D) = cases attaquees non occupees par son camp.
A. Trajectoire : flux total moyen d'un camp apres son k-ieme coup (k = 0..12).
B. Premier deplacement (depuis la case de depart) vs deplacements suivants : gain de flux de la piece et des autres.
C. Valeur du choix : gain de flux du coup joue moins le gain moyen de tous les coups possibles de la meme piece (Cavalier, Fou, Dame), 1er deplacement.
LIMITES : flux = mobilite brute ; parties de haut niveau ; description, non preuve.
USAGE : python3 flux_trajectoire.py
"""
import re, io, random, chess, chess.pgn, collections, statistics, time
random.seed(5)
def pc(x): return bin(x).count('1')
PIECES=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def flux(b,col):
    own=b.occupied_co[col]; r={}
    for s,p in b.piece_map().items():
        if p.color==col and p.piece_type in PIECES: r[s]=pc(b.attacks_mask(s)&~own)
    return r
HOME={chess.WHITE:{chess.KNIGHT:{1,6},chess.BISHOP:{2,5},chess.ROOK:{0,7},chess.QUEEN:{3}},
      chess.BLACK:{chess.KNIGHT:{57,62},chess.BISHOP:{58,61},chess.ROOK:{56,63},chess.QUEEN:{59}}}
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
NOM={chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame'}
traj=collections.defaultdict(list); AB=collections.defaultdict(list); CH=collections.defaultdict(list); ng=0; ngc=0
t0=time.time()
for bloc in blocs:
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<26: continue
    ng+=1; faire_choix=(ng<=2500 and time.time()-t0<150)
    if faire_choix: ngc+=1
    nb={chess.WHITE:0,chess.BLACK:0}
    for k0 in (chess.WHITE,chess.BLACK): traj[(0,k0)].append(sum(flux(b,k0).values()))
    for i,m in enumerate(mv[:26]):
        col=b.turn; t=b.piece_type_at(m.from_square); F0=flux(b,col); tot0=sum(F0.values())
        prem=(t in PIECES and m.from_square in HOME[col][t])
        # valeur du choix : alternatives de la même pièce (premier déplacement, 10 premiers coups)
        alt=None
        if faire_choix and prem and t in (chess.KNIGHT,chess.BISHOP,chess.QUEEN) and i<20:
            vals=[]
            for m2 in b.legal_moves:
                if m2.from_square!=m.from_square: continue
                b.push(m2); vals.append(flux(b,col).get(m2.to_square,0)-F0.get(m.from_square,0)); b.pop()
            if len(vals)>=3: alt=statistics.mean(vals)
        b.push(m); F1=flux(b,col); tot1=sum(F1.values()); nb[col]+=1
        if nb[col]<=12: traj[(nb[col],col)].append(tot1)
        if t in PIECES and i<26:
            dm=F1.get(m.to_square,0)-F0.get(m.from_square,0)
            AB[(NOM[t],'1er déplacement' if prem else 'suivants')].append((dm,(tot1-tot0)-dm))
            if alt is not None: CH[NOM[t]].append((dm,alt))
print(f"{ng} parties ; choix évalué sur {ngc} parties ; {time.time()-t0:.0f} s\n")
print("A. FLUX TOTAL D'UN CAMP APRÈS SON k-IÈME COUP (moyenne des deux camps)")
print("   k : "+' '.join(f"{k:5d}" for k in range(0,13)))
print("   flux: "+' '.join(f"{statistics.mean(traj[(k,chess.WHITE)]+traj[(k,chess.BLACK)]):5.1f}" for k in range(0,13)))
print("\nB. GAIN DE FLUX DE LA PIÈCE ET DES AUTRES : 1er déplacement (case de départ) vs déplacements suivants")
print(f"   {'pièce':10}{'déplacement':18}{'coups':>8}{'flux de la pièce':>18}{'flux des autres':>17}")
for t in ('Cavalier','Fou','Dame','Tour'):
    for lab in ('1er déplacement','suivants'):
        v=AB.get((t,lab),[])
        if len(v)>30: print(f"   {t:10}{lab:18}{len(v):8}{statistics.mean(x[0] for x in v):+18.2f}{statistics.mean(x[1] for x in v):+17.2f}")
print("\nC. VALEUR DU CHOIX (1er déplacement) : gain du coup joué - gain moyen de tous les coups possibles de la même pièce")
for t in ('Cavalier','Fou','Dame'):
    v=CH.get(t,[])
    if len(v)>30: print(f"   {t:10} n={len(v):6} gain du coup joué {statistics.mean(x[0] for x in v):+.2f} | gain moyen des alternatives {statistics.mean(x[1] for x in v):+.2f} | avantage du choix {statistics.mean(x[0]-x[1] for x in v):+.2f}")
