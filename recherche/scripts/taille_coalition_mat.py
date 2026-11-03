#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
taille_coalition_mat.py -- combien d'unites de l'attaquant visent le Roi au moment du mat ?

DEFINITION (celle de la section 10.5 du livre) : pour chaque partie de TWIC qui se termine par un mat, on compte les UNITES du camp qui mate
(pieces, pions et Roi) qui attaquent au moins une des NEUF cases du Roi maté : sa propre case et ses huit cases voisines.
  1 unite = Monome ; 2 = Binome ; 3 = Trinome ; 4 = Quadrinome ; 5 = Quintinome ; 6 et plus.
Le Monome est examiné en détail : quelle pièce, et s'agit-il d'un mat du couloir (Roi au bord, maté le long de ce bord) ?

CE QUE LA MESURE COMPTE : les unites qui visent le Roi maté, quelle que soit la Métapièce d'où elles viennent : deux Métapièces dirigées vers lui s'additionnent.
Elle ne compte PAS une pièce qui travaille ailleurs sur l'échiquier (une diversion).

USAGE : python3 taille_coalition_mat.py twic1637.pgn twic1662.pgn
"""
import sys,re,io,collections,chess,chess.pgn
def unites(b,att,cases):
    return [(s,p.piece_type) for s,p in b.piece_map().items() if p.color==att and any(t in cases for t in b.attacks(s))]
def main(fichiers):
    D=collections.Counter(); mono=collections.Counter(); paires=collections.Counter(); couloir=0; n=0; vus=set(); parties=0
    for fn in fichiers:
        c=open(fn,encoding='utf-8',errors='ignore').read()
        for bloc in re.split(r'\n\n(?=\[Event)',c):
            cle=re.sub(r'\s+',' ',bloc.split('\n\n',1)[-1])
            if cle in vus: continue
            vus.add(cle)
            try: g=chess.pgn.read_game(io.StringIO(bloc)); b=g.board()
            except Exception: continue
            parties+=1
            for m in g.mainline_moves(): b.push(m)
            if not b.is_checkmate(): continue
            n+=1; att=not b.turn; K=b.king(b.turn)
            N9={K}|set(chess.SquareSet(chess.BB_KING_ATTACKS[K]))
            u=unites(b,att,N9); D[len(u)]+=1
            if len(u)==2: paires[tuple(sorted(chess.piece_name(t) for _,t in u))]+=1
            if len(u)==1:
                mono[chess.piece_name(u[0][1])]+=1
                f,r=chess.square_file(K),chess.square_rank(K); sq=u[0][0]
                # mat du couloir : Roi sur le bord, maté par une pièce qui l'attaque le long de ce bord
                if (r in (0,7) and chess.square_rank(sq)==r) or (f in (0,7) and chess.square_file(sq)==f): couloir+=1
    print(f"{parties} parties lues ; {n} mats\n")
    noms={1:'Monôme',2:'Binôme',3:'Trinôme',4:'Quadrinôme',5:'Quintinôme'}
    six=sum(v for k,v in D.items() if k>=6)
    print(f"{'unités qui visent le Roi maté':32}{'mats':>7}{'%':>8}")
    for k in range(1,6): print(f"{k} ({noms[k]})".ljust(32)+f"{D[k]:>7}{100*D[k]/n:>8.1f}")
    print(f"{'6 et plus':32}{six:>7}{100*six/n:>8.1f}")
    print(f"plus grande coalition observée : {max(D)} unités ; mats avec cinq unités ou moins : {100*(n-six)/n:.1f} %")
    print('\nBinômes les plus fréquents (deux unités) :'); [print(f"   {a} + {b} : {v} mats ({100*v/n:.1f} % de tous les mats)") for (a,b),v in paires.most_common(5)]
    print(f"\nMonôme : {D[1]} mats ; pièce : {dict(mono)} ; mat du couloir (Roi au bord, maté le long de ce bord) : {couloir} sur {D[1]}")
if __name__=='__main__': main(sys.argv[1:] or ['twic1637.pgn','twic1662.pgn'])
