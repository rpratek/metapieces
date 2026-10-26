#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_epreuve.py -- contrôle de l'épreuve du Couple Moteur : pièces écartées (biais), saturation,
intervalles de confiance en tenant compte de la dépendance entre pièces d'une même position (bootstrap par position)."""
import sys, os, time, random, collections, chess, chess.pgn, chess.engine, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metapiece_territoire as T, couple_moteur as C
sf=sys.argv[1]; N=int(sys.argv[2]); BUD=int(sys.argv[3]) if len(sys.argv)>3 else 235; t0=time.time(); CAP=10; PROF=12
print("poids des cases (T.poids), rangées 8 -> 1 :")
for r in range(7,-1,-1): print("  ",[T.poids(chess.square(f,r)) for f in range(8)])
random.seed(7); f=open(os.environ.get('PGN','twic1637.pgn'),encoding='utf-8',errors='ignore')
eng=chess.engine.SimpleEngine.popen_uci(sf,timeout=60); eng.configure({'Threads':max(1,os.cpu_count() or 1),'Hash':128})
def ev(b): return max(-CAP,min(CAP,eng.analyse(b,chess.engine.Limit(depth=PROF))['score'].white().score(mate_score=1000)/100))
D=[]; tent=collections.Counter(); skip=collections.Counter(); skipcast=collections.Counter(); npos=0
while npos<N and time.time()-t0<BUD:
    g=chess.pgn.read_game(f)
    if g is None: break
    mv=list(g.mainline_moves())
    if len(mv)<40: continue
    b=g.board()
    for m in mv[:random.randint(16,min(70,len(mv)-2))]: b.push(m)
    if b.is_game_over(): continue
    base=ev(b); npos+=1
    for col,sq,c in C.tableau(b):
        typ=c['piece']; tent[typ]+=1
        cp=b.copy(); cp.remove_piece_at(sq); cp.castling_rights&=~chess.BB_SQUARES[sq]
        if not cp.is_valid():
            skip[typ]+=1
            if b.has_castling_rights(col): skipcast[typ]+=1
            continue
        e=ev(cp); ct=(base-e) if col==chess.WHITE else (e-base)
        c.update(pos=npos,contrib=ct,ecart=ct-c['V'],base=base,e=e,col=col); D.append(c)
eng.quit()
print(f"\n{npos} positions, {len(D)} pièces mesurées, {time.time()-t0:.0f} s")
print("\n1) PIÈCES ÉCARTÉES (position invalide après retrait) :")
for typ in ('knight','bishop','rook','queen'): print(f"   {typ:7} tentées {tent[typ]:>5}  écartées {skip[typ]:>4} ({100*skip[typ]/max(1,tent[typ]):.1f} %)  dont droits de roque encore valables : {skipcast[typ]}")
def rang(a):
    a=np.asarray(a,float); u,inv,cnt=np.unique(a,return_inverse=True,return_counts=True)
    cum=np.cumsum(cnt); avg=((cum-cnt)+cum-1)/2.0
    return avg[inv]
def sp(x,y): return float(np.corrcoef(rang(x),rang(y))[0,1])
cles=[('valeur papier V','V'),('mobilité M','M'),('brouillon V x M x B','v_brouillon'),('puissance P','P'),('P x adhérence','v_PA'),('P x A + frappe','v_PAF')]
y=np.array([d['contrib'] for d in D]); pos=np.array([d['pos'] for d in D]); X={k:np.array([d[k] for _,k in [(0,kk)]][0] if False else [d[k] for d in D]) for _,k in cles}
print("\n2) SATURATION : part des retraits dont l'évaluation atteint le plafond ±10 :",f"{100*np.mean([abs(d['e'])>=CAP for d in D]):.1f} %", "| positions de départ avec |éval| >= 6 :",f"{100*np.mean([abs(d['base'])>=6 for d in D]):.1f} % des pièces")
print("\n3) CORRÉLATIONS de rang avec l'apport réel, intervalle de confiance à 95 % (bootstrap PAR POSITION, 1 000 tirages) :")
rng=np.random.default_rng(5); upos=np.unique(pos); idx_by={p:np.where(pos==p)[0] for p in upos}
B=1000; res={k:[] for _,k in cles}; diff={'V - brouillon':[], 'V - P x A':[]}
for _ in range(B):
    ch=rng.choice(upos,len(upos)); ii=np.concatenate([idx_by[p] for p in ch]); yy=y[ii]
    r={k:sp(X[k][ii],yy) for _,k in cles}
    for k in r: res[k].append(r[k])
    diff['V - brouillon'].append(r['V']-r['v_brouillon']); diff['V - P x A'].append(r['V']-r['v_PA'])
for nom,k in cles:
    lo,hi=np.percentile(res[k],[2.5,97.5]); print(f"   {nom:22} {sp(X[k],y):+.2f}   [{lo:+.2f} ; {hi:+.2f}]")
print("   écarts appariés :")
for nom,v in diff.items():
    lo,hi=np.percentile(v,[2.5,97.5]); print(f"   {nom:22} {np.mean(v):+.2f}   [{lo:+.2f} ; {hi:+.2f}]")
print("\n4) À L'INTÉRIEUR DES TOURS (adhérence) :")
R=[i for i,d in enumerate(D) if d['piece']=='rook']; yr=y[R]; pr=pos[R]; Ar=np.array([D[i]['A'] for i in R]); ur=np.unique(pr); ib={p:np.where(pr==p)[0] for p in ur}
bs=[]
for _ in range(B):
    ch=rng.choice(ur,len(ur)); ii=np.concatenate([ib[p] for p in ch]); bs.append(sp(Ar[ii],yr[ii]))
lo,hi=np.percentile(bs,[2.5,97.5]); print(f"   n = {len(R)} tours ; corrélation adhérence - apport : {sp(Ar,yr):+.2f}   [{lo:+.2f} ; {hi:+.2f}]")
print("\n5) ROBUSTESSE : positions équilibrées seulement (|éval de départ| < 4) :")
m=np.array([abs(d['base'])<4 for d in D]); print(f"   {m.sum()} pièces")
for nom,k in cles: print(f"   {nom:22} {sp(X[k][m],y[m]):+.2f}")
