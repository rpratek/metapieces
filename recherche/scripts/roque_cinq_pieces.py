#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roque_cinq_pieces.py -- « il faut 5 pieces pour detruire un roque » : a verifier.
Pour chaque mat de TWIC : le Roi mate a-t-il roque dans la partie et se trouve-t-il encore sur son aile de roque (colonnes f-h ou a-c) ?
Mesures : (A) coalition = pieces attaquantes (hors Roi, pions exclus puis inclus) qui attaquent la zone du Roi (sa case et les cases voisines) ;
(B) pieces ENGAGEES = pieces de l'attaquant (hors Roi) qui ont joue au moins un coup dans ses 6 derniers coups, ou qui participent a la coalition.
Comparaison : Roi roque contre Roi non roque. Repere : 5 pieces.
LIMITES : mats reussis seulement (on ne voit pas les attaques echouees faute de pieces) ; description ; l'identite d'une piece est suivie par ses deplacements.
USAGE : python3 roque_cinq_pieces.py
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
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
        except Exception: continue
        if len(mv)<20: continue
        roque={chess.WHITE:False,chess.BLACK:False}; arrive={}; 
        # suivi des pieces : case -> dernier demi-coup où la pièce a bougé
        dernier={s:0 for s in b.piece_map()}
        for i,m in enumerate(mv,1):
            col=b.turn
            if b.is_castling(m): roque[col]=True
            if b.is_en_passant(m): dernier.pop(chess.square(chess.square_file(m.to_square),chess.square_rank(m.from_square)),None)
            dernier.pop(m.to_square,None)
            if b.is_castling(m):
                dernier.pop(m.from_square,None); dernier[m.to_square]=i
                rk=chess.square_rank(m.to_square)
                if chess.square_file(m.to_square)==6: dernier.pop(chess.square(7,rk),None); dernier[chess.square(5,rk)]=i
                else: dernier.pop(chess.square(0,rk),None); dernier[chess.square(3,rk)]=i
            else:
                dernier.pop(m.from_square,None); dernier[m.to_square]=i
            b.push(m)
        if not b.is_checkmate(): continue
        n=len(mv); dfc=b.turn; att=not dfc; K=b.king(dfc); f=chess.square_file(K)
        aile_roque=(f>=5 or f<=2)
        zone=[K]+[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
        A={s for sq in zone for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
        Asp={s for s in A if b.piece_type_at(s)!=chess.PAWN}
        eng={s for s,p in b.piece_map().items() if p.color==att and p.piece_type not in (chess.KING,chess.PAWN) and (n-dernier.get(s,0))<=11}|Asp
        rows.append((roque[dfc] and aile_roque,len(A),len(Asp),len(eng)))
D=np.array(rows,dtype=int); print(len(D),"mats ;",int(D[:,0].sum()),"contre un Roi qui a roqué et reste sur son aile de roque\n")
print(f"{'Roi mate':28}{'mats':>6}{'coalition (sans pions)':>26}{'≥ 5 pièces':>12}{'pièces engagées':>18}{'≥ 5':>8}")
for lab,s in (("a roqué (reste sur son aile)",D[:,0]==1),("n'a pas roqué ou a quitté l'aile",D[:,0]==0)):
    print(f"{lab:28}{s.sum():6}{np.mean(D[s,2]):20.2f} ± {np.std(D[s,2])/s.sum()**0.5:3.2f}{np.mean(D[s,2]>=5)*100:11.1f} %{np.mean(D[s,3]):14.2f}{np.mean(D[s,3]>=5)*100:9.1f} %")
s=D[:,0]==1
print("\nDistribution de la coalition (sans pions) contre un Roi roqué :",{k:int((D[s,2]==k).sum()) for k in range(0,8)})
print("Distribution des pièces engagées contre un Roi roqué :",{k:int((D[s,3]==k).sum()) for k in range(0,9)})
print("Médiane de la coalition / des pièces engagées :",int(np.median(D[s,2])),"/",int(np.median(D[s,3])))
