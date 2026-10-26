#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regimes_pieces.py -- les "regimes" d'une partie selon le nombre de pieces restantes.

Mesure, par tranche de nombre de pieces sur l'echiquier :
  - la COOPERATION : nombre moyen, par piece, de pieces amies qu'elle defend ;
  - la TENSION     : nombre moyen, par piece, de pieces adverses qu'elle attaque
    (echantillon : une position sur trois dans les 3 500 premieres parties) ;
  - le ROI AU MAT  : part des mats ou le Roi coopere, par tranche (toutes les parties).
USAGE : python3 regimes_pieces.py   (les fichiers twic1637.pgn et twic1662.pgn dans le dossier courant)
LIMITES : le nombre de liens par piece depend aussi de l'encombrement de l'echiquier ;
          le Roi au mat ne concerne que les parties finies par un mat ; une correlation n'est pas une cause.
"""
import re, io, sys, collections, statistics
import chess, chess.pgn
sys.path.insert(0,'.')
import detecteur_metapieces as D
BINS=[(28,32,"28-32 pièces"),(24,27,"24-27"),(20,23,"20-23"),(16,19,"16-19"),(12,15,"12-15"),(8,11,"8-11"),(0,7,"≤ 7")]
def tranche(n):
    for a,b,nom in BINS:
        if a<=n<=b: return nom
# --- (1) Le Roi coopère-t-il au mat, selon le matériel restant ? + (2) densité de liens dans toutes les positions
roi=collections.defaultdict(lambda:[0,0]); amis=collections.defaultdict(list); ennemis=collections.defaultdict(list); vus=set(); ng=0
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
        try: g=chess.pgn.read_game(io.StringIO(bloc)); mv=list(g.mainline_moves())
        except Exception: continue
        b=g.board(); ng+=1
        for i,m in enumerate(mv):
            b.push(m)
            if ng<=3500 and i%3==2:                     # échantillon : 1 position sur 3, 3 500 premières parties
                pm=b.piece_map(); n=len(pm)
                if n<3: continue
                a=e=0
                for sq,p in pm.items():
                    for t in b.attacks(sq):
                        q=pm.get(t)
                        if q is None: continue
                        if q.color==p.color: a+=1
                        else: e+=1
                nom=tranche(n); amis[nom].append(a/n); ennemis[nom].append(e/n)
        if b.is_checkmate():
            nom=tranche(len(b.piece_map())); roi[nom][1]+=1
            if 'K' in D.pieces_contributrices(b): roi[nom][0]+=1
print(ng,"parties lues\n")
print(f"{'pièces sur l échiquier':24}{'positions':>10}{'liens de coopération / pièce':>30}{'liens de tension / pièce':>26}")
for a,b_,nom in BINS:
    if nom in amis: print(f"{nom:24}{len(amis[nom]):10}{statistics.mean(amis[nom]):30.2f}{statistics.mean(ennemis[nom]):26.2f}")
print("\nLe Roi coopère au mat (selon le matériel restant) :")
for a,b_,nom in BINS:
    if nom in roi and roi[nom][1]: print(f"   {nom:16} : {roi[nom][0]:4}/{roi[nom][1]:4} = {roi[nom][0]/roi[nom][1]*100:4.1f} %")
