#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
etouffe_composition.py -- de quoi est fait le rempart d'un Roi mate quand il est enferme par ses propres pieces (au moins la moitie des cases voisines) ?
Types de pieces qui ferment les cases voisines ; part des Fous ; Fou en position de fianchetto (g2/b2 pour les Blancs, g7/b7 pour les Noirs) ; Roi dans un coin.
Detail des mats d'etouffe complets (toutes les cases voisines occupees par les pieces du Roi).
LIMITES : tres petits effectifs ; mats reussis seulement.
USAGE : python3 etouffe_composition.py
"""
import re, io, chess, chess.pgn, collections
NOM={chess.PAWN:'pion',chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame'}
FIAN={chess.WHITE:{'g2','b2'},chess.BLACK:{'g7','b7'}}
tot=0; enf=0; compo=collections.Counter(); fou_bloque=0; fou_fian=0; coin=0; complets=[]
vus=set()
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
        for m in mv[:-1]: b.push(m)
        san=b.san(mv[-1]); b.push(mv[-1])
        if not b.is_checkmate(): continue
        tot+=1; dfc=b.turn; K=b.king(dfc); vois=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
        occ=[(s,b.piece_at(s)) for s in vois if b.piece_at(s) and b.piece_at(s).color==dfc]
        if len(occ)/len(vois)<0.5: continue
        enf+=1; blocs=[p.piece_type for s,p in occ]
        for t in blocs: compo[NOM[t]]+=1
        fb=[s for s,p in occ if p.piece_type==chess.BISHOP]
        if fb: fou_bloque+=1
        if any(chess.square_name(s) in FIAN[dfc] for s in fb): fou_fian+=1
        if chess.square_name(K) in ('h1','a1','h8','a8'): coin+=1
        if len(occ)==len(vois): complets.append((b.fen(),san,[NOM[p.piece_type]+'@'+chess.square_name(s) for s,p in occ],chess.square_name(K)))
print(f"{tot} mats ; Roi enfermé par ses propres pièces (au moins la moitié des cases voisines) : {enf}")
print("\nPièces qui ferment les cases voisines (toutes cases comptées) :",dict(compo.most_common()))
print(f"\nParmi ces {enf} mats : au moins un Fou du Roi parmi les pièces du rempart : {fou_bloque} ({fou_bloque/enf*100:.0f} %) ; Fou en position de fianchetto (g2/b2, g7/b7) : {fou_fian} ({fou_fian/enf*100:.0f} %) ; Roi dans un coin : {coin} ({coin/enf*100:.0f} %)")
print("\nMats à l'étouffé complets :")
for f,san,occ,K in complets: print(f"   Roi en {K} | mat par {san} | rempart : {', '.join(occ)}\n      {f}")
