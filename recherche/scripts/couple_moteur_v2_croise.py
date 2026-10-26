import re, io, chess, chess.pgn, numpy as np
# frontière entre les parties du TWIC 1637 et du TWIC 1662 (mêmes filtres que couple_moteur_v2.py)
vus=set(); gid=0; frontiere=None
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
        if len(mv)<30: continue
        gid+=1
    if frontiere is None: frontiere=gid
R=np.load('couple_v2_donnees.npy'); G=R[:,0].astype(int); y=R[:,-1]; X=R[:,1:11]
print("parties TWIC 1637 :",frontiere," | TWIC 1662 :",gid-frontiere)
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
M2=((X[:,[0]]+X[:,[1]])-(X[:,[6]]+X[:,[7]]))
M3=np.column_stack([X[:,0]+X[:,1],X[:,2],X[:,3],X[:,4],X[:,5],X[:,6]+X[:,7],X[:,8]])
a=G<=frontiere; b=~a
print(f"positions : 1637 = {int(a.sum())} ({int(y[a].sum())} mats) ; 1662 = {int(b.sum())} ({int(y[b].sum())} mats)")
for nom,Z in (("M2 solde avec pions",M2),("M3 Couple Moteur",M3)):
    out=[]
    for tr,te,lab in ((a,b,"entraîné sur 1637, testé sur 1662"),(b,a,"entraîné sur 1662, testé sur 1637")):
        Zs,mu,sd=std(Z[tr]); w=logit(Zs,y[tr]); s=np.hstack([np.ones((te.sum(),1)),std(Z[te],mu,sd)[0]])@w; out.append((lab,auc(s,y[te])))
    print(f"   {nom:24}", " | ".join(f"{l} : {v:.3f}" for l,v in out))
