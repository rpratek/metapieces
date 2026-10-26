#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regime_fen.py -- a quel regime appartient une position ? (prototype, un seul FEN)

Calcule, a partir du seul FEN :
  n          : nombre de pieces sur l'echiquier (pions et Rois compris) ;
  cohesion   : nombre moyen, par piece, de pieces amies qu'elle defend ;
  tension    : nombre moyen, par piece, de pieces adverses qu'elle attaque ;
  rois       : avancement moyen des deux Rois (0 = rangee de depart, 1 = au centre ou au-dela) ;
  dames      : nombre de Dames.
Puis propose deux lectures du regime, qu'on compare :
  - par le MATERIEL (n) ;
  - par les INDICATEURS (cohesion et tension, comparees aux moyennes mesurees sur TWIC).
Si les deux lectures divergent, la position est dite "atypique" : le regime est une position sur des echelles continues,
pas une etiquette.
USAGE : python3 regime_fen.py "<FEN>"        (sans argument : exemples)
"""
import sys, chess
# moyennes mesurees sur TWIC (voir regimes_pieces.py) : (min, max, cohesion, tension, nom du regime)
REFERENCE = [(28, 32, 1.41, 0.13, "deploiement"), (24, 27, 1.32, 0.24, "transition 1 (entree dans le contact)"),
             (20, 23, 1.11, 0.27, "transition 1 (entree dans le contact)"),
             (16, 19, 0.89, 0.26, "reseaux (milieu de jeu)"), (12, 15, 0.70, 0.23, "reseaux (milieu de jeu)"),
             (8, 11, 0.57, 0.21, "transition 2 (le Roi s'eveille)"), (0, 7, 0.41, 0.18, "finale")]

def indicateurs(b):
    pm = b.piece_map(); n = len(pm); a = e = 0
    for sq, p in pm.items():
        for t in b.attacks(sq):
            q = pm.get(t)
            if q is None: continue
            if q.color == p.color: a += 1
            else: e += 1
    rois = []
    for coul in (chess.WHITE, chess.BLACK):
        k = b.king(coul)
        if k is None: continue
        r = chess.square_rank(k) if coul == chess.WHITE else 7 - chess.square_rank(k)
        rois.append(min(r / 3.0, 1.0))
    dames = len(b.pieces(chess.QUEEN, chess.WHITE)) + len(b.pieces(chess.QUEEN, chess.BLACK))
    return n, a / n, e / n, sum(rois) / len(rois), dames

def lecture(fen):
    b = chess.Board(fen); n, coh, ten, rois, dames = indicateurs(b)
    par_materiel = next(nom for lo, hi, c, t, nom in REFERENCE if lo <= n <= hi)
    plus_proche = min(REFERENCE, key=lambda r: abs(r[2] - coh) + 0.5 * abs(r[3] - ten))
    par_indic = plus_proche[4]
    return dict(n=n, cohesion=coh, tension=ten, rois=rois, dames=dames, materiel=par_materiel, indicateurs=par_indic, atypique=(par_materiel != par_indic))

EXEMPLES = [("Position de depart", chess.STARTING_FEN),
            ("pjdw, avant 11.e4", "r1b2rk1/ppqnn1pp/2p1pp2/3p4/2PP4/1PBBPN2/P4PPP/R2Q1RK1 w - - 2 11"),
            ("rpratek-guestfxjx, apres 20.Dh5", "rn3qk1/p1b3p1/b1pNp2p/1p2P2Q/2pPN3/P5P1/1P4BP/R5K1 b - - 1 20"),
            ("Karpov-Unzicker, apres 24.Fa7", "r1rq1bk1/Bn1b1p1p/3p1np1/1p1Pp3/1Pp1P3/2P2NNP/R2Q1PP1/1B2R1K1 b - - 0 24"),
            ("Final de Maghsoodloo (Roi + Dame)", "8/8/8/8/8/5K2/6Qk/8 b - - 0 87"),
            ("Final de Nakamura (Roi + Tour)", "8/8/8/8/8/6K1/8/5R1k b - - 4 62")]
# REMARQUE : avec moins de 8 pieces, les indicateurs par piece sont instables : se fier au nombre de pieces et a l'activite des Rois.
if __name__ == "__main__":
    fens = [("FEN fourni", sys.argv[1])] if len(sys.argv) > 1 else EXEMPLES
    print(f"{'position':44}{'n':>3}{'cohésion':>9}{'tension':>8}{'Rois':>6}{'D':>3}  {'par le matériel':32}{'par les indicateurs':32}")
    for nom, fen in fens:
        try: r = lecture(fen)
        except Exception as ex: print(nom, "FEN invalide :", ex); continue
        print(f"{nom:44}{r['n']:3}{r['cohesion']:9.2f}{r['tension']:8.2f}{r['rois']:6.2f}{r['dames']:3}  {r['materiel']:32}{r['indicateurs']:32}{'  <- atypique' if r['atypique'] else ''}")
