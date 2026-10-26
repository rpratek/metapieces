#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
desequilibre_materiel.py -- comment se perdent les parties qui ne finissent pas par un mat ?

Pour chaque partie decisive (1-0 / 0-1) sans mat, on mesure l'ecart de materiel a la DERNIERE position
enregistree (pion 1, cavalier 3, fou 3, tour 5, dame 9), en faveur du vainqueur, et on le range par tranche.
Option --abandons : meme mesure sur le fichier CSV produit par abandons_metapieces.py (mats forces retrouves).

USAGE
    python3 desequilibre_materiel.py twic1637.pgn twic1662.pgn
    python3 desequilibre_materiel.py twic1637.pgn twic1662.pgn --abandons abandons_twic.csv

LIMITES
    - L'ecart est lu a la derniere position du fichier : si la partie s'arrete juste apres une capture,
      il peut etre fausse d'un point ou deux.
    - Les fichiers ne distinguent pas l'abandon du depassement de temps.
    - A materiel egal en points, une qualite contre deux pions n'est pas distinguee.
"""
import re, io, csv, sys, argparse, collections
import chess, chess.pgn
V = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
ORDRE = ["le perdant a plus de materiel", "materiel equilibre (ecart < 2)", "2 a < 3 (qualite ou pions)",
         "3 a < 5 (une piece mineure)", "5 a < 9 (une Tour ou plus)", "9 et plus (une Dame ou plus)"]

def materiel(b, c):
    return sum(V[p.piece_type] for p in b.piece_map().values() if p.color == c and p.piece_type in V)

def tranche(d):
    if d <= -2: return ORDRE[0]
    if d < 2: return ORDRE[1]
    if d < 3: return ORDRE[2]
    if d < 5: return ORDRE[3]
    if d < 9: return ORDRE[4]
    return ORDRE[5]

def affiche(titre, compte):
    n = sum(compte.values()); print(f"\n{titre} (n = {n})")
    for k in ORDRE: print(f"  {k:34} {compte[k]:5}  ({compte[k]/n*100:4.1f} %)")
    mat = sum(compte[k] for k in ORDRE[2:]); eq = compte[ORDRE[0]] + compte[ORDRE[1]]
    print(f"  -> sur la matiere (ecart >= 2) : {mat} ({mat/n*100:.1f} %) | equilibre ou favorable au perdant : {eq} ({eq/n*100:.1f} %)")

def main():
    ap = argparse.ArgumentParser(description="Ecart de materiel des parties sans mat.")
    ap.add_argument('pgn', nargs='+'); ap.add_argument('--abandons', default=None)
    a = ap.parse_args(); vus = set(); compte = collections.Counter()
    for fn in a.pgn:
        contenu = open(fn, encoding='utf-8', errors='ignore').read()
        for bloc in re.split(r'\n\n(?=\[Event)', contenu):
            r = re.search(r'\[Result "([^"]+)"\]', bloc)
            if not r or r.group(1) not in ('1-0', '0-1'): continue
            cle = re.sub(r'\s+', ' ', bloc.split('\n\n', 1)[-1])
            if cle in vus: continue
            vus.add(cle)
            try:
                g = chess.pgn.read_game(io.StringIO(bloc)); b = g.board()
                for m in g.mainline_moves(): b.push(m)
            except Exception: continue
            if b.is_game_over(): continue
            gag = chess.WHITE if r.group(1) == '1-0' else chess.BLACK
            compte[tranche(materiel(b, gag) - materiel(b, not gag))] += 1
    affiche("Parties decisives sans mat", compte)
    if a.abandons:
        ca = collections.Counter()
        for r in csv.DictReader(open(a.abandons, encoding='utf-8'), delimiter=';'):
            b = chess.Board(r['fen_abandon']); gag = chess.WHITE if r['result'] == '1-0' else chess.BLACK
            ca[tranche(materiel(b, gag) - materiel(b, not gag))] += 1
        affiche("Abandons ou un mat force existait", ca)

if __name__ == '__main__':
    main()
