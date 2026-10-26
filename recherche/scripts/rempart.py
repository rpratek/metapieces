#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rempart.py -- combien coute la destruction d'un rempart ?
Pour chaque mat de TWIC : epaisseur du rempart = nombre de pieces ou pions du Roi mate sur ses cases adjacentes ;
coalition = nombre de pieces attaquantes (hors Rois) qui attaquent la zone du Roi (sa case et les cases adjacentes) ;
cout pour l'attaquant sur les 12 derniers demi-coups = valeur des pieces (hors pions) que l'attaquant a PERDUES (1 pion = 1, C/F = 3, T = 5, D = 9) ;
avancement = nombre de pieces sur l'echiquier 12 demi-coups avant le mat.
LIMITES : mats reussis seulement ; description ; un seul horizon (12 demi-coups).
USAGE : python3 rempart.py
"""
import re, io, chess, chess.pgn, collections, statistics
import numpy as np
VAL={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9}
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
        vus.add(cle); r=re.search(r'\[Result "([^"]+)"\]',bloc)
        if not r or r.group(1) not in ('1-0','0-1') or '#' not in cle: continue
        try:
            g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
        except Exception: continue
        if len(mv)<26: continue
        pos_av=None; pertes_att=0; gains_att=0
        for i,m in enumerate(mv):
            if i==len(mv)-12: pos_av=len(b.piece_map())
            cap=b.is_capture(m)
            if cap and i>=len(mv)-12:
                tgt=m.to_square
                if b.is_en_passant(m): v=1; col_vict=not b.turn
                else: p=b.piece_at(tgt); v=VAL.get(p.piece_type,0); col_vict=p.color
                rows_cap=(col_vict,v)
                # on note la couleur de la victime ; l'attaquant est connu a la fin
                if 'caps' not in locals() or i==len(mv)-12: caps=[]
                caps.append((col_vict,v))
            b.push(m)
        if not b.is_checkmate(): continue
        dfc=b.turn; att=not dfc; K=b.king(dfc)
        # captures des 12 derniers demi-coups : on les recalcule proprement
        b2=g.board(); caps=[]
        for i,m in enumerate(mv):
            if i>=len(mv)-12 and b2.is_capture(m):
                if b2.is_en_passant(m): caps.append((not b2.turn,1))
                else:
                    p=b2.piece_at(m.to_square); caps.append((p.color,VAL.get(p.piece_type,0)))
            b2.push(m)
        perte_att=sum(v for col,v in caps if col==att); perte_def=sum(v for col,v in caps if col==dfc)
        vois=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
        epais=sum(1 for s in vois if b.piece_at(s) and b.piece_at(s).color==dfc)
        zone=[K]+vois
        A={s for sq in zone for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
        rows.append((epais,len(A),perte_att,perte_def,pos_av if pos_av else 32))
D=np.array(rows); print(len(D),"mats\n")
print("A. SELON L'ÉPAISSEUR DU REMPART (pièces du Roi sur ses cases adjacentes)")
print(f"{'rempart':14}{'mats':>6}{'coalition (pièces)':>20}{'perte de l’attaquant (pions)':>30}{'attaquant perd ≥ 3':>20}")
for lab,lo,hi in (("0 à 1 pièce",0,1),("2 à 3",2,3),("4 et plus",4,8)):
    s=(D[:,0]>=lo)&(D[:,0]<=hi)
    print(f"{lab:14}{s.sum():6}{D[s,1].mean():20.2f}{D[s,2].mean():30.2f}{(D[s,2]>=3).mean()*100:19.0f} %")
print("\nB. SELON L'AVANCEMENT (pièces sur l'échiquier 12 demi-coups avant le mat)")
print(f"{'pièces':14}{'mats':>6}{'rempart moyen':>16}{'coalition':>12}{'perte de l’attaquant':>24}")
for lab,lo,hi in (("24 et plus",24,40),("16 à 23",16,23),("8 à 15",8,15),("7 ou moins",0,7)):
    s=(D[:,4]>=lo)&(D[:,4]<=hi)
    if s.sum()>10: print(f"{lab:14}{s.sum():6}{D[s,0].mean():16.2f}{D[s,1].mean():12.2f}{D[s,2].mean():24.2f}")
print("\nC. CORRÉLATIONS (rempart, coalition, perte de l'attaquant, nombre de pièces)")
for a,na in ((0,'rempart'),):
    for b_,nb in ((1,'coalition'),(2,'perte de l’attaquant'),(4,'pièces sur l’échiquier')):
        print(f"   {na} - {nb} : {np.corrcoef(D[:,a],D[:,b_])[0,1]:+.2f}")
