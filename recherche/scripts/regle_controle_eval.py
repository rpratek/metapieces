#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regle_controle_eval.py -- la regle de mat apporte-t-elle une information en plus du materiel ?
Compare, a evaluation egale (Stockfish, profondeur 8, du point de vue du camp attaquant), les positions qui reunissent les
conditions (fuite <= 1, attaquants >= 3, defenseurs <= 3) a des positions temoins sans ces conditions (avantage materiel >= 3 pions),
selon la frequence d'un mat du meme camp dans les 5 coups suivants.
USAGE : python3 regle_controle_eval.py <budget_en_secondes>   (twic1637.pgn et twic1662.pgn dans le dossier courant)
LIMITES : temoins echantillonnes, appariement imparfait ; positions successives non independantes ; profondeur faible.
"""
import re, io, chess, chess.pgn, chess.engine, random, collections, time, sys
import os
random.seed(5)
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
random.shuffle(blocs); blocs=blocs[:2200]
VAL={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9}
def mat(b,col): return sum(VAL[p.piece_type]*1 for p in b.piece_map().values() if p.color==col and p.piece_type in VAL)
A=[]; N=[]
for bloc in blocs:
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<10: continue
    bb=g.board()
    for m in mv: bb.push(m)
    gag=(not bb.turn) if bb.is_checkmate() else None; mp=len(mv) if bb.is_checkmate() else None
    for i,m in enumerate(mv,1):
        b.push(m)
        if b.is_checkmate(): continue
        att=not b.turn; dfc=b.turn
        reussite=(gag==att and mp is not None and 0<mp-i<=10)
        k=b.king(dfc); z=[k]+list(b.attacks(k))
        Aa={s for sq in z for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
        Dd={s for sq in z for s in b.attackers(dfc,sq) if b.piece_type_at(s)!=chess.KING}
        if len(Aa)>=3 and len(Dd)<=3:
            b2=b.copy(); b2.turn=dfc; f=sum(1 for q in b2.legal_moves if q.from_square==k)
            if f<=1: A.append((b.fen(),att,reussite)); continue
        if mat(b,att)-mat(b,dfc)>=3 and random.random()<0.07: N.append((b.fen(),att,reussite))
print(len(A),"positions A ;",len(N),"positions témoins (avantage matériel ≥ 3, hors A)",flush=True)
eng=chess.engine.SimpleEngine.popen_uci(os.environ.get("STOCKFISH","/usr/games/stockfish")); eng.configure({"Threads":1,"Hash":64})
def ev(fen,att):
    b=chess.Board(fen); s=eng.analyse(b,chess.engine.Limit(depth=8))['score'].pov(att).score(mate_score=1000)/100; return max(-10,min(10,s))
t0=time.time(); BUD=float(sys.argv[1]); res={'A':[],'N':[]}
random.shuffle(N); 
for nom,L in (('A',A),('N',N)):
    for fen,att,r in L:
        if time.time()-t0>BUD: break
        res[nom].append((ev(fen,att),r))
eng.quit()
print(f"évalués : A {len(res['A'])}, témoins {len(res['N'])}\n")
bins=[(-10,2),(2,4),(4,6),(6,10.1)]
print(f"{'éval. du camp attaquant (pions)':32}{'groupe A : n':>14}{'mat ≤5 coups':>14}{'témoins : n':>14}{'mat ≤5 coups':>14}")
for lo,hi in bins:
    a=[r for e,r in res['A'] if lo<=e<hi]; n=[r for e,r in res['N'] if lo<=e<hi]
    pa=f"{sum(a)/len(a)*100:.1f} %" if a else "—"; pn=f"{sum(n)/len(n)*100:.1f} %" if n else "—"
    print(f"{('['+str(lo)+' ; '+str(hi if hi<10 else '+∞')+'[') if lo>-10 else '< 2':32}{len(a):14}{pa:>14}{len(n):14}{pn:>14}")
