#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seuil_roque_v2.py -- la mesure du roque, avec pions, défenseurs et identification de la Métapièce par la CONVERGENCE.
Mêmes positions que seuil_roque.py (Roi roqué, encore sur son aile, tous les 4 demi-coups de 20 à 90 ; zone de 12 cases).
Grandeurs par position :
  A   = pièces adverses (C, F, T, D) qui attaquent au moins une case de la zone          (mesure d'origine)
  Ap  = pions adverses AVANCÉS (rangée 5+ pour les Blancs, 4- pour les Noirs) qui attaquent une case de la zone
  D   = pièces du camp du Roi (C, F, T, D) qui défendent au moins une case de la zone    (mesure d'origine)
  Dp  = pions du camp du Roi situés SUR la zone (le bouclier)
  Mc  = taille du plus grand groupe d'attaquants (pièces) reliés par une case de la zone attaquée en commun : la MÉTAPIÈCE
  Mcp = idem en y ajoutant les pions avancés
  K2  = nombre de cases de la zone attaquées par au moins DEUX attaquants (convergence)
Résultat y = l'adversaire mate dans les 10 demi-coups suivants. Intervalles de confiance : bootstrap PAR PARTIE.
USAGE : cd donnees ; python3 ../recherche/scripts/seuil_roque_v2.py"""
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
def composante_max(att):   # att : dict pièce -> ensemble de cases de la zone ; graphe : reliés si case commune
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
                att=not dfc; Z=zone(K,dfc); piece_att={}; pawn_att={}; A=set(); D=set(); Dp=0
                for sq in Z:
                    for s in b.attackers(att,sq):
                        t=b.piece_type_at(s)
                        if t in PCS: piece_att.setdefault(s,set()).add(sq)
                        elif t==chess.PAWN:
                            rk=chess.square_rank(s)
                            if (att==chess.WHITE and rk>=4) or (att==chess.BLACK and rk<=3): pawn_att.setdefault(s,set()).add(sq)
                    for s in b.attackers(dfc,sq):
                        if b.piece_type_at(s) in PCS: D.add(s)
                    p=b.piece_at(sq)
                    if p and p.color==dfc and p.piece_type==chess.PAWN: Dp+=1
                allp=dict(piece_att); allp.update(pawn_att)
                cnt={}
                for ss in piece_att.values():
                    for sq in ss: cnt[sq]=cnt.get(sq,0)+1
                K2=sum(1 for v in cnt.values() if v>=2)
                y=int(mat_par==att and 0<n-i<=10)
                rows.append((gid,len(piece_att),len(pawn_att),len(D),Dp,composante_max(piece_att),composante_max(allp),K2,y))
R=np.array(rows,dtype=int); G=R[:,0]; y=R[:,8]; ng=G.max()
print(f"{len(R)} positions, {ng} parties, {int(y.sum())} mats dans les 10 demi-coups ({time.time()-t0:.0f} s)")
A,Ap,D,Dp,Mc,Mcp,K2=R[:,1],R[:,2],R[:,3],R[:,4],R[:,5],R[:,6],R[:,7]
print(f"\nPIONS : positions avec au moins un pion adverse avancé qui attaque la zone : {100*np.mean(Ap>0):.1f} % ; bouclier (pions du Roi sur la zone) en moyenne {Dp.mean():.2f} ; défenseurs-pièces en moyenne {D.mean():.2f}")
rng=np.random.default_rng(3); B=300; W=[rng.multinomial(ng,np.ones(ng)/ng)[G-1] for _ in range(B)]
def rapport(flag,w):
    a=(w*flag).sum(); b_=(w*(~flag)).sum()
    return ((w*y*flag).sum()/a)/((w*y*(~flag)).sum()/b_)
print("\nRAPPORT DES TAUX DE MAT (positions signalées / autres), intervalle à 95 % par partie :")
V=[("A >= 3  (mesure d'origine)",A>=3),("A + pions avancés >= 3",A+Ap>=3),("Métapièce Mc >= 3 (attaquants reliés)",Mc>=3),("Métapièce avec pions Mcp >= 3",Mcp>=3),("convergence K2 >= 2 (2 cases doublement attaquées)",K2>=2),("solde A - D >= 1",A-D>=1),("solde (A+Ap) - (D+Dp) >= 1",(A+Ap)-(D+Dp)>=1)]
for nom,fl in V:
    r0=rapport(fl,np.ones(len(y))); bs=[rapport(fl,w) for w in W]; lo,hi=np.percentile(bs,[2.5,97.5])
    print(f"   {nom:52} n={fl.sum():>6}  {r0:5.1f}×  [{lo:4.1f} ; {hi:4.1f}]   taux {100*y[fl].mean():.2f} % contre {100*y[~fl].mean():.2f} %")
def auc(s,w):
    s=s-s.min(); P=np.bincount(s[y==1],weights=w[y==1],minlength=s.max()+1); N=np.bincount(s[y==0],weights=w[y==0],minlength=s.max()+1)
    cumN=np.cumsum(N)-N; return float((P*(cumN+0.5*N)).sum()/(P.sum()*N.sum()))
print("\nPOUVOIR DE DISCRIMINATION (aire sous la courbe ROC, 0,5 = hasard), intervalle à 95 % par partie :")
S=[("A (pièces attaquantes)",A),("A + Ap (avec pions avancés)",A+Ap),("Mc (Métapièce par convergence)",Mc),("Mcp (Métapièce avec pions)",Mcp),("K2 (cases doublement attaquées)",K2),("moins D (peu de défenseurs-pièces)",-D),("moins Dp (peu de pions de bouclier)",-Dp),("solde A - D",A-D),("solde (A+Ap) - (D+Dp)",(A+Ap)-(D+Dp))]
for nom,s in S:
    a0=auc(s,np.ones(len(y))); bs=[auc(s,w) for w in W]; lo,hi=np.percentile(bs,[2.5,97.5]); print(f"   {nom:40} {a0:.3f}   [{lo:.3f} ; {hi:.3f}]")
print("\nTAUX DE MAT (%) SELON LES ATTAQUANTS (A) ET LES DÉFENSEURS-PIÈCES (D), nombre de positions entre parenthèses :")
print(f"{'':10}{'D <= 1':>16}{'D = 2':>16}{'D >= 3':>16}")
for lab,fa in (("A <= 1",A<=1),("A = 2",A==2),("A >= 3",A>=3)):
    ligne=f"{lab:10}"
    for fd in (D<=1,D==2,D>=3):
        s=fa&fd; ligne+=f"{100*y[s].mean():7.2f} ({s.sum():>6})" if s.sum()>30 else f"{'-':>16}"
    print(ligne)
print("\nTAUX DE MAT (%) SELON LA PRÉSENCE D'UN PION AVANCÉ ET LE BOUCLIER, pour A >= 2 :")
for lab,s in (("pion avancé : non, bouclier >= 2",(A>=2)&(Ap==0)&(Dp>=2)),("pion avancé : non, bouclier <= 1",(A>=2)&(Ap==0)&(Dp<=1)),("pion avancé : oui, bouclier >= 2",(A>=2)&(Ap>=1)&(Dp>=2)),("pion avancé : oui, bouclier <= 1",(A>=2)&(Ap>=1)&(Dp<=1))):
    print(f"   {lab:36} {100*y[s].mean():.2f} %  (n={s.sum()})")
