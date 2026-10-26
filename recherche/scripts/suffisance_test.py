#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suffisance_test.py -- contre un Roi muré par ses propres pieces, la presence d'un Cavalier chez l'attaquant change-t-elle la probabilite d'un mat rapide ?
Positions (toutes les 4 demi-coups, entre 20 et 90) ou le Roi d'un camp a au moins la moitie de ses cases adjacentes occupees par ses propres pieces, et ou l'adversaire a au moins une Tour ou une Dame.
Resultat = l'adversaire mate dans les 10 demi-coups suivants (dans la partie reellement jouee).
Comparaison : attaquant avec au moins un Cavalier / sans Cavalier, par strates (nombre de pieces lourdes, presence d'un Fou, stade de la partie).
LIMITES : partie reelle ; correlation ; positions successives d'une meme partie non independantes ; haut niveau ; effectifs faibles dans certaines strates.
USAGE : python3 suffisance_test.py
"""
import re, io, chess, chess.pgn, collections, math
import numpy as np
cases=[]; vus=set()
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
        for i,m in enumerate(mv,1):
            b.push(m)
            if i<20 or i>90 or i%4: continue
            for dfc in (chess.WHITE,chess.BLACK):
                att=not dfc; K=b.king(dfc)
                vois=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
                enf=sum(1 for s in vois if b.piece_at(s) and b.piece_at(s).color==dfc)/len(vois)
                if enf<0.5: continue
                lourds=len(b.pieces(chess.ROOK,att))+len(b.pieces(chess.QUEEN,att))
                if lourds==0: continue
                cav=len(b.pieces(chess.KNIGHT,att)); fou=len(b.pieces(chess.BISHOP,att)); npieces=len(b.piece_map())
                reussi=(mat_par==att and 0<n-i<=10)
                cases.append((cav>=1,min(lourds,2),fou>=1,0 if npieces>=26 else (1 if npieces>=18 else 2),reussi))
D=np.array(cases,dtype=int); print(len(D),"positions (Roi muré à moitié ou plus, attaquant avec Tour ou Dame)")
a=D[:,0]==1; r=D[:,4]==1
print(f"Taux de mat dans les 10 demi-coups : attaquant AVEC Cavalier {r[a].mean()*100:.2f} % (n={a.sum()}) | SANS Cavalier {r[~a].mean()*100:.2f} % (n={(~a).sum()})")
print("\nPar strates (pièces lourdes de l'attaquant, présence d'un Fou, stade) :")
print(f"{'strate':46}{'avec Cav.':>14}{'sans Cav.':>14}")
num=den=0; poids=[]; diffs=[]
for L in (1,2):
    for F in (0,1):
        for S in (0,1,2):
            s=(D[:,1]==L)&(D[:,2]==F)&(D[:,3]==S)
            na=(s&a).sum(); nb=(s&~a).sum()
            if na>=15 and nb>=15:
                pa=r[s&a].mean(); pb=r[s&~a].mean(); w=1/(1/na+1/nb); poids.append(w); diffs.append(pa-pb)
                print(f"{('Q/T×'+str(L)+(', avec Fou' if F else ', sans Fou')+', stade '+['≥26 pièces','18-25','≤17'][S]):46}{pa*100:8.1f} % ({na:3}){pb*100:8.1f} % ({nb:3})")
poids=np.array(poids); diffs=np.array(diffs); m=(poids*diffs).sum()/poids.sum(); se=1/np.sqrt(poids.sum())*np.sqrt(0.05*0.95)
print(f"\nÉcart poolé (avec - sans Cavalier), mêmes strates : {m*100:+.2f} points de pourcentage")
