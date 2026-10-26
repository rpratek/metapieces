#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
couple_moteur_v2.py -- COUPLE MOTEUR DE LA MÉTAPIÈCE (et non d'une pièce isolée), validé sur des parties NON VUES.
Positions : Roi roqué sur son aile, tous les 4 demi-coups de 20 à 90 (TWIC 1637 et 1662), zone du Roi de 12 cases.
Grandeurs de l'attaque : A pièces attaquantes (C,F,T,D) ; Ap pions avancés attaquants ; K2 cases de la zone attaquées par au moins deux pièces (convergence) ;
  Mc plus grand groupe d'attaquants reliés ; L attaquants lourds (Dame, Tour) ; Q présence de la Dame.
Grandeurs de la résistance : D défenseurs-pièces ; Dp pions du bouclier ; F fuites libres du Roi (cases voisines ni occupées par ses pièces ni attaquées).
Résultat : mat dans les 10 demi-coups. Évaluation : régression logistique, validation croisée par PARTIE (5 plis), aire sous la courbe ROC.
USAGE : cd donnees ; python3 ../recherche/scripts/couple_moteur_v2.py"""
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
        roque={chess.WHITE:False,chess.BLACK:False}
        for i,m in enumerate(mv,1):
            if b.is_castling(m): roque[b.turn]=True
            b.push(m)
            if i<20 or i>90 or i%4: continue
            for dfc in (chess.WHITE,chess.BLACK):
                if not roque[dfc]: continue
                K=b.king(dfc); f=chess.square_file(K)
                if not (f>=5 or f<=2): continue
                att=not dfc; Z=zone(K,dfc); pa={}; pw=set(); D=set(); Dp=0; heavy=0; hq=0
                for sq in Z:
                    for s in b.attackers(att,sq):
                        t=b.piece_type_at(s)
                        if t in PCS: pa.setdefault(s,set()).add(sq)
                        elif t==chess.PAWN:
                            rk=chess.square_rank(s)
                            if (att==chess.WHITE and rk>=4) or (att==chess.BLACK and rk<=3): pw.add(s)
                    for s in b.attackers(dfc,sq):
                        if b.piece_type_at(s) in PCS: D.add(s)
                    p=b.piece_at(sq)
                    if p and p.color==dfc and p.piece_type==chess.PAWN: Dp+=1
                for s in pa:
                    t=b.piece_type_at(s)
                    if t in (chess.ROOK,chess.QUEEN): heavy+=1
                    if t==chess.QUEEN: hq=1
                cnt={}
                for ss in pa.values():
                    for sq in ss: cnt[sq]=cnt.get(sq,0)+1
                K2=sum(1 for v in cnt.values() if v>=2)
                b2=b.copy(); b2.remove_piece_at(K); F=0
                for s in chess.SquareSet(chess.BB_KING_ATTACKS[K]):
                    pc=b.piece_at(s)
                    if pc and pc.color==dfc: continue
                    if not b2.is_attacked_by(att,s): F+=1
                y=int(mat_par==att and 0<n-i<=10)
                rows.append((gid,len(pa),len(pw),K2,compmax(pa) if pa else 0,heavy,hq,len(D),Dp,F,len(b.piece_map()),y))
R=np.array(rows,float); np.save('couple_v2_donnees.npy',R)
G=R[:,0].astype(int); y=R[:,-1]; print(f"{len(R)} positions, {len(np.unique(G))} parties, {int(y.sum())} mats ({time.time()-t0:.0f} s)")
noms=['A','Ap','K2','Mc','L','Q','D','Dp','F','pieces']; X=R[:,1:11]
def auc(s,yy):
    u,inv,cnt=np.unique(s,return_inverse=True,return_counts=True); cum=np.cumsum(cnt); rk=(((cum-cnt)+cum+1)/2.0)[inv]; P=yy.sum(); N=len(yy)-P
    return float((rk[yy==1].sum()-P*(P+1)/2)/(P*N))
def logit(Z,yy,l2=1.0,it=12):
    Z1=np.hstack([np.ones((len(Z),1)),Z]); w=np.zeros(Z1.shape[1])
    for _ in range(it):
        p=1/(1+np.exp(-np.clip(Z1@w,-30,30))); Wd=p*(1-p)+1e-9
        H=(Z1*Wd[:,None]).T@Z1+l2*np.eye(len(w)); gr=Z1.T@(p-yy)+l2*np.r_[0,w[1:]]; w-=np.linalg.solve(H,gr)
    return w
def std(Z,mu=None,sd=None):
    mu=Z.mean(0) if mu is None else mu; sd=Z.std(0)+1e-9 if sd is None else sd; return (Z-mu)/sd,mu,sd
modeles={
 "M0  attaquants seuls (A)":[0],
 "M1  solde pièces (A - D)":'solde1',
 "M2  solde avec pions (A+Ap) - (D+Dp)":'solde2',
 "M3  Couple Moteur : pression convergente - résistance [A+Ap, K2, Mc, L, Q, D+Dp, F]":'cm',
 "M4  complet (les 10 grandeurs)":list(range(10))}
def design(nom,cols):
    if cols=='solde1': return (X[:,[0]]-X[:,[6]])
    if cols=='solde2': return ((X[:,[0]]+X[:,[1]])-(X[:,[6]]+X[:,[7]]))
    if cols=='cm': return np.column_stack([X[:,0]+X[:,1],X[:,2],X[:,3],X[:,4],X[:,5],X[:,6]+X[:,7],X[:,8]])
    return X[:,cols]
rng=np.random.default_rng(21); ug=np.unique(G); rng.shuffle(ug); plis=np.array_split(ug,5)
print("\nAIRE SOUS LA COURBE ROC sur parties NON VUES (5 plis par partie) :")
res={}
for nom,cols in modeles.items():
    Z=design(nom,cols); sc=[]
    for k in range(5):
        te=np.isin(G,plis[k]); tr=~te; Zs,mu,sd=std(Z[tr]); w=logit(Zs,y[tr]); s=np.hstack([np.ones((te.sum(),1)),std(Z[te],mu,sd)[0]])@w; sc.append(auc(s,y[te]))
    res[nom]=sc; print(f"   {nom[:92]:94}{np.mean(sc):.3f}  (± {np.std(sc):.3f})")
# modèle retenu : M3, coefficients en unités d'attaquant
Z=design('cm','cm'); Zs,mu,sd=std(Z); w=logit(Zs,y)
coef=w[1:]/sd; b0=w[0]-np.sum(w[1:]*mu/sd)
lab=['pression : attaquants (pièces + pions avancés)','convergence : cases doublement attaquées (K2)','Métapièce : plus grand groupe relié (Mc)','attaquants lourds (Dame, Tour)','présence de la Dame','résistance : défenseurs (pièces + bouclier)','fuites libres du Roi']
print("\nCOUPE MOTEUR (M3), COEFFICIENTS en unités de log-cotes (par unité de chaque grandeur) :")
for l,c in zip(lab,coef): print(f"   {l:50} {c:+.2f}")
print(f"   constante {b0:+.2f}")
score=Z@coef+b0; p=1/(1+np.exp(-score))
print("\nCALIBRATION (parties vues + non vues confondues, indicatif) : taux de mat observé par tranche de score")
qs=np.quantile(score,[0.5,0.8,0.9,0.95,0.98,0.995]); edges=[-1e9]+list(qs)+[1e9]
for a,b_ in zip(edges[:-1],edges[1:]):
    m=(score>a)&(score<=b_); print(f"   score {max(a,score.min()):6.2f} à {min(b_,score.max()):6.2f} : prévu {100*p[m].mean():5.2f} %  observé {100*y[m].mean():5.2f} %  (n = {int(m.sum())})")
