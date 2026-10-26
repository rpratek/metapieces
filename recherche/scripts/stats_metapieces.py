#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stats_metapieces.py -- Statistiques de Metapieces par periode (mois / annee) dans une ou plusieurs archives PGN.

USAGE
    python3 stats_metapieces.py twic1637.pgn twic1662.pgn --out stats.csv
    python3 stats_metapieces.py twic*.pgn --par annee --out stats_annuelles.csv

Ce que le script compte, pour chaque periode (d'apres la DATE de chaque partie, pas celle du fichier) :
    parties      : nombre de parties (doublons exclus, meme coups = meme partie)
    mats         : parties terminees par un mat
    classees     : mats rattaches a une categorie du catalogue (B1..B10, T1..T8, Quadrinome?, Pentanome?)
    puis le nombre de mats par categorie, et le taux pour 1000 parties.

ATTENTION : ces chiffres decrivent les METAPIECES VISIBLES DANS UN MAT FINAL, pas leur frequence reelle
dans le jeu (voir les limites du detecteur). Sur une semaine de TWIC, les categories rares valent 0 a 3 :
un mois ou une annee donnent des chiffres bien plus exploitables.
"""
import re, io, csv, sys, hashlib, argparse
from collections import Counter, defaultdict
import chess, chess.pgn
from detecteur_metapieces import pieces_contributrices, classer

CATS = ['B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','T1','T2','T3','T4','T6','T7','T8','Quadrinome?','Pentanome?']

def periode(date, mode):
    m = re.match(r'(\d{4})\.(\d{2})', date or '')
    if not m: return 'date inconnue'
    return m.group(1) if mode == 'annee' else f"{m.group(1)}-{m.group(2)}"

def analyser(fichiers, mode='mois'):
    vus = set()
    stats = defaultdict(lambda: Counter())
    for fn in fichiers:
        contenu = open(fn, encoding='utf-8', errors='ignore').read()
        for bloc in re.split(r'\n\n(?=\[Event)', contenu):
            if not bloc.startswith('[Event'): continue
            coups = bloc.split('\n\n', 1)[-1]
            cle = hashlib.md5(re.sub(r'\s+', ' ', coups).encode()).hexdigest()
            if cle in vus: continue
            vus.add(cle)
            d = re.search(r'\[Date "([^"]*)"\]', bloc)
            p = periode(d.group(1) if d else '', mode)
            stats[p]['parties'] += 1
            if '#' not in bloc: continue
            try:
                g = chess.pgn.read_game(io.StringIO(bloc)); b = g.board()
                for m in g.mainline_moves(): b.push(m)
                if not b.is_checkmate(): continue
                stats[p]['mats'] += 1
                cat, n = classer(pieces_contributrices(b))
                if cat:
                    stats[p]['classees'] += 1
                    stats[p][cat] += 1
            except Exception:
                continue
    return stats

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Statistiques de Metapieces par periode.")
    ap.add_argument('pgn', nargs='+')
    ap.add_argument('--par', choices=['mois', 'annee'], default='mois')
    ap.add_argument('--out', default='stats_metapieces.csv')
    a = ap.parse_args()
    st = analyser(a.pgn, a.par)
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['periode', 'parties', 'mats', 'classees'] + CATS + [f'{c} /1000 parties' for c in CATS])
        for p in sorted(st):
            s = st[p]; n = s['parties']
            w.writerow([p, n, s['mats'], s['classees']] + [s[c] for c in CATS] + [round(1000 * s[c] / n, 1) if n else 0 for c in CATS])
    tot = Counter()
    for s in st.values(): tot.update(s)
    print(f"{len(st)} periode(s) -> {a.out}")
    print(f"Total : {tot['parties']} parties, {tot['mats']} mats ({100*tot['mats']/max(1,tot['parties']):.1f} %), {tot['classees']} classes")
    for c in CATS:
        if tot[c]: print(f"  {c:12} {tot[c]:4}   ({1000*tot[c]/tot['parties']:.1f} pour 1000 parties)")
