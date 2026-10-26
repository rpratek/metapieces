#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synergie_paires.py -- le tout vaut-il plus (ou moins) que la somme des parties ?
Pour des paires de pieces d'un meme camp : synergie = apport(retrait des DEUX) - apport(retrait de A) - apport(retrait de B), en pions (Stockfish).
J = part ponderee du territoire commun aux deux pieces (0 = territoires disjoints, 1 = identiques).
USAGE : python3 synergie_paires.py <stockfish> [nb_positions]"""
import sys, os, time, random, itertools, collections, statistics as st, chess, chess.pgn, chess.engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metapiece_territoire as T
sf=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 300
random.seed(11); t0=time.time(); prof=12
eng=chess.engine.SimpleEngine.popen_uci(sf); eng.configure({'Threads':4,'Hash':128})
CAP=10
def ev(b):
    s=eng.analyse(b,chess.engine.Limit(depth=prof))['score'].white().score(mate_score=1000)/100
    return max(-CAP,min(CAP,s))
def sans(b,sqs):
    c=b.copy()
    for s in sqs: c.remove_piece_at(s)
    return c if c.is_valid() else None
f=open(os.environ.get('PGN','twic1637.pgn'),encoding='utf-8',errors='ignore'); L=[]; npos=0
while npos<N and time.time()-t0<250:
    g=chess.pgn.read_game(f)
    if g is None: break
    mv=list(g.mainline_moves())
    if len(mv)<40: continue
    b=g.board()
    for m in mv[:random.randint(16,min(70,len(mv)-2))]: b.push(m)
    if b.is_game_over(): continue
    base=ev(b)
    if abs(base)>6: continue
    npos+=1
    for col in (chess.WHITE,chess.BLACK):
        A=T.attaques_pieces(b,col); pcs=[(s,t,att) for s,(t,att) in A.items() if t!=chess.PAWN]
        indiv={}
        for s,t,att in pcs:
            c=sans(b,[s])
            if c is None: continue
            e=ev(c); indiv[s]=(base-e) if col==chess.WHITE else (e-base)
            indiv[s]=(indiv[s],e)
        paires=[p for p in itertools.combinations([x for x in pcs if x[0] in indiv],2)]
        random.shuffle(paires)
        for (s1,t1,a1),(s2,t2,a2) in paires[:5]:
            c=sans(b,[s1,s2])
            if c is None: continue
            e=ev(c)
            if abs(e)>=CAP or abs(indiv[s1][1])>=CAP or abs(indiv[s2][1])>=CAP: continue
            cp=(base-e) if col==chess.WHITE else (e-base)
            syn=cp-indiv[s1][0]-indiv[s2][0]
            own=b.occupied_co[col]
            T1={x for x in a1 if not (own>>x)&1}; T2={x for x in a2 if not (own>>x)&1}
            w=lambda S: sum(T.poids(x) for x in S)
            J=w(T1&T2)/w(T1|T2) if (T1|T2) else 0.0
            L.append((J,syn,sorted([chess.piece_name(t1),chess.piece_name(t2)]),indiv[s1][0]+indiv[s2][0],cp))
eng.quit()
print(f"{npos} positions, {len(L)} paires mesurees en {time.time()-t0:.0f} s (positions equilibrees, |eval| <= 6)")
syn=[x[1] for x in L]
print(f"synergie moyenne sur toutes les paires : {st.mean(syn):+.2f} pion (ecart-type {st.pstdev(syn):.2f}, erreur type {st.pstdev(syn)/len(syn)**.5:.2f})")
print("\nSynergie selon le degre d'engrenage J (part de territoire commun) :")
bandes=[(0,0.001,'territoires disjoints (J = 0)'),(0.001,0.15,'engrenage faible (0 < J <= 0,15)'),(0.15,0.35,'engrenage moyen (0,15 < J <= 0,35)'),(0.35,1.01,'engrenage fort (J > 0,35)')]
for a,b_,nom in bandes:
    S=[x[1] for x in L if a<=x[0]<b_]
    if len(S)>=15: print(f"  {nom:38} n={len(S):>4}  synergie moyenne {st.mean(S):+.2f}  (erreur type {st.pstdev(S)/len(S)**.5:.2f})")
import numpy as np
def rang(a):
    a=np.asarray(a,float); o=a.argsort(); r=np.empty(len(a)); r[o]=np.arange(len(a))
    for v in np.unique(a): r[a==v]=r[a==v].mean()
    return r
print(f"\ncorrelation de rang (Spearman) entre J et la synergie : {float(np.corrcoef(rang([x[0] for x in L]),rang(syn))[0,1]):+.3f}")
print("\nPar type de paire (synergie moyenne, au moins 25 paires) :")
tp=collections.defaultdict(list)
for J,s,typ,_,_ in L: tp['+'.join(typ)].append(s)
for k,v in sorted(tp.items(),key=lambda kv:-st.mean(kv[1])):
    if len(v)>=25: print(f"  {k:18} n={len(v):>4}  {st.mean(v):+.2f}")
