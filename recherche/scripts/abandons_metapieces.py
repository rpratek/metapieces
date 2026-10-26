#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
abandons_metapieces.py -- Metapieces cachees dans les parties finies SANS mat (abandon, temps).

PRINCIPE
    Le detecteur principal ne voit que les parties terminees par un mat (environ 15 % des parties).
    Ce script examine les autres parties decisives (1-0 / 0-1) : depuis la position finale, Stockfish
    cherche un mat force en N coups ou moins pour le vainqueur. Si on en trouve un, on joue la ligne
    jusqu'au mat et on classe ce mat comme le fait detecteur_metapieces.py. On recupere ainsi les
    Metapieces qui ont ete "annoncees" puis non jouees parce que l'adversaire a abandonne.

USAGE
    python3 abandons_metapieces.py twic1637.pgn twic1662.pgn --out abandons.csv
    python3 abandons_metapieces.py monfichier.pgn --mat-max 4 --profondeur 16 --out abandons.csv

DEPENDANCES   pip install python-chess   +   Stockfish (par defaut /usr/games/stockfish ; sinon --moteur CHEMIN)

LIMITES
    - Le mat est celui que le MOTEUR joue, pas necessairement celui qu'aurait joue le vainqueur
      (plusieurs mats peuvent exister) : a utiliser pour des statistiques, pas comme preuve d'un coup.
    - Un abandon sur depassement de temps peut tomber sur une position sans mat force : ignoree.
    - Ces parties s'ajoutent aux mats reels : ne pas additionner sans distinguer les deux sources.
"""
import re, io, csv, sys, argparse
from collections import Counter
import chess, chess.pgn, chess.engine
from detecteur_metapieces import pieces_contributrices, classer

def scanner_abandons(fichiers, profondeur=12, mat_max=3, moteur="/usr/games/stockfish", max_parties=None):
    eng = chess.engine.SimpleEngine.popen_uci(moteur)
    res = []; vus = set(); n_decisives = 0; n_analysees = 0
    try:
        for fn in fichiers:
            contenu = open(fn, encoding='utf-8', errors='ignore').read()
            for bloc in re.split(r'\n\n(?=\[Event)', contenu):
                if not bloc.startswith('[Event'): continue
                r = re.search(r'\[Result "([^"]+)"\]', bloc)
                if not r or r.group(1) not in ('1-0', '0-1'): continue
                coups = bloc.split('\n\n', 1)[-1]
                cle = re.sub(r'\s+', ' ', coups)
                if cle in vus: continue
                vus.add(cle)
                try:
                    g = chess.pgn.read_game(io.StringIO(bloc)); b = g.board()
                    for m in g.mainline_moves(): b.push(m)
                    if b.is_game_over(): continue          # mat, pat... : deja traites ailleurs
                    n_decisives += 1
                    if max_parties and n_decisives > max_parties: break
                    gagnant = chess.WHITE if r.group(1) == '1-0' else chess.BLACK
                    info = eng.analyse(b, chess.engine.Limit(depth=profondeur)); n_analysees += 1
                    sc = info["score"].white()
                    if not sc.is_mate(): continue
                    mt = sc.mate()
                    if (mt > 0) != (gagnant == chess.WHITE) or abs(mt) > mat_max: continue
                    pv = info.get("pv", []); c = b.copy(); san = []
                    for mv in pv:
                        san.append(c.san(mv)); c.push(mv)
                        if c.is_checkmate(): break
                    if not c.is_checkmate(): continue
                    types = pieces_contributrices(c); cat, n = classer(types)
                    if not cat: continue
                    h = g.headers
                    res.append({'categorie': cat, 'n_pieces': n, 'types': ''.join(sorted(types)),
                                'mat_en': abs(mt), 'ligne': ' '.join(san),
                                'white': h.get('White', '?'), 'black': h.get('Black', '?'),
                                'whiteelo': h.get('WhiteElo', '?'), 'blackelo': h.get('BlackElo', '?'),
                                'event': h.get('Event', '?'), 'date': h.get('Date', '?'),
                                'result': h.get('Result', '?'), 'fen_abandon': b.fen(), 'fen_mat': c.fen()})
                except Exception:
                    continue
    finally:
        eng.quit()
    return res, n_decisives, n_analysees

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Metapieces dans les abandons (mat force retrouve par Stockfish).")
    ap.add_argument('pgn', nargs='+'); ap.add_argument('--out', default='abandons_metapieces.csv')
    ap.add_argument('--profondeur', type=int, default=12); ap.add_argument('--mat-max', type=int, default=3)
    ap.add_argument('--moteur', default='/usr/games/stockfish'); ap.add_argument('--max', type=int, default=None)
    a = ap.parse_args()
    res, nd, na = scanner_abandons(a.pgn, a.profondeur, a.mat_max, a.moteur, a.max)
    cols = ['categorie','n_pieces','types','mat_en','ligne','white','black','whiteelo','blackelo','event','date','result','fen_abandon','fen_mat']
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=';'); w.writeheader()
        for r in res: w.writerow(r)
    print(f"{nd} parties decisives sans mat analysees ; {len(res)} avec un mat force en {a.mat_max} coups ou moins -> {a.out}")
    for cat, n in Counter(r['categorie'] for r in res).most_common(): print(f"  {n:4}  {cat}")
