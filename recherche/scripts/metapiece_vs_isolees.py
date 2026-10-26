#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metapiece_vs_isolees.py -- À NOMBRE DE PIÈCES ÉGAL, des pièces qui CONVERGENT (une Métapièce) mènent-elles plus souvent au mat que des pièces ISOLÉES ?
Mêmes positions que seuil_roque.py (Roi roqué sur son aile, tous les 4 demi-coups de 20 à 90, zone de 12 cases, mat dans les 10 demi-coups).
A = pièces adverses (C, F, T, D) qui attaquent la zone ; Mc = taille du plus grand groupe d'attaquants reliés par au moins une case de la zone qu'ils attaquent
tous deux (la Métapièce). Mc = A : toutes les pièces sont reliées ; Mc = 1 : aucune n'est reliée à une autre (pièces isolées).
Intervalles de confiance : bootstrap PAR PARTIE (500 tirages).
USAGE : cd donnees ; python3 ../recherche/scripts/metapiece_vs_isolees.py"""
import re, io, chess, chess.pgn, numpy as np, time
t0=time.time(); PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def zone(K,col):
    f,r=chess.square_file(K),chess.square_rank(K); z=set()
    for df in (-1,0,1):
        for dr in (-1,0,1):
            ff,rr=f+df,r+dr
            if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    dr=1 if col==chess.WHITE else -1
    for df in (-1,0,1):
        ff,rr=f+df,r+2*dr
        if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    return z
def compmax(att):
    ks=list(att); seen=set(); best=0
    for k in ks:
        if k in seen: continue
        pile=[k]; seen.add(k); n=0
        while pile:
            u=pile.pop(); n+=1
            for v in ks:
                if v not in seen and att[u]&att[v]: seen.add(v); pile.append(v)
        best=max(best,n)
    return best
rows=[]; vus=set(); gid=0
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
        vus.add(cle)
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
        except Exception: continue
        if len(mv)<30: continue
        fin=g.board()
        for m in mv: fin.push(m)
        mat_par=(not fin.turn) if fin.is_checkmate() else None; n=len(mv); gid+=1
        roque={chess.WHITE:False,chess.BLACK:False}
        for i,m in enumerate(mv,1):
            if b.is_castling(m): roque[b.turn]=True
            b.push(m)
            if i<20 or i>90 or i%4: continue
            for dfc in (chess.WHITE,chess.BLACK):
                if not roque[dfc]: continue
                K=b.king(dfc); f=chess.square_file(K)
                if not (f>=5 or f<=2): continue
                att=not dfc; Z=zone(K,dfc); pa={}
                for sq in Z:
                    for s in b.attackers(att,sq):
                        if b.piece_type_at(s) in PCS: pa.setdefault(s,set()).add(sq)
                rows.append((gid,len(pa),compmax(pa) if pa else 0,int(mat_par==att and 0<n-i<=10)))
R=np.array(rows,int); G=R[:,0]; A=R[:,1]; Mc=R[:,2]; y=R[:,3]; ng=G.max()
print(f"{len(R)} positions, {ng} parties, {int(y.sum())} mats ({time.time()-t0:.0f} s)")
rng=np.random.default_rng(4); W=[rng.multinomial(ng,np.ones(ng)/ng)[G-1] for _ in range(500)]
def taux(f,w): return (w*y*f).sum()/(w*f).sum()
def ligne(nom,f,g=None):
    r0=taux(f,np.ones(len(y)))
    s=f"   {nom:46} n={int(f.sum()):>7}  taux {100*r0:5.2f} %"
    if g is not None:
        rr=r0/taux(g,np.ones(len(y))); bs=[taux(f,w)/taux(g,w) for w in W]; lo,hi=np.percentile(bs,[2.5,97.5]); s+=f"  rapport {rr:4.1f} x [{lo:4.1f} ; {hi:4.1f}]"
    print(s)
print("\nDEUX PIÈCES (A = 2) :")
f2c=(A==2)&(Mc==2); f2i=(A==2)&(Mc==1)
ligne("deux pièces ISOLÉES (aucune case commune)",f2i); ligne("deux pièces qui CONVERGENT (un Binôme)",f2c,f2i)
print("\nTROIS PIÈCES (A = 3) :")
f3i=(A==3)&(Mc==1); f3p=(A==3)&(Mc==2); f3c=(A==3)&(Mc==3)
ligne("trois pièces ISOLÉES",f3i); ligne("un Binôme + une pièce isolée",f3p,f3i); ligne("trois pièces qui CONVERGENT (un Trinôme)",f3c,f3i)
print("\nTROIS PIÈCES OU PLUS (A >= 3) :")
fi=(A>=3)&(Mc<3); fc=(A>=3)&(Mc>=3)
ligne("pas de groupe relié de trois pièces",fi); ligne("un groupe relié d'au moins trois pièces",fc,fi)
print("\nTOUTES POSITIONS AVEC AU MOINS DEUX PIÈCES (A >= 2) :")
ligne("aucune paire reliée (Mc = 1)",(A>=2)&(Mc==1)); ligne("au moins une paire reliée (Mc >= 2)",(A>=2)&(Mc>=2),(A>=2)&(Mc==1))
print("\nPART DES MATS SELON LA TAILLE DU PLUS GRAND GROUPE RELIÉ (parmi les positions suivies d'un mat) :")
m=y==1; tot=m.sum()
for lab,s in (("aucune pièce attaquante (A = 0)",A==0),("pièces isolées seulement (Mc = 1)",Mc==1),("un Binôme (Mc = 2)",Mc==2),("un Trinôme ou plus (Mc >= 3)",Mc>=3)):
    print(f"   {lab:40} {int((m&s).sum()):>5} mats ({100*(m&s).sum()/tot:4.1f} %)   sur {100*s.mean():4.1f} % des positions")
