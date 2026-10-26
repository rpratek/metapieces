#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pivot_parties.py -- par ou les pieces changent-elles d'aile dans de vraies parties ?

On suit chaque piece (Cavalier, Fou, Tour, Dame) coup apres coup. Une "bascule" est un passage de l'aile
Dame (colonnes a-c) a l'aile Roi (colonnes f-h), ou l'inverse. On classe la route empruntee :
  - directe       : la piece saute d'une aile a l'autre sans case intermediaire (Fou, Tour, Dame) ;
  - par le pivot  : au moins une case intermediaire sur les colonnes d-e, rangees 3 a 6 ;
  - par l'arriere : cases intermediaires uniquement sur les colonnes d-e, rangees 1-2 ou 7-8.
Repere : au hasard, 50 % des cases d-e sont en rangees 3-6.
USAGE : python3 pivot_parties.py twic1637.pgn twic1662.pgn
"""
import re, io, sys, collections
import chess, chess.pgn

TYPES = {chess.KNIGHT: "Cavalier", chess.BISHOP: "Fou", chess.ROOK: "Tour", chess.QUEEN: "Dame"}
def aile(sq):
    f = chess.square_file(sq); return 'Q' if f <= 2 else ('K' if f >= 5 else 'C')

def suit(game):
    """Renvoie la liste des trajets : (type, [(ply, case)...]) pour chaque piece, avec nb de pieces au depart."""
    b = game.board(); ident = {}; typ = {}; chemin = collections.defaultdict(list); n = 0
    for sq, p in b.piece_map().items():
        ident[sq] = n; typ[n] = p.piece_type; chemin[n].append((0, sq, 32)); n += 1
    ply = 0
    for m in game.mainline_moves():
        ply += 1; nb = len(b.piece_map())
        cap_sq = m.to_square
        if b.is_en_passant(m): cap_sq = chess.square(chess.square_file(m.to_square), chess.square_rank(m.from_square))
        if b.is_capture(m): ident.pop(cap_sq, None)
        pid = ident.pop(m.from_square)
        if b.is_castling(m):
            ident[m.to_square] = pid
            if chess.square_file(m.to_square) == 6: r_from, r_to = chess.square(7, chess.square_rank(m.to_square)), chess.square(5, chess.square_rank(m.to_square))
            else: r_from, r_to = chess.square(0, chess.square_rank(m.to_square)), chess.square(3, chess.square_rank(m.to_square))
            rid = ident.pop(r_from); ident[r_to] = rid
            chemin[rid].append((ply, r_to, nb))
        else:
            ident[m.to_square] = pid
            if m.promotion: typ[pid] = m.promotion; chemin[pid] = []
        chemin[pid].append((ply, m.to_square, nb))
        b.push(m)
    return [(typ[i], c) for i, c in chemin.items() if typ[i] in TYPES and len(c) > 1]

def bascules(trajet):
    """Detecte les bascules Q<->K : renvoie (nb_cases_intermediaires, cases, coups_de_la_piece, nb_pieces_au_depart)."""
    sorties = []; derniere = None; idx = None
    for k, (ply, sq, nb) in enumerate(trajet):
        a = aile(sq)
        if a == 'C': continue
        if derniere is None: derniere, idx = a, k; continue
        if a != derniere:
            inter = [trajet[j][1] for j in range(idx + 1, k)]          # cases d-e traversees
            sorties.append((inter, k - idx, trajet[idx][2]))
        derniere, idx = a, k
    return sorties

def main(fichiers):
    stats = collections.defaultdict(lambda: collections.Counter()); coups = collections.defaultdict(list); nbg = 0; vus = set()
    for fn in fichiers:
        c = open(fn, encoding='utf-8', errors='ignore').read()
        for bloc in re.split(r'\n\n(?=\[Event)', c):
            cle = re.sub(r'\s+', ' ', bloc.split('\n\n', 1)[-1])
            if cle in vus: continue
            vus.add(cle)
            try: g = chess.pgn.read_game(io.StringIO(bloc)); tr = suit(g)
            except Exception: continue
            nbg += 1
            for t, trajet in tr:
                for inter, k, nb in bascules(trajet):
                    if not inter: cl = 'directe'
                    elif any(2 <= chess.square_rank(s) <= 5 for s in inter): cl = 'pivot'
                    else: cl = 'arriere'
                    nm = TYPES[t]; stats[nm][cl] += 1; coups[(nm, cl)].append(k)
                    if t == chess.KNIGHT: stats['Cavalier ' + ('>=24 pieces' if nb >= 24 else ('16-23' if nb >= 16 else '<=15'))][cl] += 1
    print(f"{nbg} parties analysees\n")
    print(f"{'piece':22}{'bascules':>9}{'directes':>10}{'par le pivot':>14}{'par l arriere':>15}{'pivot / (pivot+arriere)':>25}")
    for nm in ('Cavalier', 'Fou', 'Tour', 'Dame', 'Cavalier >=24 pieces', 'Cavalier 16-23', 'Cavalier <=15'):
        s = stats[nm]; tot = sum(s.values())
        if not tot: continue
        pv, ar = s['pivot'], s['arriere']
        print(f"{nm:22}{tot:9}{s['directe']/tot*100:9.1f}%{pv/tot*100:13.1f}%{ar/tot*100:14.1f}%{(pv/(pv+ar)*100 if pv+ar else 0):24.1f}%")
    print("\nNombre moyen de coups de la piece pour changer d'aile :")
    for nm in ('Cavalier', 'Fou', 'Tour', 'Dame'):
        for cl in ('pivot', 'arriere'):
            L = coups[(nm, cl)]
            if L: print(f"   {nm:9} par {cl:8} : {sum(L)/len(L):.2f} coups  (n = {len(L)})")
if __name__ == '__main__':
    main(sys.argv[1:] or ['twic1637.pgn', 'twic1662.pgn'])
