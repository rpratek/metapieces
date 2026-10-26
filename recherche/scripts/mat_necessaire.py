import re, io, chess, chess.pgn, numpy as np, collections
rows=[]; vus=set(); types=collections.Counter()
NOM={chess.PAWN:'P',chess.KNIGHT:'C',chess.BISHOP:'F',chess.ROOK:'T',chess.QUEEN:'D'}
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
        dfc=b.turn; att=not dfc; ess=[]
        for sq,p in b.piece_map().items():
            if p.color==att and p.piece_type!=chess.KING:
                b2=b.copy(); b2.remove_piece_at(sq)
                if not b2.is_checkmate(): ess.append(NOM[p.piece_type])
        rows.append((int(roque[dfc]),len(ess))); 
        if len(ess)<=3: types[''.join(sorted(ess))]+=1
R=np.array(rows)
def bloc(lab,S):
    n=len(S); e=S[:,1]
    print(f"{lab} : {n} mats")
    for lab2,s in (("une seule pièce nécessaire (Monôme)",e==1),("deux pièces nécessaires (Binôme)",e==2),("trois pièces nécessaires (Trinôme)",e==3),("quatre pièces ou plus",e>=4)):
        print(f"   {lab2:40} {int(s.sum()):>5}  ({100*s.mean():4.1f} %)")
    print(f"   => deux pièces nécessaires ou plus (Métapièce) : {100*np.mean(e>=2):4.1f} %   | médiane {np.median(e):.0f} | moyenne {e.mean():.2f}")
bloc("TOUS LES MATS",R); print(); bloc("CONTRE UN ROI ROQUÉ",R[R[:,0]==1]); print(); bloc("CONTRE UN ROI NON ROQUÉ",R[R[:,0]==0])
print("\nCOMPOSITIONS LES PLUS FRÉQUENTES (pièces nécessaires, trois au plus) :")
for k,v in types.most_common(10): print(f"   {k or '(aucune)':6} {v:5}")
