#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
etouffe.py -- le Roi enferme par ses propres pieces : qui donne le mat ?
Pour chaque mat des archives TWIC : part des cases adjacentes au Roi occupees par ses propres pieces ; piece qui donne le mat ; mat par prise ou non.
Categories : « etouffe complet » (toutes les cases adjacentes occupees par ses pieces), « presque » (au moins la moitie), « partiel » (au moins une), « ouvert » (aucune).
USAGE : python3 etouffe.py
"""
import re, io, chess, chess.pgn, collections
NOM={chess.PAWN:'Pion',chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame'}
cat=collections.Counter(); mat_par=collections.defaultdict(collections.Counter); prise=collections.defaultdict(lambda:[0,0]); n=0; vus=set()
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
        r=re.search(r'\[Result "([^"]+)"\]',bloc)
        if not r or r.group(1) not in ('1-0','0-1') or '#' not in cle: continue
        try:
            g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
            for m in mv[:-1]: b.push(m)
            dernier=mv[-1]; capt=b.is_capture(dernier); pt=b.piece_type_at(dernier.from_square); b.push(dernier)
        except Exception: continue
        if not b.is_checkmate(): continue
        n+=1; dfc=b.turn; K=b.king(dfc); vois=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
        propre=sum(1 for s in vois if b.piece_at(s) and b.piece_at(s).color==dfc); f=propre/len(vois)
        k='complet' if f==1 else ('presque' if f>=0.5 else ('partiel' if f>0 else 'ouvert'))
        cat[k]+=1; mat_par[k][NOM.get(pt,'Roi')]+=1; prise[k][0]+=capt; prise[k][1]+=1
print(f"{n} mats\n")
print(f"{'Roi enfermé par ses propres pièces':36}{'mats':>7}{'part':>8}{'dont mat par prise':>20}   pièce qui donne le mat")
for k,lab in (('complet','complet (toutes les cases)'),('presque','au moins la moitié des cases'),('partiel','au moins une case'),('ouvert','aucune case')):
    v=mat_par[k]; tot=sum(v.values())
    print(f"{lab:36}{cat[k]:7}{cat[k]/n*100:7.1f}%{prise[k][0]/max(1,prise[k][1])*100:18.0f} %   "+', '.join(f"{p} {c/tot*100:.0f} %" for p,c in v.most_common(4)))
tot_c=sum(cat[k] for k in ('complet','presque','partiel'))
cav=sum(1 for k in cat for _ in [0] if False)
print("\nMats donnés par un Cavalier : part où le Roi est enfermé par ses propres pièces (au moins une case) :",end=' ')
tc=sum(mat_par[k]['Cavalier'] for k in cat); ec=sum(mat_par[k]['Cavalier'] for k in ('complet','presque','partiel'))
print(f"{ec}/{tc} ({ec/max(1,tc)*100:.0f} %) ; enfermement complet : {mat_par['complet']['Cavalier']}/{tc}")
