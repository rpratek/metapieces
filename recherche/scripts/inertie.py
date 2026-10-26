#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inertie.py -- cout d'engagement (« inertie ») des pieces pour changer d'aile.
Pour chaque piece lourde ou legere (Cavalier, Fou, Tour, Dame) posee sur une aile (colonnes a-c ou f-h), on calcule
le nombre minimal de coups pour atteindre l'aile opposee (colonnes f-h ou a-c) :
  - d_libre  : sur un echiquier vide ;
  - d_reel   : avec les pieces et pions de la position (ses propres pieces bloquent, les pieces adverses peuvent etre prises, rien d'autre).
Inertie (cout d'engagement) = d_reel - d_libre. Plafond : 6 coups (7 = inaccessible en 6).
Pas de prise en compte des clouages ni des echecs. Positions tirees toutes les 4 demi-coups, camp qui vient de jouer.
USAGE : python3 inertie.py <budget_secondes> <nb_parties>
"""
import re, io, sys, time, random, chess, chess.pgn, collections, statistics
random.seed(11)
CAP=6
DIAG=[(1,1),(1,-1),(-1,1),(-1,-1)]; ORTH=[(1,0),(-1,0),(0,1),(0,-1)]
KN=[(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
def sq(f,r): return r*8+f
RAYS={}  # (type, square) -> liste de rayons (chaque rayon = liste de cases) ou liste de sauts
for s in range(64):
    f,r=s%8,s//8
    for t,dirs in (('B',DIAG),('R',ORTH),('Q',DIAG+ORTH)):
        rays=[]
        for df,dr in dirs:
            ray=[]; ff,rr=f+df,r+dr
            while 0<=ff<8 and 0<=rr<8: ray.append(sq(ff,rr)); ff+=df; rr+=dr
            if ray: rays.append(ray)
        RAYS[(t,s)]=rays
    RAYS[('N',s)]=[[sq(f+df,r+dr)] for df,dr in KN if 0<=f+df<8 and 0<=r+dr<8]
WING_Q=0b00000111; WING_K=0b11100000
def cible(f): return WING_K if f<=2 else WING_Q
def bfs(t,s,own,enemy,target_files):
    """own/enemy : bitmasks (int) des cases occupees. Retourne le nb minimal de coups (<=CAP) ou CAP+1."""
    if (target_files>>(s%8))&1: return 0
    vus=1<<s; front=[s]
    for d in range(1,CAP+1):
        nxt=[]
        for u in front:
            for ray in RAYS[(t,u)]:
                for v in ray:
                    b=1<<v
                    if own&b: break
                    if not (vus&b):
                        vus|=b; nxt.append(v)
                        if (target_files>>(v%8))&1: return d
                    if enemy&b: break
        front=nxt
        if not front: break
    return CAP+1
LIBRE={}
def d_libre(t,s):
    k=(t,s)
    if k not in LIBRE: LIBRE[k]=bfs(t,s,0,0,cible(s%8))
    return LIBRE[k]
# --- parties
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
random.shuffle(blocs); NB=int(sys.argv[2]); blocs=blocs[:NB]
BUD=float(sys.argv[1]); t0=time.time()
TR=[(28,32,'28-32'),(24,27,'24-27'),(20,23,'20-23'),(16,19,'16-19'),(12,15,'12-15'),(8,11,'8-11'),(0,7,'<=7')]
def tranche(n):
    for a,b,l in TR:
        if a<=n<=b: return l
rows=[]  # (tranche, type, d_libre, d_reel, avance)
PT={chess.KNIGHT:'N',chess.BISHOP:'B',chess.ROOK:'R',chess.QUEEN:'Q'}
ng=0
for bloc in blocs:
    if time.time()-t0>BUD: break
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<20: continue
    ng+=1
    for i,m in enumerate(mv,1):
        b.push(m)
        if i%4: continue
        col=not b.turn                      # camp qui vient de jouer
        npieces=len(b.piece_map()); tr=tranche(npieces)
        own=sum(1<<s for s,p in b.piece_map().items() if p.color==col)
        enemy=sum(1<<s for s,p in b.piece_map().items() if p.color!=col)
        init=1 if col==chess.WHITE else 6
        adv=sum(1 for s in b.pieces(chess.PAWN,col) if s//8!=init)
        for s,p in b.piece_map().items():
            if p.color!=col or p.piece_type not in PT: continue
            f=s%8
            if f in (3,4): continue
            t=PT[p.piece_type]; dl=d_libre(t,s)
            dr=bfs(t,s,own&~(1<<s),enemy,cible(f))
            rows.append((tr,t,dl,dr,adv))
print(f"{ng} parties, {len(rows)} mesures de pièces en {time.time()-t0:.0f} s\n")
NOM={'N':'Cavalier','B':'Fou','R':'Tour','Q':'Dame'}
print("INERTIE = coups réels - coups libres, pour passer d'une aile à l'autre (moyenne ; entre parenthèses : coups réels)")
print(f"{'pièces sur l’échiquier':24}"+''.join(f"{NOM[t]:>16}" for t in 'NBRQ'))
for a,b,l in TR:
    ligne=f"{l:24}"
    for t in 'NBRQ':
        R=[(dl,dr) for tr,tt,dl,dr,adv in rows if tr==l and tt==t]
        ligne+=(f"{statistics.mean(dr-dl for dl,dr in R):+8.2f} ({statistics.mean(dr for dl,dr in R):.1f})" if len(R)>=30 else f"{'—':>16}").rjust(16)
    print(ligne)
print("\nEFFET DES PIONS : inertie des pièces à longue portée (Fou, Tour, Dame) selon le nombre de pions avancés du camp, à 20-32 pièces")
for lab,lo,hi in (("0 à 2 pions avancés",0,2),("3 à 4",3,4),("5 et plus",5,8)):
    R=[(dr-dl) for tr,tt,dl,dr,adv in rows if tt in 'BRQ' and tr in ('28-32','24-27','20-23') and lo<=adv<=hi]
    print(f"  {lab:24} n={len(R):6} inertie moyenne {statistics.mean(R):+.2f}")
print("\nPART DES PIÈCES QUI NE PEUVENT PAS CHANGER D'AILE EN 6 COUPS (inaccessible)")
for a,b,l in TR[:4]:
    R=[dr for tr,tt,dl,dr,adv in rows if tr==l]
    print(f"  {l:8} {sum(1 for d in R if d>CAP)/len(R)*100:5.1f} %  (n={len(R)})")
