#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flux_resultat.py -- le flux acquis dans l'ouverture predit-il le resultat ?
x_k = flux pondere des Blancs - flux pondere des Noirs apres k coups chacun (k = 6, 10, 15). Poids : coeur 4, zone pivot 3, couronne 2, bord 1.
Resultat = score des Blancs (1, 0,5, 0). Controle : difference d'Elo (WhiteElo - BlackElo) quand elle est connue.
Modele : regression lineaire (probabilite lineaire) score ~ x_k et score ~ x_k + dElo ; pente restreinte a |dElo| <= 50.
LIMITES : correlation, pas causalite ; parties de haut niveau ; beaucoup de nulles ; x est une mobilite brute.
USAGE : python3 flux_resultat.py
"""
import re, io, random, chess, chess.pgn, statistics, time
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
    own=b.occupied_co[col]; tot=0
    for s,p in b.piece_map().items():
        if p.color==col and p.piece_type in PIECES:
            tot+=sum(W[q] for q in chess.scan_forward(b.attacks_mask(s)&~own))
    return tot
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
KS=(6,10,15); data=[]; t0=time.time()
for bloc in blocs:
    r=re.search(r'\[Result "([^"]+)"\]',bloc)
    if not r or r.group(1) not in ('1-0','0-1','1/2-1/2'): continue
    score={'1-0':1.0,'0-1':0.0,'1/2-1/2':0.5}[r.group(1)]
    we=re.search(r'\[WhiteElo "(\d+)"\]',bloc); be=re.search(r'\[BlackElo "(\d+)"\]',bloc)
    de=(int(we.group(1))-int(be.group(1)))/100 if we and be else np.nan
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<2*max(KS)+10: continue
    xs=[]
    for i,m in enumerate(mv[:2*max(KS)],1):
        b.push(m)
        if i%2==0 and i//2 in KS: xs.append(flux(b,chess.WHITE)-flux(b,chess.BLACK))
    data.append([score,de]+xs)
D=np.array(data); print(f"{len(D)} parties avec résultat ; {np.isfinite(D[:,1]).sum()} avec Elo des deux joueurs ; {time.time()-t0:.0f} s\n")
y=D[:,0]; print(f"score moyen des Blancs : {y.mean():.3f} ; parts : victoires Blancs {np.mean(y==1)*100:.1f} %, nulles {np.mean(y==0.5)*100:.1f} %, victoires Noirs {np.mean(y==0)*100:.1f} %\n")
for j,k in enumerate(KS):
    x=D[:,2+j]
    corr=np.corrcoef(x,y)[0,1]
    qs=np.quantile(x,[0.2,0.4,0.6,0.8]); q=np.digitize(x,qs)
    moy=[y[q==i].mean() for i in range(5)]
    print(f"k = {k:2d} coups : corrélation flux-résultat {corr:+.3f} | score des Blancs par quintile de x (du plus défavorable au plus favorable) : "+' '.join(f"{m:.3f}" for m in moy))
print("\nCONTRÔLE DU CLASSEMENT (parties avec Elo)")
M=np.isfinite(D[:,1])
for j,k in enumerate(KS):
    x=D[M,2+j]; de=D[M,1]; yy=D[M,0]
    A1=np.c_[np.ones(len(x)),x]; b1=np.linalg.lstsq(A1,yy,rcond=None)[0]
    A2=np.c_[np.ones(len(x)),x,de]; b2=np.linalg.lstsq(A2,yy,rcond=None)[0]
    res=yy-A2@b2; se=np.sqrt(np.diag(np.linalg.inv(A2.T@A2))*res.var()); 
    sel=np.abs(de)<=0.5; A3=np.c_[np.ones(sel.sum()),x[sel]]; b3=np.linalg.lstsq(A3,yy[sel],rcond=None)[0]
    print(f"k = {k:2d} : pente du flux seul {b1[1]*100:+.3f} pt de score / unité ; avec Elo {b2[1]*100:+.3f} (t = {b2[1]/se[1]:.1f}) ; Elo seul : {b2[2]*100:+.2f} pt par 100 Elo ; parties à Elo voisins (|dElo| <= 50, n={sel.sum()}) : pente {b3[1]*100:+.3f}")
print("\nÉcart-type de x (unités de flux pondéré) : "+', '.join(f"k={k}: {D[:,2+j].std():.1f}" for j,k in enumerate(KS)))
