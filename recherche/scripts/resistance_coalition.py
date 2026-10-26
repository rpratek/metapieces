#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resistance_coalition.py -- la taille de la coalition qui mate s'ajuste-t-elle à la RÉSISTANCE de la défense ?
Pour chaque mat (TWIC 1637 et 1662) : C = attaquants de la zone du Roi mat AU MOMENT DU MAT ; résistance mesurée 14 demi-coups avant :
D14 = défenseurs de la zone, F14 = fuites du Roi, P14 = pièces sur l'échiquier (proxy de la complexité). Zone = case du Roi + cases adjacentes (comme approche_mat.py).
LIMITES : seuls les mats RÉUSSIS sont observés (biais de survie) ; coalition comptée à l'arrivée ; corrélations.
USAGE : cd donnees ; python3 ../recherche/scripts/resistance_coalition.py"""
import re, io, chess, chess.pgn, numpy as np, time
t0=time.time(); K=14
def mes(b,att,dfc):
    k=b.king(dfc); b2=b.copy(); b2.turn=dfc
    try: fu=sum(1 for m in b2.legal_moves if m.from_square==k)
    except Exception: return None
    z=[k]+list(b.attacks(k))
    A={s for sq in z for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
    D={s for sq in z for s in b.attackers(dfc,sq) if b.piece_type_at(s)!=chess.KING}
    return fu,len(A),len(D)
rows=[]; vus=set()
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
        try:
            g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); pos=[]
            for m in g.mainline_moves(): b.push(m); pos.append(b.copy())
        except Exception: continue
        if not pos or not pos[-1].is_checkmate() or len(pos)<K+2: continue
        dfc=pos[-1].turn; att=not dfc
        m0=mes(pos[-1],att,dfc); m14=mes(pos[-1-K],att,dfc); m10=mes(pos[-1-10],att,dfc)
        if not(m0 and m14 and m10): continue
        rows.append((m0[1],m14[2],m14[0],m10[2],m10[0],len(pos[-1-K].piece_map()),m14[1]))
R=np.array(rows,float); C,D14,F14,D10,F10,P14,A14=R.T
print(f"{len(R)} mats analysés ({time.time()-t0:.0f} s)")
def rang(a):
    u,inv,cnt=np.unique(a,return_inverse=True,return_counts=True); cum=np.cumsum(cnt); return (((cum-cnt)+cum-1)/2.0)[inv]
def sp(x,y): return float(np.corrcoef(rang(x),rang(y))[0,1])
rng=np.random.default_rng(2)
def ci(x,y):
    b=[]; n=len(x)
    for _ in range(500):
        i=rng.integers(0,n,n); b.append(sp(x[i],y[i]))
    return np.percentile(b,[2.5,97.5])
print("\nCORRÉLATION de rang entre la TAILLE DE LA COALITION AU MAT et la résistance 14 demi-coups avant (IC 95 %) :")
for nom,v in (("défenseurs de la zone (D14)",D14),("fuites du Roi (F14)",F14),("pièces sur l'échiquier (P14)",P14),("attaquants déjà présents (A14)",A14)):
    lo,hi=ci(v,C); print(f"   {nom:34} {sp(v,C):+.2f}   [{lo:+.2f} ; {hi:+.2f}]")
print("\nCOALITION AU MAT SELON LES DÉFENSEURS 14 DEMI-COUPS AVANT :")
print(f"   {'défenseurs':14}{'mats':>6}{'coalition moyenne':>20}{'coalition >= 3':>16}{'>= 4':>8}")
for lab,s in (("0 ou 1",D14<=1),("2",D14==2),("3",D14==3),("4 ou plus",D14>=4)):
    if s.sum()>15: print(f"   {lab:14}{int(s.sum()):>6}{C[s].mean():>20.2f}{100*np.mean(C[s]>=3):>14.0f} %{100*np.mean(C[s]>=4):>6.0f} %")
print("\nMÊME QUESTION À COMPLEXITÉ ÉGALE (pièces sur l'échiquier 14 demi-coups avant) :")
for lab,sp_ in (("≥ 26 pièces",P14>=26),("18 à 25",(P14>=18)&(P14<26)),("≤ 17",P14<18)):
    if sp_.sum()>40:
        lo=sp_&(D14<=2); hi=sp_&(D14>=3)
        print(f"   {lab:12} défense <= 2 : coalition {C[lo].mean():.2f} (n={int(lo.sum())}) | défense >= 3 : {C[hi].mean():.2f} (n={int(hi.sum())})")
print("\nFUITES 14 DEMI-COUPS AVANT (marge de manœuvre du Roi) :")
for lab,s in (("0 à 2 fuites",F14<=2),("3 fuites",F14==3),("4 fuites ou plus",F14>=4)):
    if s.sum()>15: print(f"   {lab:18}{int(s.sum()):>6} mats   coalition moyenne {C[s].mean():.2f}   >= 3 : {100*np.mean(C[s]>=3):.0f} %")
