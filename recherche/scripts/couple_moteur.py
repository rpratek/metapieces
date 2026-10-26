#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
couple_moteur.py -- le COUPLE MOTEUR des pieces, calcule a la demande.

Trois composantes tirees du livre (p.545 : adherence, puissance instantanee, force de frappe reelle) :
  puissance  P = poids (4/3/2/1) des cases controlees par la piece (hors cases occupees par ses pieces)
  adherence  A = part (ponderee) de ce territoire aussi controlee par une autre piece amie (0 a 1) : l'EMBRAYAGE
  frappe     F = poids des cases du Roi adverse et de ses voisines que la piece controle
Variantes comparees :
  v_papier = valeur 1-3-5-9            v_mobilite = nombre de cases controlees M
  v_brouillon = V x M x B  (formule du brouillon ; B = nombre de secteurs de l'echiquier atteints, de 1 a 4)
  v_P = P     v_PA = P x A     v_PAF = P x A + F
USAGE : python3 couple_moteur.py "<FEN>"                 (tableau d'une position)
        python3 couple_moteur.py --epreuve N <stockfish>  (N positions TWIC, contribution mesuree par Stockfish)
"""
import sys, os, time, random, chess, chess.pgn, chess.engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metapiece_territoire as T
V = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9}
def secteurs(cases):
    return len({(chess.square_file(s)//4, chess.square_rank(s)//4) for s in cases}) or 1
def composantes(board, couleur, sq, A):
    t, att = A[sq]; propres = board.occupied_co[couleur]
    terr = {s for s in att if not (propres >> s) & 1}
    P = sum(T.poids(s) for s in terr)
    autres = set().union(*[a for s2, (t2, a) in A.items() if s2 != sq]) if len(A) > 1 else set()
    mesh = sum(T.poids(s) for s in terr if s in autres); Ad = mesh / P if P else 0.0
    K = board.king(not couleur); zone = {K} | {s for s in chess.SQUARES if chess.square_distance(s, K) == 1}
    F = sum(T.poids(s) for s in att if s in zone)
    M = len(terr); B = secteurs(terr)
    return dict(V=V[t], M=M, B=B, P=P, A=Ad, F=F, v_brouillon=V[t]*M*B, v_PA=P*Ad, v_PAF=P*Ad+F)
def tableau(board):
    lignes = []
    for col in (chess.WHITE, chess.BLACK):
        A = T.attaques_pieces(board, col)
        for sq, (t, att) in A.items():
            if t == chess.PAWN: continue
            c = composantes(board, col, sq, A); c.update(camp='Blancs' if col else 'Noirs', case=chess.square_name(sq), piece=chess.piece_name(t)); lignes.append((col, sq, c))
    return lignes
def contribution(eng, board, col, sq, base, prof):
    c = board.copy(); c.remove_piece_at(sq); c.castling_rights &= ~chess.BB_SQUARES[sq]
    if not c.is_valid(): return None
    e = max(-10, min(10, eng.analyse(c, chess.engine.Limit(depth=prof))['score'].white().score(mate_score=1000)/100))
    return (base - e) if col == chess.WHITE else (e - base)
def rang(a):
    import numpy as np
    a = np.asarray(a, float); o = a.argsort(); r = np.empty(len(a)); r[o] = np.arange(len(a))
    for v in np.unique(a): r[a == v] = r[a == v].mean()
    return r
def spearman(x, y):
    import numpy as np
    return float(np.corrcoef(rang(x), rang(y))[0, 1])
def epreuve(N, sf, budget=250, prof=12):
    random.seed(7); t0 = time.time(); f = open(os.environ.get('PGN','twic1637.pgn'), encoding='utf-8', errors='ignore')
    eng = chess.engine.SimpleEngine.popen_uci(sf); eng.configure({'Threads': 4, 'Hash': 128}); donnees = []; npos = 0
    while npos < N and time.time() - t0 < budget:
        g = chess.pgn.read_game(f)
        if g is None: break
        mv = list(g.mainline_moves())
        if len(mv) < 40: continue
        b = g.board()
        for m in mv[:random.randint(16, min(70, len(mv)-2))]: b.push(m)
        if b.is_game_over(): continue
        base = max(-10, min(10, eng.analyse(b, chess.engine.Limit(depth=prof))['score'].white().score(mate_score=1000)/100)); npos += 1
        for col, sq, c in tableau(b):
            ct = contribution(eng, b, col, sq, base, prof)
            if ct is not None: c['contrib'] = ct; c['ecart'] = ct - c['V']; donnees.append(c)
    eng.quit(); return npos, donnees, time.time() - t0
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--epreuve':
        N = int(sys.argv[2]); sf = sys.argv[3]
        npos, D, dt = epreuve(N, sf)
        print(f"{npos} positions, {len(D)} pieces mesurees en {dt:.0f} s (Stockfish, profondeur 12)")
        cles = [('valeur papier V','V'),('mobilite M','M'),('brouillon V x M x B','v_brouillon'),('puissance P','P'),('puissance x adherence','v_PA'),('P x A + frappe','v_PAF')]
        print("\nCorrelation de rang (Spearman) avec la CONTRIBUTION reelle de la piece :")
        for nom, k in cles: print(f"  {nom:24} {spearman([d[k] for d in D],[d['contrib'] for d in D]):+.2f}")
        import json
        json.dump(D,open('epreuve_donnees.json','w'))
        print("\nA L'INTERIEUR D'UN MEME TYPE DE PIECE (la valeur papier est constante) : correlation avec la contribution reelle")
        print(f"{'type':9}{'n':>5}{'M':>7}{'P':>7}{'A':>7}{'F':>7}{'P*A':>7}{'P*A+F':>8}")
        for typ in ('knight','bishop','rook','queen'):
            S=[d for d in D if d['piece']==typ]
            if len(S)<30: continue
            r=lambda k: spearman([d[k] for d in S],[d['contrib'] for d in S])
            print(f"{typ:9}{len(S):>5}{r('M'):>+7.2f}{r('P'):>+7.2f}{r('A'):>+7.2f}{r('F'):>+7.2f}{r('v_PA'):>+7.2f}{r('v_PAF'):>+8.2f}")
        print("\nCorrelation avec l'ECART a la valeur papier (contribution moins V) :")
        for nom, k in (('mobilite M','M'),('puissance P','P'),('adherence A','A'),('frappe F','F'),('brouillon V x M x B','v_brouillon')):
            print(f"  {nom:24} {spearman([d[k] for d in D],[d['ecart'] for d in D]):+.2f}")
    else:
        b = chess.Board(sys.argv[1]); print(f"{'camp':7}{'piece':8}{'case':5}{'V':>3}{'M':>4}{'B':>3}{'P':>5}{'A':>6}{'F':>4}{'brouillon':>11}{'P*A':>7}{'P*A+F':>8}")
        for col, sq, c in tableau(b): print(f"{c['camp']:7}{c['piece']:8}{c['case']:5}{c['V']:>3}{c['M']:>4}{c['B']:>3}{c['P']:>5}{c['A']:>6.2f}{c['F']:>4}{c['v_brouillon']:>11}{c['v_PA']:>7.1f}{c['v_PAF']:>8.1f}")
