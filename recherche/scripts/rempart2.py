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
print("PERTE DE L'ATTAQUANT (en pions) selon l'épaisseur du rempart, A L'INTÉRIEUR de chaque stade de la partie")
print(f"{'pièces (12 demi-coups avant)':30}{'rempart 0-1':>16}{'rempart 2 et +':>18}{'écart':>9}")
for lab,lo,hi in (("24 et plus",24,40),("16 à 23",16,23),("8 à 15",8,15),("7 ou moins",0,7)):
    st=(D[:,4]>=lo)&(D[:,4]<=hi); a=st&(D[:,0]<=1); b=st&(D[:,0]>=2)
    if a.sum()>10 and b.sum()>10:
        d=D[b,2].mean()-D[a,2].mean(); se=(D[a,2].var()/a.sum()+D[b,2].var()/b.sum())**0.5
        print(f"{lab:30}{D[a,2].mean():8.2f} (n={a.sum():3}){D[b,2].mean():10.2f} (n={b.sum():3}){d:+8.2f}  (t = {d/se:+.1f})")
