#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roques_config.py -- les reperes changent-ils avec la configuration de roque ?
Classe chaque partie (20 coups ou plus) : petit roque des deux cotes (PP), roques opposes (OPP), grand roque des deux cotes (CC),
ou au moins un Roi non roque. Puis, par configuration : duree, taux de mats, cohesion et tension selon le nombre de pieces,
Roi au mat, taille de la coalition, aile du Roi mate.
LIMITE : la configuration n'est connue qu'a la fin de la partie (on classe les parties qui FINISSENT ainsi).
USAGE : python3 roques_config.py   (twic1637.pgn et twic1662.pgn dans le dossier courant)
"""
import re, io, sys, statistics, collections
import chess, chess.pgn
sys.path.insert(0,'.')
import detecteur_metapieces as D
BINS=[(28,32),(24,27),(20,23),(16,19),(12,15),(8,11),(0,7)]
def tr(n):
    for a,b in BINS:
        if a<=n<=b: return (a,b)
def config(mv,b0):
    b=b0.copy(); r={True:None,False:None}; ply={True:None,False:None}
    for i,m in enumerate(mv):
        if b.is_castling(m):
            r[b.turn]='c' if chess.square_file(m.to_square)==2 else 'p'; ply[b.turn]=i
        b.push(m)
    if r[True] and r[False]:
        if r[True]==r[False]: return ('CC' if r[True]=='c' else 'PP')
        return 'OPP'
    return 'incomplet'
def liens(b):
    pm=b.piece_map(); n=len(pm); a=e=0
    for sq,p in pm.items():
        for t in b.attacks(sq):
            q=pm.get(t)
            if q is None: continue
            if q.color==p.color: a+=1
            else: e+=1
    return n,a,e
nbg=collections.Counter(); coh=collections.defaultdict(list); ten=collections.defaultdict(list)
mats=collections.defaultdict(list); longueur=collections.defaultdict(list); vus=set()
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
        if len(mv)<20: continue
        cf=config(mv,g.board()); nbg[cf]+=1; longueur[cf].append(len(mv)//2)
        b=g.board()
        for i,m in enumerate(mv):
            b.push(m)
            if i%4==3 and cf in ('PP','OPP','CC'):
                n,a,e=liens(b); k=tr(n); coh[(cf,k)].append(a/n); ten[(cf,k)].append(e/n)
        if b.is_checkmate():
            t=D.pieces_contributrices(b); cat,nn=D.classer(t); ff=chess.square_file(b.king(b.turn))
            mats[cf].append((len(t),'K' in t,len(b.piece_map()),'Q' if ff<=2 else ('K' if ff>=5 else 'C')))
tot=sum(nbg.values())
print("CONFIGURATIONS DE ROQUE (parties de 20 coups ou plus) :")
for cf,lab in (('PP','petit roque des deux côtés'),('OPP','roques opposés'),('CC','grand roque des deux côtés'),('incomplet','au moins un Roi non roqué')):
    L=longueur[cf]; print(f"  {lab:34} {nbg[cf]:5} ({nbg[cf]/tot*100:4.1f} %) | durée médiane {statistics.median(L):.0f} coups | mats : {len(mats[cf]):4} ({len(mats[cf])/nbg[cf]*1000:5.1f} pour 1000 parties)")
print("\nCOHÉSION / TENSION par configuration et nombre de pièces (positions échantillonnées) :")
print(f"{'pièces':10}"+''.join(f"{cf:>26}" for cf in ('PP','OPP','CC')))
for a,b in BINS:
    row=f"{(str(a)+'-'+str(b)):10}"
    for cf in ('PP','OPP','CC'):
        L=coh.get((cf,(a,b)),[]); T=ten.get((cf,(a,b)),[])
        row+=f"{(f'{statistics.mean(L):.2f} / {statistics.mean(T):.2f} (n={len(L)})' if len(L)>30 else '—'):>26}"
    print(row)
print("\nMATS par configuration :")
print(f"{'':30}{'mats':>6}{'Roi coopère':>13}{'coalition ≥4':>14}{'coalition ≥5':>14}{'pièces au mat (méd.)':>22}{'Roi maté aile Roi':>19}{'aile Dame':>11}")
for cf,lab in (('PP','petit-petit'),('OPP','roques opposés'),('CC','grand-grand')):
    M=mats[cf]
    if len(M)<20: print(f"{lab:30}{len(M):6}  (trop peu)"); continue
    print(f"{lab:30}{len(M):6}{sum(1 for m in M if m[1])/len(M)*100:12.1f}%{sum(1 for m in M if m[0]>=4)/len(M)*100:13.1f}%{sum(1 for m in M if m[0]>=5)/len(M)*100:13.1f}%{statistics.median([m[2] for m in M]):22.0f}{sum(1 for m in M if m[3]=='K')/len(M)*100:18.1f}%{sum(1 for m in M if m[3]=='Q')/len(M)*100:10.1f}%")
