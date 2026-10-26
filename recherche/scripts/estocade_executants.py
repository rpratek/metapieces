#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estocade_executants.py -- QUI FAIT L'ESTOCADE ? Pour chaque mat réel (TWIC 1637 et 1662) :
  pièces NÉCESSAIRES = pièces ou pions de l'attaquant dont la suppression fait disparaître le mat (Métapièce par nécessité) ;
  EXÉCUTANT = la pièce déplacée au dernier coup (celle qui donne le mat), sauf mat à la découverte ;
  SOUTIEN = les autres pièces nécessaires.
USAGE : cd donnees ; python3 ../recherche/scripts/estocade_executants.py"""
import re, io, chess, chess.pgn, collections
NOM={chess.PAWN:'Pion',chess.KNIGHT:'Cavalier',chess.BISHOP:'Fou',chess.ROOK:'Tour',chess.QUEEN:'Dame'}
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
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board(); mv=list(g.mainline_moves())
        except Exception: continue
        if not mv: continue
        for m in mv[:-1]: b.push(m)
        dernier=mv[-1]; b.push(dernier)
        if not b.is_checkmate(): continue
        dfc=b.turn; att=not dfc; dest=dernier.to_square
        ess={}
        for sq,p in b.piece_map().items():
            if p.color==att and p.piece_type!=chess.KING:
                b2=b.copy(); b2.remove_piece_at(sq)
                if not b2.is_checkmate(): ess[sq]=NOM[p.piece_type]
        exe=b.piece_at(dest)
        decouverte=dest not in ess          # la pièce déplacée n'est pas nécessaire : mat à la découverte (ou pièce redondante)
        executant=NOM[exe.piece_type] if (exe and not decouverte) else 'découverte'
        soutiens=sorted(v for sq,v in ess.items() if sq!=dest)
        rows.append((len(ess),executant,tuple(soutiens)))
n=len(rows); print(f"{n} mats analysés\n")
ex=collections.Counter(r[1] for r in rows)
print("QUI DONNE LE MAT (exécutant) — tous les mats :")
for k,v in ex.most_common(): print(f"   {k:11} {v:5}  ({100*v/n:4.1f} %)")
for taille,titre in ((1,"MONÔME (une seule pièce nécessaire)"),(2,"BINÔME (deux pièces nécessaires)"),(3,"TRINÔME (trois pièces nécessaires)")):
    S=[r for r in rows if r[0]==taille]; m=len(S)
    print(f"\n{titre} : {m} mats ({100*m/n:.1f} %)")
    C=collections.Counter((r[1],' + '.join(r[2]) if r[2] else '—') for r in S)
    for (e,s),v in C.most_common(10 if taille>1 else 6): print(f"   exécutant {e:11} soutien {s:22} {v:4}  ({100*v/m:4.1f} % des {titre.split()[0].lower()}s)")
B=[r for r in rows if r[0]==2]
print("\nBINÔMES : la Dame intervient-elle ? exécutant = Dame :",f"{100*sum(1 for r in B if r[1]=='Dame')/len(B):.0f} %"," | Dame parmi les deux pièces :",f"{100*sum(1 for r in B if r[1]=='Dame' or 'Dame' in r[2])/len(B):.0f} %"," | exécutant = Tour :",f"{100*sum(1 for r in B if r[1]=='Tour')/len(B):.0f} %")
