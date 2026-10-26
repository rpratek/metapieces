#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construction_mats.py -- comment une coalition se construit avant le mat.
Pour chaque mat : les pieces qui attaquent la zone du Roi mate ; pour chacune, l'age (en demi-coups) de sa derniere arrivee
sur sa case ; la piece arrivee en dernier ; la duree de construction (ecart entre la premiere et la derniere arrivee des pieces
qui ont bouge) selon la taille de la coalition.
LIMITES : mesure descriptive ; une piece "en place" depuis longtemps n'a pas forcement ete placee pour ce mat.
USAGE : python3 construction_mats.py   (twic1637.pgn et twic1662.pgn dans le dossier courant)
"""
import re, io, chess, chess.pgn, collections, statistics
NOM={chess.PAWN:'Pion',chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame'}
def suit(g):
    b=g.board(); arr={s:0 for s in b.piece_map()}; i=0
    for m in g.mainline_moves():
        i+=1; cap=m.to_square
        if b.is_en_passant(m): cap=chess.square(chess.square_file(m.to_square),chess.square_rank(m.from_square))
        if b.is_capture(m): arr.pop(cap,None)
        if b.is_castling(m):
            arr.pop(m.from_square,None); arr[m.to_square]=i
            r=chess.square_rank(m.to_square)
            if chess.square_file(m.to_square)==6: arr.pop(chess.square(7,r),None); arr[chess.square(5,r)]=i
            else: arr.pop(chess.square(0,r),None); arr[chess.square(3,r)]=i
        else:
            arr.pop(m.from_square,None); arr[m.to_square]=i
        b.push(m)
    return b,arr,i
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
        vus.add(cle)
        r=re.search(r'\[Result "([^"]+)"\]',bloc)
        if not r or r.group(1) not in ('1-0','0-1') or '#' not in cle: continue
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b,arr,n=suit(g)
        except Exception: continue
        if not b.is_checkmate(): continue
        dfc=b.turn; att=not dfc; k=b.king(dfc); z=[k]+list(b.attacks(k))
        A={s for sq in z for s in b.attackers(att,sq) if b.piece_type_at(s)!=chess.KING}
        if not A: continue
        ages={s:n-arr.get(s,0) for s in A}                     # âge en demi-coups (0 = arrivé au dernier coup)
        mobiles={s:a for s,a in ages.items() if arr.get(s,0)>0}
        dernier=min(ages,key=lambda s:ages[s])
        span=(max(mobiles.values())-min(mobiles.values()))/2 if len(mobiles)>=2 else 0
        rows.append(dict(n=len(A),dernier=NOM[b.piece_type_at(dernier)],age_dernier=ages[dernier],span=span,
                         vieux=sum(1 for a in ages.values() if a>=20)/len(A),mobiles=len(mobiles)))
print(len(rows),"mats analysés\n")
print("PIÈCE QUI ARRIVE EN DERNIER (celle qui a bougé le plus récemment) :")
C=collections.Counter(r['dernier'] for r in rows)
for k,v in C.most_common(): print(f"   {k:9} {v:5} ({v/len(rows)*100:4.1f} %)")
print("\nCONSTRUCTION PAR TAILLE DE COALITION (attaquants de la zone du Roi) :")
print(f"{'pièces':8}{'mats':>6}{'durée de construction (coups)':>32}{'en place depuis ≥10 coups':>27}")
for n in (1,2,3,4,5):
    R=[r for r in rows if (r['n']==n if n<5 else r['n']>=5)]
    if len(R)<5: continue
    sp=[r['span'] for r in R if r['mobiles']>=2]
    print(f"{(str(n) if n<5 else '5+'):8}{len(R):6}{(f'médiane {statistics.median(sp):.0f} ; moyenne {statistics.mean(sp):.1f}' if sp else '—'):>32}{statistics.mean(r['vieux'] for r in R)*100:26.0f} %")
ad=[r['age_dernier']/2 for r in rows]; print(f"\nâge de la dernière arrivée : médiane {statistics.median(ad):.1f} coups (0 = c'est le coup du mat)")
