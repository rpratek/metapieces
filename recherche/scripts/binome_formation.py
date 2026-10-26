#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
binome_formation.py -- que se passe-t-il quand un binome (batterie) vient de se former ?
Batterie = deux pieces du meme camp alignees, sans rien entre elles : Tour+Tour (meme colonne ou rangee), Dame+Tour (idem), Dame+Fou (meme diagonale).
Evenement = coup apres lequel une batterie existe qui n'existait pas avant (premiere formation de chaque paire de cases).
Mesures, du point de vue du camp qui joue : variation d'evaluation Stockfish (centipions) et variation du flux pondere du camp.
Temoins : coups de Tour / Fou / Dame du meme camp, dans la meme plage de coups, qui ne forment aucune batterie.
LIMITES : echantillon limite par le temps ; evaluation a temps court ; correlation (un joueur forme une batterie quand la position s'y prete).
USAGE : python3 binome_formation.py <chemin_stockfish> <budget_secondes>
"""
import re, io, sys, os, time, random, chess, chess.pgn, chess.engine, statistics, collections
import numpy as np
random.seed(9)
def poids(s):
    f,r=s%8,s//8
    if f in (3,4) and r in (3,4): return 4
    if 2<=f<=5 and 2<=r<=5: return 3
    if 1<=f<=6 and 1<=r<=6: return 2
    return 1
W=[poids(s) for s in range(64)]
PIECES=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def flux(b,col):
    own=b.occupied_co[col]; tot=0
    for s,p in b.piece_map().items():
        if p.color==col and p.piece_type in PIECES: tot+=sum(W[q] for q in chess.scan_forward(b.attacks_mask(s)&~own))
    return tot
def batteries(b,col):
    res={}
    P=[(s,p.piece_type) for s,p in b.piece_map().items() if p.color==col and p.piece_type in (chess.ROOK,chess.QUEEN,chess.BISHOP)]
    for i in range(len(P)):
        for j in range(i+1,len(P)):
            (a,ta),(c,tc)=P[i],P[j]
            types={ta,tc}
            fa,ra,fc,rc=a%8,a//8,c%8,c//8
            orth=(fa==fc or ra==rc); diag=(abs(fa-fc)==abs(ra-rc))
            nom=None
            if orth and types<= {chess.ROOK,chess.QUEEN}:
                nom='Tour+Tour' if types=={chess.ROOK} else ('Dame+Tour' if types=={chess.ROOK,chess.QUEEN} else None)
            elif diag and types=={chess.QUEEN,chess.BISHOP}: nom='Dame+Fou'
            if nom and not (b.occupied & chess.between(a,c)): res[frozenset((a,c))]=nom
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
eng=chess.engine.SimpleEngine.popen_uci(sys.argv[1]); eng.configure({"Threads":max(1,min(6,(os.cpu_count() or 2)//2)),"Hash":128})
BUD=float(sys.argv[2]); t0=time.time()
def ev(b,col):
    s=eng.analyse(b,chess.engine.Limit(time=0.03))['score'].pov(col).score(mate_score=1000)/100
    return max(-6,min(6,s))
EV=collections.defaultdict(list); TEM=[]; ng=0
for bloc in blocs:
    if time.time()-t0>BUD: break
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<40: continue
    ng+=1; deja={chess.WHITE:set(),chess.BLACK:set()}; formes=[]; temoins=[]
    for i,m in enumerate(mv[:60]):
        col=b.turn; t=b.piece_type_at(m.from_square)
        avant=batteries(b,col); f0=flux(b,col); b.push(m); apres=batteries(b,col)
        nouv=[(k,n) for k,n in apres.items() if k not in avant and k not in deja[col]]
        if nouv:
            for k,n in nouv: deja[col].add(k)
            formes.append((i,col,nouv[0][1]))
        elif t in (chess.ROOK,chess.BISHOP,chess.QUEEN) and 10<=i<=50: temoins.append((i,col))
        b.pop() if False else None
        # on revient en arrière pour l'évaluation plus tard : on mémorise les positions
        if nouv or (t in (chess.ROOK,chess.BISHOP,chess.QUEEN) and 10<=i<=50 and not nouv):
            pass
    # deuxième passage : évaluations sur les événements retenus (formation + 1 témoin au hasard)
    b=g.board(); ev_idx={i for i,c_,n in formes if i<50}
    tem=random.choice(temoins) if temoins else None
    if tem: ev_idx.add(tem[0])
    for i,m in enumerate(mv[:60]):
        col=b.turn
        if i in ev_idx:
            e0=ev(b,col); f0=flux(b,col); b.push(m); e1=ev(b,col); f1=flux(b,col)
            etiq=[n for ii,c_,n in formes if ii==i]
            if etiq: EV[etiq[0]].append(((e1-e0)*100,f1-f0))
            elif tem and tem[0]==i: TEM.append(((e1-e0)*100,f1-f0))
        else: b.push(m)
eng.quit()
print(f"{ng} parties ; {time.time()-t0:.0f} s\n")
print(f"{'événement':22}{'effectif':>9}{'Δ évaluation (centipions)':>28}{'Δ flux pondéré':>17}")
for n,v in EV.items():
    a=np.array(v); print(f"{'formation '+n:22}{len(v):9}{a[:,0].mean():+20.1f} ±{a[:,0].std()/np.sqrt(len(a)):4.1f}{a[:,1].mean():+17.1f}")
if TEM:
    a=np.array(TEM); print(f"{'coup témoin (R,F,D)':22}{len(a):9}{a[:,0].mean():+20.1f} ±{a[:,0].std()/np.sqrt(len(a)):4.1f}{a[:,1].mean():+17.1f}")
tout=np.array([x for v in EV.values() for x in v])
if len(tout) and TEM:
    a=np.array(TEM); d=tout[:,0].mean()-a[:,0].mean(); se=np.sqrt(tout[:,0].var()/len(tout)+a[:,0].var()/len(a))
    print(f"\nÉcart formation - témoin : {d:+.1f} centipions (erreur type {se:.1f}, t = {d/se:+.1f})")
