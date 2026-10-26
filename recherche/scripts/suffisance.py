#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suffisance.py -- l'attaquant dispose-t-il encore des pieces capables de porter le coup ?
Pour chaque mat de TWIC : nombre de Cavaliers, de Fous, de Tours, de Dames de l'attaquant au moment du mat ; enfermement du Roi mate (part des cases adjacentes occupees par ses propres pieces).
Question : quand le Roi est enferme par ses pieces, l'attaquant a-t-il plus souvent encore un Cavalier ? Combien de pieces mineures reste-t-il en general ?
LIMITES : mats reussis seulement (on ne voit pas les attaques qui ont echoue faute de matériel) ; description.
USAGE : python3 suffisance.py
"""
import re, io, chess, chess.pgn, collections
import numpy as np
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
            g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board()
            for m in g.mainline_moves(): b.push(m)
        except Exception: continue
        if not b.is_checkmate(): continue
        dfc=b.turn; att=not dfc; K=b.king(dfc); vois=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
        enf=sum(1 for s in vois if b.piece_at(s) and b.piece_at(s).color==dfc)/len(vois)
        n=lambda t:len(b.pieces(t,att))
        rows.append((enf,n(chess.KNIGHT),n(chess.BISHOP),n(chess.ROOK),n(chess.QUEEN),n(chess.PAWN)))
D=np.array(rows); print(len(D),"mats\n")
mineur=D[:,1]+D[:,2]; lourd=D[:,3]+D[:,4]
print("A. PIÈCES DE L'ATTAQUANT AU MOMENT DU MAT")
print(f"   aucune pièce mineure (ni Cavalier ni Fou) : {np.mean(mineur==0)*100:.0f} % | exactement une : {np.mean(mineur==1)*100:.0f} % | deux ou plus : {np.mean(mineur>=2)*100:.0f} %")
print(f"   aucune pièce lourde (ni Tour ni Dame) : {np.mean(lourd==0)*100:.0f} % | au moins une : {np.mean(lourd>=1)*100:.0f} %")
print(f"   ni pièce mineure ni pièce lourde (Roi et pions seulement) : {np.mean((mineur+lourd)==0)*100:.1f} %")
print("\nB. LE ROI ENFERMÉ PAR SES PIÈCES : l'attaquant a-t-il encore un Cavalier ?")
print(f"   {'enfermement':34}{'mats':>6}{'au moins un Cavalier':>24}{'au moins une pièce mineure':>28}")
for lab,lo,hi in (("aucune case fermée par le Roi",0,0),("au moins une case",0.01,0.49),("au moins la moitié des cases",0.5,1.0)):
    s=(D[:,0]>=lo)&(D[:,0]<=hi)
    print(f"   {lab:34}{s.sum():6}{np.mean(D[s,1]>=1)*100:22.0f} %{np.mean(mineur[s]>=1)*100:26.0f} %")
s=(D[:,0]>=0.5); t=(D[:,0]==0)
print("\nC. ÉCART : attaquant avec Cavalier, rempart fort (≥ la moitié des cases) contre rempart nul")
a=np.mean(D[s,1]>=1); b=np.mean(D[t,1]>=1); se=(a*(1-a)/s.sum()+b*(1-b)/t.sum())**0.5
print(f"   {a*100:.0f} % contre {b*100:.0f} % : écart {100*(a-b):+.0f} points (t = {(a-b)/se:+.1f})")
