import re, io, chess, chess.pgn, numpy as np
PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
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
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); roque={chess.WHITE:False,chess.BLACK:False}
        except Exception: continue
        for m in g.mainline_moves():
            if b.is_castling(m): roque[b.turn]=True
            b.push(m)
        if not b.is_checkmate(): continue
        dfc=b.turn; att=not dfc; K=b.king(dfc); z=[K]+list(b.attacks(K)); pa={}
        for sq in z:
            for s in b.attackers(att,sq):
                if b.piece_type_at(s) in PCS: pa.setdefault(s,set()).add(sq)
        rows.append((roque[dfc],len(pa),compmax(pa) if pa else 0))
R=np.array(rows,int)
def rapport(lab,S):
    n=len(S)
    if n==0: return
    a=S[:,1]; m=S[:,2]
    print(f"{lab} : {n} mats")
    print(f"   aucune pièce attaquante (pions ou Roi seuls) : {100*np.mean(a==0):4.1f} %")
    print(f"   une seule pièce (Monôme)                    : {100*np.mean(a==1):4.1f} %")
    print(f"   deux pièces ou plus, AUCUNE paire reliée      : {100*np.mean((a>=2)&(m==1)):4.1f} %")
    print(f"   un groupe relié de deux pièces (Binôme)      : {100*np.mean(m==2):4.1f} %")
    print(f"   un groupe relié de trois pièces ou plus      : {100*np.mean(m>=3):4.1f} %")
    print(f"   => au moins un groupe relié (Métapièce)      : {100*np.mean(m>=2):4.1f} %")
rapport("TOUS LES MATS",R); print(); rapport("MATS CONTRE UN ROI ROQUÉ",R[R[:,0]==1]); print(); rapport("MATS CONTRE UN ROI NON ROQUÉ",R[R[:,0]==0])
