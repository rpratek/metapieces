#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strategie_trajectoire.py -- la TRACE de la stratégie : la trajectoire d'une attaque apporte-t-elle plus que sa photographie ?
Mêmes positions que seuil_roque.py (Roi roqué sur son aile, tous les 4 demi-coups de 20 à 90, zone de 12 cases, mat dans les 10 demi-coups).
Photographie (M0) : A, Ap, D, Dp, K2, Mc au moment t + nombre de pièces sur l'échiquier.
Trajectoire (M1 = M0 + ) : croissance des attaquants sur 4 et 8 demi-coups, PERSISTANCE (nombre d'échantillons précédents, jusqu'à 3,
  avec au moins 2 attaquants), variation des défenseurs, variation du bouclier de pions, variation de la convergence.
Évaluation : régression logistique, validation croisée par PARTIE (5 plis), aire sous la courbe ROC sur les parties non vues.
USAGE : cd donnees ; python3 ../recherche/scripts/strategie_trajectoire.py"""
import re, io, chess, chess.pgn, numpy as np, time
t0=time.time(); PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def zone(K,col):
    f,r=chess.square_file(K),chess.square_rank(K); z=set()
    for df in (-1,0,1):
        for dr in (-1,0,1):
            ff,rr=f+df,r+dr
            if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    dr=1 if col==chess.WHITE else -1
    for df in (-1,0,1):
        ff,rr=f+df,r+2*dr
        if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    return z
def compmax(att):
    ks=list(att); seen=set(); best=0
    for k in ks:
        if k in seen: continue
        pile=[k]; seen.add(k); n=0
        while pile:
            u=pile.pop(); n+=1
            for v in ks:
                if v not in seen and att[u]&att[v]: seen.add(v); pile.append(v)
        best=max(best,n)
    return best
def snap(b,dfc):
    att=not dfc; K=b.king(dfc); Z=zone(K,dfc); pa={}; pw={}; D=set(); Dp=0
    for sq in Z:
        for s in b.attackers(att,sq):
            t=b.piece_type_at(s)
            if t in PCS: pa.setdefault(s,set()).add(sq)
            elif t==chess.PAWN:
                rk=chess.square_rank(s)
                if (att==chess.WHITE and rk>=4) or (att==chess.BLACK and rk<=3): pw.setdefault(s,set()).add(sq)
        for s in b.attackers(dfc,sq):
            if b.piece_type_at(s) in PCS: D.add(s)
        p=b.piece_at(sq)
        if p and p.color==dfc and p.piece_type==chess.PAWN: Dp+=1
    cnt={}
    for ss in pa.values():
        for sq in ss: cnt[sq]=cnt.get(sq,0)+1
    return (len(pa),len(pw),len(D),Dp,sum(1 for v in cnt.values() if v>=2),compmax(pa))
rows=[]; vus=set(); gid=0
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
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
        except Exception: continue
        if len(mv)<30: continue
        fin=g.board()
        for m in mv: fin.push(m)
        mat_par=(not fin.turn) if fin.is_checkmate() else None; n=len(mv); gid+=1
        roque={chess.WHITE:False,chess.BLACK:False}; hist={chess.WHITE:[],chess.BLACK:[]}
        for i,m in enumerate(mv,1):
            if b.is_castling(m): roque[b.turn]=True
            b.push(m)
            if i<20 or i>90 or i%4: continue
            for dfc in (chess.WHITE,chess.BLACK):
                if not roque[dfc]: hist[dfc].append(None); continue
                K=b.king(dfc); f=chess.square_file(K)
                if not (f>=5 or f<=2): hist[dfc].append(None); continue
                s=snap(b,dfc); h=hist[dfc]; hist[dfc].append(s)
                if len(h)<4 or any(x is None for x in h[-4:-1]): continue     # il faut les 3 échantillons précédents
                p1,p2,p3=h[-4+0] if False else h[-2],h[-3],h[-4]
                y=int(mat_par==(not dfc) and 0<n-i<=10)
                pers=sum(1 for x in (p1,p2,p3) if x[0]>=2)
                rows.append((gid,*s,len(b.piece_map()),s[0]-p1[0],s[0]-p2[0],pers,s[2]-p1[2],s[3]-p1[3],s[4]-p1[4],y))
R=np.array(rows,dtype=float); G=R[:,0].astype(int); y=R[:,-1]; X0=R[:,1:8]; X1=R[:,1:14]
print(f"{len(R)} positions avec trois échantillons précédents, {len(np.unique(G))} parties, {int(y.sum())} mats ({time.time()-t0:.0f} s)")
def stdz(X): return (X-X.mean(0))/(X.std(0)+1e-9)
def logit(X,y,it=300,lr=0.5,l2=1e-3):
    X=np.hstack([np.ones((len(X),1)),X]); w=np.zeros(X.shape[1])
    for _ in range(it):
        p=1/(1+np.exp(-X@w)); g=X.T@(p-y)/len(y)+l2*np.r_[0,w[1:]]; w-=lr*g
    return w
def auc(s,y):
    o=np.argsort(s,kind='mergesort'); ss=s[o]; yy=y[o]; u,inv,cnt=np.unique(ss,return_inverse=True,return_counts=True)
    cum=np.cumsum(cnt); rk=((cum-cnt)+cum+1)/2.0; r=rk[inv]; P=yy.sum(); N=len(yy)-P
    return float((r[yy==1].sum()-P*(P+1)/2)/(P*N))
rng=np.random.default_rng(11); ug=np.unique(G); rng.shuffle(ug); plis=np.array_split(ug,5)
res={'M0 photographie':[],'M1 photographie + trajectoire':[]}; W1=[]
for k in range(5):
    te=np.isin(G,plis[k]); tr=~te
    for nom,X in (('M0 photographie',X0),('M1 photographie + trajectoire',X1)):
        Z=stdz(X); w=logit(Z[tr],y[tr]); s=np.hstack([np.ones((te.sum(),1)),Z[te]])@w; res[nom].append(auc(s,y[te]))
        if nom.startswith('M1'): W1.append(w[1:])
print("\nAIRE SOUS LA COURBE ROC sur parties NON VUES (5 plis par partie) :")
for nom,v in res.items(): print(f"   {nom:32} {np.mean(v):.3f}   (écart-type des plis {np.std(v):.3f})")
dif=np.array(res['M1 photographie + trajectoire'])-np.array(res['M0 photographie'])
print(f"   gain de la trajectoire : {dif.mean():+.3f}   (plis : {', '.join(f'{d:+.3f}' for d in dif)})")
noms=['attaquants A','pions avancés Ap','défenseurs D','bouclier Dp','convergence K2','Métapièce Mc','pièces sur l\'échiquier','croissance A (4 demi-coups)','croissance A (8 demi-coups)','persistance (0 à 3)','variation de D','variation du bouclier','variation de K2']
w=np.mean(W1,axis=0); print("\nPOIDS de la régression M1 (variables centrées-réduites, signe = sens de l'effet sur le mat) :")
for nm,v in sorted(zip(noms,w),key=lambda t:-abs(t[1])): print(f"   {nm:30} {v:+.2f}")
print("\nTAUX DE MAT (%) SELON LA PERSISTANCE (échantillons précédents avec >= 2 attaquants) ET LES ATTAQUANTS ACTUELS :")
pers=R[:,10]; A=R[:,1]
for lab,fa in (("A <= 1",A<=1),("A = 2",A==2),("A >= 3",A>=3)):
    lig=f"   {lab:8}"
    for pv in (0,1,2,3):
        s=fa&(pers==pv); lig+=f"  pers={pv}: {100*y[s].mean():5.2f} % (n={int(s.sum()):>6})" if s.sum()>40 else f"  pers={pv}:   -    "
    print(lig)
