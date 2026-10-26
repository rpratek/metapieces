#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regle_mat_test.py -- valeur predictive de la regle de mat.
Sur 5 000 parties de TWIC (tirees au hasard), pour chaque position ou le camp qui vient de jouer attaque, on compte
les cases de fuite du Roi adverse, les attaquants et les defenseurs de sa zone, puis on regarde si la partie se termine par
le mat de ce camp dans les 3 ou 5 coups suivants. Compare a la frequence de reference (toutes positions).
LIMITES : positions successives non independantes ; l'echec = pas de mat du meme camp dans l'horizon, meme si l'attaque reussit autrement.
USAGE : python3 regle_mat_test.py   (twic1637.pgn et twic1662.pgn dans le dossier courant)
"""
import re, io, chess, chess.pgn, collections, random
random.seed(5)
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
random.shuffle(blocs); blocs=blocs[:5000]
CONDS={"A  : fuite ≤ 1, attaquants ≥ 3, défenseurs ≤ 3":lambda f,a,d:f<=1 and a>=3 and d<=3,
       "B  : fuite ≤ 2, attaquants ≥ 2, défenseurs ≤ 2":lambda f,a,d:f<=2 and a>=2 and d<=2,
       "C  : attaquants > défenseurs (seul)":lambda f,a,d:a>d,
       "D  : fuite ≤ 1 (seul)":lambda f,a,d:f<=1}
H=(6,10)
tot=collections.Counter(); pos=collections.Counter(); ng=0; npos=0
for bloc in blocs:
    try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
    except Exception: continue
    if len(mv)<10: continue
    ng+=1; gagnant=None; mate_ply=None
    bb=g.board()
    for m in mv: bb.push(m)
    if bb.is_checkmate(): gagnant=not bb.turn; mate_ply=len(mv)
    for i,m in enumerate(mv,1):
        b.push(m); att=not b.turn; dfc=b.turn
        if b.is_checkmate(): continue
        npos+=1
        res={h:(gagnant==att and mate_ply is not None and 0<mate_ply-i<=h) for h in H}
        tot['tous']+=1
        for h in H: pos[('tous',h)]+=res[h]
        k=b.king(dfc); z=[k]+list(b.attacks(k))
        A={s for sq in z for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
        D={s for sq in z for s in b.attackers(dfc,sq) if b.piece_type_at(s)!=chess.KING}
        if len(A)<2 and True: 
            continue
        b2=b.copy(); b2.turn=dfc
        f=sum(1 for q in b2.legal_moves if q.from_square==k)
        for nom,fn in CONDS.items():
            if fn(f,len(A),len(D)):
                tot[nom]+=1
                for h in H: pos[(nom,h)]+=res[h]
print(ng,"parties,",npos,"positions\n")
base={h:pos[('tous',h)]/tot['tous'] for h in H}
print(f"RÉFÉRENCE (toutes positions) : mat du camp qui vient de jouer dans les 3 coups : {base[6]*100:.2f} % ; dans les 5 coups : {base[10]*100:.2f} %\n")
print(f"{'conditions':50}{'positions':>10}{'mat ≤ 3 coups':>15}{'gain':>7}{'mat ≤ 5 coups':>15}{'gain':>7}")
for nom in CONDS:
    n=tot[nom]
    if n==0: continue
    p6=pos[(nom,6)]/n; p10=pos[(nom,10)]/n
    print(f"{nom:50}{n:10}{p6*100:14.1f}%{p6/base[6]:6.0f}×{p10*100:14.1f}%{p10/base[10]:6.0f}×")
