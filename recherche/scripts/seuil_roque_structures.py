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

def structure(b,dfc,K):
    f=chess.square_file(K); n=lambda c:chess.parse_square(c)
    P=lambda c:(b.piece_at(n(c)) is not None and b.piece_at(n(c)).piece_type==chess.PAWN and b.piece_at(n(c)).color==dfc)
    B=lambda c:(b.piece_at(n(c)) is not None and b.piece_at(n(c)).piece_type==chess.BISHOP and b.piece_at(n(c)).color==dfc)
    w=(dfc==chess.WHITE)
    if f>=5:   # aile roi
        std=all(P(c) for c in (('f2','g2','h2') if w else ('f7','g7','h7')))
        pg=P('g3') if w else P('g6'); bg=B('g2') if w else B('g7')
    else:      # aile dame
        std=all(P(c) for c in (('a2','b2','c2') if w else ('a7','b7','c7')))
        pg=P('b3') if w else P('b6'); bg=B('b2') if w else B('b7')
    if std: return 0
    if pg and bg: return 1
    if pg: return 2
    return 3
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
                rows.append((len(A),len(D),0 if npieces>=26 else (1 if npieces>=18 else 2),int(mat_par==att and 0<n-i<=10),structure(b,dfc,K)))
D=np.array(rows,dtype=int); print(len(D),"positions ;",int(D[:,3].sum()),"mats dans les 10 demi-coups\n")
NOM=["roque classique (3 pions du bouclier intacts)","FIANCHETTO (pion g3/g6 ou b3/b6 + Fou en place)","pion de fianchetto SANS Fou (trou)","autre structure (pions avancés, bouclier entamé)"]
print(f"{'structure du roque':52}{'positions':>10}{'mats':>6}{'taux':>8}{'A moyen':>9}{'D moyen':>9}")
for k in range(4):
    s_=D[:,4]==k; print(f"{NOM[k]:52}{s_.sum():10}{D[s_,3].sum():6}{D[s_,3].mean()*100:7.2f}%{D[s_,0].mean():9.2f}{D[s_,1].mean():9.2f}")
print("\nTAUX DE MAT SELON LE NOMBRE A DE PIÈCES QUI MENACENT LA ZONE, PAR STRUCTURE")
print(f"{'structure':52}{'A=0-1':>10}{'A=2':>10}{'A=3':>10}{'A≥4':>10}{'A≥3 / A<3':>14}")
for k in range(4):
    s_=D[:,4]==k; r=[]
    for lo,hi in ((0,1),(2,2),(3,3),(4,9)):
        m=s_&(D[:,0]>=lo)&(D[:,0]<=hi); r.append(f"{D[m,3].mean()*100:5.2f}% ({m.sum()})" if m.sum()>=30 else "—")
    a=s_&(D[:,0]>=3); b_=s_&(D[:,0]<3)
    rap=(D[a,3].mean()/D[b_,3].mean()) if a.sum()>=30 and D[b_,3].mean()>0 else float('nan')
    print(f"{NOM[k][:52]:52}"+''.join(f"{x:>10}" for x in r)+f"{rap:13.1f}×")
