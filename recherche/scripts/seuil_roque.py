#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seuil_roque.py -- courbe dose-reponse : nombre de pieces qui menacent un roque -> probabilite de mat rapide.
Positions (toutes les 4 demi-coups entre 20 et 90) ou un camp a roque et son Roi est encore sur son aile de roque (colonnes f-h ou a-c).
Zone du roque = cases voisines du Roi + les trois cases devant lui (cases du bouclier de pions) : 12 cases.
A = nombre de pieces adverses (Cavalier, Fou, Tour, Dame) qui attaquent au moins une case de la zone. D = pieces du Roi qui la defendent.
Resultat = l'adversaire mate dans les 10 demi-coups suivants (partie reelle).
LIMITES : mat tres rare, correlation, positions successives non independantes, haut niveau, pas de controle de l'evaluation.
USAGE : python3 seuil_roque.py
"""
import re, io, chess, chess.pgn, collections
import numpy as np
PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
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
rows=[]; vus=set()
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
        mat_par=(not fin.turn) if fin.is_checkmate() else None; n=len(mv)
        roque={chess.WHITE:False,chess.BLACK:False}
        for i,m in enumerate(mv,1):
            if b.is_castling(m): roque[b.turn]=True
            b.push(m)
            if i<20 or i>90 or i%4: continue
            npieces=len(b.piece_map())
            for dfc in (chess.WHITE,chess.BLACK):
                if not roque[dfc]: continue
                K=b.king(dfc); f=chess.square_file(K)
                if not (f>=5 or f<=2): continue
                att=not dfc; Z=zone(K,dfc)
                A={s for sq in Z for s in b.attackers(att,sq) if b.piece_type_at(s) in PCS}
                D={s for sq in Z for s in b.attackers(dfc,sq) if b.piece_type_at(s) in PCS}
                rows.append((len(A),len(D),0 if npieces>=26 else (1 if npieces>=18 else 2),int(mat_par==att and 0<n-i<=10)))
D=np.array(rows,dtype=int); print(len(D),"positions (Roi roqué, encore sur son aile) ;",int(D[:,3].sum()),"mats dans les 10 demi-coups\n")
base=D[:,3].mean()
print(f"{'pièces adverses qui menacent la zone':40}{'positions':>10}{'mats':>7}{'taux':>9}{'× la moyenne':>14}")
for k in range(0,7):
    s=(D[:,0]==k) if k<6 else (D[:,0]>=6)
    if s.sum()>20: print(f"{('A = '+str(k)+(' ou plus' if k==6 else '')):40}{s.sum():10}{D[s,3].sum():7}{D[s,3].mean()*100:8.2f}%{D[s,3].mean()/base:13.1f}×")
print("\nSEUILS : taux de mat si A ≥ seuil (contre A < seuil)")
for t in (2,3,4,5):
    a=D[:,0]>=t; ra=D[a,3].mean(); rb=D[~a,3].mean(); se=(ra*(1-ra)/a.sum()+rb*(1-rb)/(~a).sum())**0.5
    print(f"   A ≥ {t} : {ra*100:.2f} % (n={a.sum()}) contre {rb*100:.2f} % : rapport {ra/rb:.1f}× (écart {100*(ra-rb):+.2f} points, t = {(ra-rb)/se:+.1f})")
print("\nA ≥ 3 PAR STADE (pièces sur l'échiquier) et PAR DÉFENSE (D = pièces du Roi qui défendent la zone)")
for lab,S in (("≥ 26 pièces",0),("18-25",1),("≤ 17",2)):
    s=D[:,2]==S; a=s&(D[:,0]>=3); b_=s&(D[:,0]<3)
    if a.sum()>20 and b_.sum()>20: print(f"   {lab:12} A≥3 : {D[a,3].mean()*100:.2f} % (n={a.sum()}) | A<3 : {D[b_,3].mean()*100:.2f} % (n={b_.sum()})")
for lab,lo,hi in (("D ≤ 1",0,1),("D = 2",2,2),("D ≥ 3",3,9)):
    s=(D[:,1]>=lo)&(D[:,1]<=hi); a=s&(D[:,0]>=3); b_=s&(D[:,0]<3)
    if a.sum()>20 and b_.sum()>20: print(f"   {lab:12} A≥3 : {D[a,3].mean()*100:.2f} % (n={a.sum()}) | A<3 : {D[b_,3].mean()*100:.2f} % (n={b_.sum()})")
