#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approche_mat.py -- profil d'approche du mat : fuites du Roi, attaquants et defenseurs de sa zone,
du 14e demi-coup avant le mat jusqu'au mat (moyennes sur tous les mats des archives TWIC).
Zone du Roi = sa case + les cases adjacentes. Attaquants/defenseurs = pieces (hors Rois) qui attaquent la zone.
USAGE : python3 approche_mat.py     (twic1637.pgn et twic1662.pgn dans le dossier courant)
"""
import re, io, chess, chess.pgn, collections, statistics
K=14
def mes(b,att,dfc):
    k=b.king(dfc); b2=b.copy(); b2.turn=dfc
    try: fu=sum(1 for m in b2.legal_moves if m.from_square==k)
    except Exception: return None
    z=[k]+list(b.attacks(k))
    A={s for sq in z for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
    D={s for sq in z for s in b.attackers(dfc,sq) if b.piece_type_at(s)!=chess.KING}
    return fu,len(A),len(D)
prof=collections.defaultdict(lambda:[[],[],[]]); vus=set(); n=0
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
        dfc=pos[-1].turn; att=not dfc; n+=1
        for k in range(K+1):
            v=mes(pos[-1-k],att,dfc)
            if v:
                for j in range(3): prof[k][j].append(v[j])
print(n,"mats analyses")
print(f"{'demi-coups avant le mat':25}{'fuites':>8}{'attaquants':>12}{'defenseurs':>12}")
for k in (14,12,10,8,6,5,4,3,2,1,0):
    P=prof[k]; print(f"{('mat' if k==0 else k):25}{statistics.mean(P[0]):8.2f}{statistics.mean(P[1]):12.2f}{statistics.mean(P[2]):12.2f}")
