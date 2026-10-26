#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syn_reelle.py -- synergie (formule du Cahier Obi) de batteries et de paires temoins, sur des positions reelles de TWIC.
Syn(A,B) = V_ref + V_sans(A,B) - V_sans(A) - V_sans(B)  (en pions, du point de vue du camp qui possede la paire ; Stockfish, temps fixe).
Batterie = deux pieces du meme camp alignees sans rien entre elles : Tour+Tour, Dame+Tour (meme colonne/rangee), Dame+Fou (meme diagonale).
Temoin = deux pieces de memes types, du meme camp, NON alignees (ou alignees avec un obstacle entre elles), prises dans d'autres positions.
Une position par partie, au hasard entre les coups 20 et 60. Valeurs bornees a +-10 pions.
LIMITES : echantillon limite par le temps ; evaluation a temps court ; la retraite d'une piece cree des positions artificielles ; le temoin n'est pas apparie a la batterie ; correlation.
USAGE : python3 syn_reelle.py <chemin_stockfish> <budget_secondes>
"""
import re, io, sys, os, time, random, chess, chess.pgn, chess.engine, statistics, collections
import numpy as np
random.seed(31)
sf=sys.argv[1]; BUD=float(sys.argv[2])
def paire_types(b,col):
    """retourne {'RR':[(a,c,aligne)],'QR':[...],'QB':[...]} pour toutes les paires de pieces concernees."""
    P=[(s,p.piece_type) for s,p in b.piece_map().items() if p.color==col and p.piece_type in (chess.ROOK,chess.QUEEN,chess.BISHOP)]
    res=collections.defaultdict(list)
    for i in range(len(P)):
        for j in range(i+1,len(P)):
            (a,ta),(c,tc)=P[i],P[j]; types={ta,tc}
            nom=None
            if types=={chess.ROOK} and ta==tc: nom='RR'
            elif types=={chess.ROOK,chess.QUEEN}: nom='QR'
            elif types=={chess.QUEEN,chess.BISHOP}: nom='QB'
            if not nom: continue
            fa,ra,fc,rc=a%8,a//8,c%8,c//8
            lie=(fa==fc or ra==rc) if nom in ('RR','QR') else (abs(fa-fc)==abs(ra-rc))
            libre=lie and not (b.occupied & chess.between(a,c))
            res[nom].append((a,c,libre))
    return res
blocs=[]; vus=set()
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
        vus.add(cle); blocs.append(bloc)
random.shuffle(blocs)
eng=chess.engine.SimpleEngine.popen_uci(sf); eng.configure({"Threads":max(1,min(6,(os.cpu_count() or 2)//2)),"Hash":128})
def ev(b,col):
    s=eng.analyse(b,chess.engine.Limit(time=0.06))['score'].pov(col).score(mate_score=1000)/100
    return max(-10,min(10,s))
def syn(b,col,a,c):
    vref=ev(b,col); vals=[]
    for retirer in ((a,c),(a,),(c,)):
        b2=b.copy()
        for s in retirer: b2.remove_piece_at(s)
        if not b2.is_valid() or b2.is_check() and False: return None
        vals.append(ev(b2,col))
    return vref+vals[0]-vals[1]-vals[2]
R={('RR','bat'):[],('RR','tem'):[],('QR','bat'):[],('QR','tem'):[],('QB','bat'):[],('QB','tem'):[]}
t0=time.time(); NMAX=120
for bloc in blocs:
    if time.time()-t0>BUD: break
    try: g=chess.pgn.read_game(io.StringIO(bloc)); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<65: continue
    k=random.randint(20,60); b=g.board()
    for m in mv[:k]: b.push(m)
    col=not b.turn; pt=paire_types(b,col)
    for nom in ('RR','QR','QB'):
        if nom not in pt: continue
        bats=[p for p in pt[nom] if p[2]]; tems=[p for p in pt[nom] if not p[2]]
        if bats and len(R[(nom,'bat')])<NMAX:
            a,c,_=random.choice(bats); s=syn(b,col,a,c)
            if s is not None: R[(nom,'bat')].append(s)
        elif tems and len(R[(nom,'tem')])<NMAX:
            a,c,_=random.choice(tems); s=syn(b,col,a,c)
            if s is not None: R[(nom,'tem')].append(s)
eng.quit()
print(f"{time.time()-t0:.0f} s\n")
NOM={'RR':'Tour + Tour','QR':'Dame + Tour','QB':'Dame + Fou'}
print(f"{'paire':14}{'groupe':14}{'n':>5}{'Syn moyenne':>14}{'médiane':>10}{'Syn ≥ 0,30':>12}")
for nom in ('RR','QR','QB'):
    for g_,lab in (('bat','alignées'),('tem','non alignées')):
        v=R[(nom,g_)]
        if len(v)>3: print(f"{NOM[nom]:14}{lab:14}{len(v):5}{np.mean(v):+9.2f} ±{np.std(v)/len(v)**0.5:4.2f}{np.median(v):+10.2f}{np.mean(np.array(v)>=0.30)*100:10.0f} %")
print()
for nom in ('RR','QR','QB'):
    a=np.array(R[(nom,'bat')]); t=np.array(R[(nom,'tem')])
    if len(a)>5 and len(t)>5:
        d=a.mean()-t.mean(); se=np.sqrt(a.var()/len(a)+t.var()/len(t)); print(f"{NOM[nom]:14} écart alignées - non alignées : {d:+.2f} pion (erreur type {se:.2f}, t = {d/se:+.1f})")
