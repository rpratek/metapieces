#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flux_vs_moteur.py -- le flux acquis apporte-t-il une information que l'evaluation du moteur ne donne pas deja ?
Pour k = 10 et k = 15 coups : x_k = flux pondere (Blancs) - flux pondere (Noirs) ; e_k = evaluation Stockfish (pion, point de vue des Blancs, bornee a +-5).
Tests : (A) score ~ e_15 ; ~ e_15 + x_15 ; ~ e_15 + x_15 + dElo ;  (B) e_15 - e_10 ~ e_10 + x_10 (le flux a 10 coups prevoit-il l'evolution de l'evaluation ?).
LIMITES : echantillon de parties limite par le temps ; evaluation a faible profondeur (temps fixe) ; correlation.
USAGE : python3 flux_vs_moteur.py <chemin_stockfish> <budget_secondes>
"""
import re, io, sys, os, time, random, chess, chess.pgn, chess.engine
import numpy as np
random.seed(21)
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
BUD=float(sys.argv[2]); t0=time.time(); rows=[]
def ev(b):
    s=eng.analyse(b,chess.engine.Limit(time=0.04))['score'].white().score(mate_score=1000)/100
    return max(-5,min(5,s))
for bloc in blocs:
    if time.time()-t0>BUD: break
    r=re.search(r'\[Result "([^"]+)"\]',bloc)
    if not r or r.group(1) not in ('1-0','0-1','1/2-1/2'): continue
    y={'1-0':1.0,'0-1':0.0,'1/2-1/2':0.5}[r.group(1)]
    we=re.search(r'\[WhiteElo "(\d+)"\]',bloc); be=re.search(r'\[BlackElo "(\d+)"\]',bloc)
    de=(int(we.group(1))-int(be.group(1)))/100 if we and be else np.nan
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<40: continue
    pos={}
    for i,m in enumerate(mv[:30],1):
        b.push(m)
        if i in (20,30): pos[i]=(flux(b,chess.WHITE)-flux(b,chess.BLACK),ev(b))
    rows.append([y,de,pos[20][0],pos[20][1],pos[30][0],pos[30][1]])
eng.quit()
D=np.array(rows); y=D[:,0]; de=D[:,1]; x10,e10,x15,e15=D[:,2],D[:,3],D[:,4],D[:,5]
print(f"{len(D)} parties évaluées en {time.time()-t0:.0f} s ; avec Elo : {np.isfinite(de).sum()}\n")
def ols(X,yv):
    X=np.c_[np.ones(len(yv)),X]; b=np.linalg.lstsq(X,yv,rcond=None)[0]; res=yv-X@b
    se=np.sqrt(np.diag(np.linalg.inv(X.T@X))*res.var(ddof=X.shape[1])); r2=1-res.var()/yv.var(); return b,b/se,r2
print(f"corrélation flux(15 coups) - évaluation moteur(15 coups) : {np.corrcoef(x15,e15)[0,1]:+.3f}")
print(f"corrélation flux(15 coups) - résultat : {np.corrcoef(x15,y)[0,1]:+.3f} ; évaluation(15 coups) - résultat : {np.corrcoef(e15,y)[0,1]:+.3f}\n")
print("A. PRÉDIRE LE RÉSULTAT (score des Blancs)")
b,t,r2=ols(e15,y); print(f"   évaluation seule            : R² = {r2:.4f} | pente éval {b[1]:+.3f}")
b,t,r2b=ols(np.c_[e15,x15],y); print(f"   évaluation + flux           : R² = {r2b:.4f} | pente flux {b[2]*100:+.3f} pt/unité (t = {t[2]:+.1f}) | gain de R² = {r2b-r2:+.4f}")
M=np.isfinite(de)
b,t,r2c=ols(np.c_[e15[M],x15[M],de[M]],y[M]); print(f"   évaluation + flux + Elo     : R² = {r2c:.4f} | pente flux {b[2]*100:+.3f} (t = {t[2]:+.1f}) | pente Elo {b[3]*100:+.2f} pt/100 Elo")
print("\nB. LE FLUX À 10 COUPS PRÉVOIT-IL L'ÉVOLUTION DE L'ÉVALUATION (10 -> 15 coups) ?")
d=e15-e10
b,t,r2=ols(e10,d); print(f"   évolution ~ éval(10)        : R² = {r2:.4f} | pente éval(10) {b[1]:+.3f} (retour vers la moyenne)")
b,t,r2b=ols(np.c_[e10,x10],d); print(f"   évolution ~ éval(10) + flux(10) : R² = {r2b:.4f} | pente flux {b[2]:+.5f} pion/unité (t = {t[2]:+.1f}) | 1 écart-type de flux (={x10.std():.1f}) = {b[2]*x10.std()*100:+.1f} centipions")
print(f"\nÉcart-type de l'évaluation à 10 coups : {e10.std():.2f} pion ; à 15 coups : {e15.std():.2f} pion")
