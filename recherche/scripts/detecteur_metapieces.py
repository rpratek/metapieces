#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detecteur_metapieces.py -- Extraction automatique de Metapieces depuis une archive PGN
=========================================================================================
Aligne sur le catalogue "Les Metapieces" (Richard Pratek, 2025).

PRINCIPE
--------
Pour chaque partie d'un fichier PGN se terminant par un mat (#), le script identifie
les pieces du camp gagnant qui "travaillent" dans le filet de mat -- c'est-a-dire
celles qui donnent echec ou qui controlent une case de fuite du Roi matte (y compris
le Roi attaquant lui-meme, pertinent pour B7 et T4). Le multi-ensemble de types de
pieces ainsi obtenu est compare au catalogue pour identifier la Metapiece en jeu.

USAGE
-----
    python3 detecteur_metapieces.py monfichier.pgn --out resultats.csv
    python3 detecteur_metapieces.py monfichier.pgn --out resultats.csv --max 5000
    python3 detecteur_metapieces.py monfichier.pgn --categorie T4 --out t4_seuls.csv

DEPENDANCE
----------
    pip install python-chess --break-system-packages

SOURCE DES ARCHIVES
--------------------
The Week in Chess (TWIC) publie une archive hebdomadaire de parties de haut niveau :
    https://theweekinchess.com/twic
Pour une archive personnelle solide, un rythme mensuel (4-5 fichiers) ou annuel
(cumul de l'annee) est largement suffisant -- scanner chaque semaine individuellement
n'apporte rien de plus qu'un cumul periodique.

LIMITES CONNUES (honnetes, a garder en tete)
----------------------------------------------
- B7 (Pion+Roi) et T5 (pions lies) sont des motifs STRUCTURELS, pas des motifs de
  mat : ce script, qui ne regarde que les positions de mat, ne peut structurellement
  pas les trouver. Ce n'est pas une absence du jeu reel, juste une limite de methode.
- B2, B5, B6, T3 ressortent rarement voire jamais sur de grands echantillons : dans
  la pratique, une piece supplementaire incidente (souvent un pion) vient presque
  toujours s'ajouter au duo/trio theorique, faisant basculer le classement vers une
  categorie a cardinalite superieure (Quadrinome, etc.). A verifier manuellement
  avant de rejeter une partie prometteuse -- voir la fonction detail_case() ci-dessous.
- "Quadrinome?" / "Pentanome?" sont des CANDIDATS (4 ou 5 pieces contributrices),
  pas des categories officiellement nommees dans le catalogue a ce jour -- a valider
  un par un.
- B8 = Tour + Fou (mat de Mayet). Attention : une paire Tour + Fou n'est PAS
  forcement un mat de Mayet (mat de l'Opera, Pillsbury, Morphy... sont aussi des
  Tour + Fou). Utiliser est_mayet(board) pour le test strict : Tour au contact du
  Roi, defendue par un Fou eloigne qui ne couvre aucune autre case de fuite.
"""
import chess, chess.pgn, io, csv, sys, re
from collections import Counter

CATALOGUE = {
    tuple(sorted(['B','N'])): 'B1',
    tuple(sorted(['Q','B'])): 'B2',
    tuple(sorted(['Q','R'])): 'B3',
    tuple(sorted(['R','R'])): 'B4',
    tuple(sorted(['B','B'])): 'B5',
    tuple(sorted(['N','P'])): 'B6',
    tuple(sorted(['P','K'])): 'B7',
    tuple(sorted(['R','B'])): 'B8',   # Tour + Fou : mat de Mayet
    tuple(sorted(['Q','N'])): 'B9',
    tuple(sorted(['R','N'])): 'B10',
    tuple(sorted(['Q','B','N'])): 'T1',
    tuple(sorted(['Q','R','B'])): 'T2',
    tuple(sorted(['N','N','P'])): 'T3',
    tuple(sorted(['K','N','B'])): 'T4',
    tuple(sorted(['Q','R','N'])): 'T6',
    tuple(sorted(['Q','B','B'])): 'T7',
    tuple(sorted(['Q','R','P'])): 'T8',
}

def pieces_contributrices(board):
    """Multi-ensemble (lettres de type) des pieces attaquantes qui donnent echec ou
    controlent une case de fuite du Roi matte."""
    assert board.is_checkmate()
    roi_couleur = board.turn
    roi_sq = board.king(roi_couleur)
    attaquant = not roi_couleur
    cases_interet = set(chess.SquareSet(chess.BB_KING_ATTACKS[roi_sq])) | {roi_sq}
    contributeurs = {}
    for sq, piece in board.piece_map().items():
        if piece.color != attaquant:
            continue
        couverts = board.attacks(sq) & chess.SquareSet(cases_interet)
        if couverts:
            contributeurs[sq] = piece.piece_type
    return [chess.piece_symbol(t).upper() for t in contributeurs.values()]


def est_mayet(board):
    """Test strict du mat de Mayet sur une position de mat : une Tour donne l'echec
    au contact du Roi, un Fou eloigne la defend, et ce Fou ne couvre aucune autre
    case de fuite (sinon : mat de l'Opera). Retourne (True/False, explication)."""
    assert board.is_checkmate()
    roi = board.king(board.turn); att = not board.turn
    voisines = chess.SquareSet(chess.BB_KING_ATTACKS[roi])
    checkers = list(board.checkers())
    if len(checkers) != 1: return False, "double echec"
    ck = checkers[0]
    if board.piece_at(ck).piece_type != chess.ROOK or ck not in voisines:
        return False, "echec non donne par une Tour au contact du Roi"
    fous = [s for s, q in board.piece_map().items() if q.color == att and q.piece_type == chess.BISHOP and ck in board.attacks(s)]
    if not fous: return False, "Tour non defendue par un Fou"
    f = fous[0]
    if f in voisines: return False, "Fou au contact du Roi (pas eloigne)"
    if [s for s in voisines if s != ck and s in board.attacks(f) and not board.piece_at(s)]:
        return False, "le Fou couvre une case de fuite (type Opera)"
    return True, f"Tour {chess.square_name(ck)} defendue par Fou {chess.square_name(f)}"

def detail_case(fen):
    """Affiche le detail case-par-case (quelle piece couvre quoi) pour une FEN de mat
    donnee -- utile pour verifier a la main si une piece est vraiment necessaire ou
    seulement redondante (ex. un pion qui 'couvre' une case deja occupee par une
    piece amie, donc sans effet reel sur le mat)."""
    board = chess.Board(fen)
    roi_sq = board.king(board.turn)
    cases = list(chess.SquareSet(chess.BB_KING_ATTACKS[roi_sq])) + [roi_sq]
    for sq, piece in board.piece_map().items():
        if piece.color == board.turn: continue
        couverts = board.attacks(sq) & chess.SquareSet(cases)
        if couverts:
            noms = [chess.square_name(s) for s in couverts]
            print(f"  {chess.piece_name(piece.piece_type):8} en {chess.square_name(sq)} couvre: {noms}")

def classer(types):
    n = len(types)
    multiset = tuple(sorted(types))
    if multiset in CATALOGUE:
        return CATALOGUE[multiset], n
    if n == 4: return 'Quadrinome?', n
    if n >= 5: return 'Pentanome?', n
    return None, n

def scanner_pgn(chemin, max_parties=None, categorie_filtre=None):
    resultats = []
    with open(chemin, encoding='utf-8', errors='ignore') as f:
        contenu = f.read()
    blocs = re.split(r'\n\n(?=\[Event)', contenu)
    n_scan = 0
    n_total = len(blocs)
    for i, bloc in enumerate(blocs):
        if max_parties and n_scan >= max_parties: break
        if '#' not in bloc: continue
        if n_scan % 500 == 0 and n_scan > 0:
            print(f"  ... {n_scan} parties avec mat traitees sur {n_total} lues", file=sys.stderr)
        try:
            game = chess.pgn.read_game(io.StringIO(bloc))
            if game is None: continue
            board = game.board()
            moves = list(game.mainline_moves())
            if not moves: continue
            for m in moves: board.push(m)
            if not board.is_checkmate(): continue
            types = pieces_contributrices(board)
            cat, n = classer(types)
            n_scan += 1
            if not cat: continue
            if categorie_filtre and cat != categorie_filtre: continue
            headers = game.headers
            resultats.append({
                'categorie': cat, 'n_pieces': n, 'types': ''.join(sorted(types)),
                'white': headers.get('White','?'), 'black': headers.get('Black','?'),
                'whiteelo': headers.get('WhiteElo','?'), 'blackelo': headers.get('BlackElo','?'),
                'event': headers.get('Event','?'), 'date': headers.get('Date','?'),
                'result': headers.get('Result','?'), 'fen': board.fen(),
            })
        except Exception:
            continue
    return resultats

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description="Extrait les Metapieces d'une archive PGN (ex. TWIC).")
    ap.add_argument('pgn', help="chemin du fichier .pgn a analyser")
    ap.add_argument('--out', default='resultats_metapieces.csv', help="fichier CSV de sortie")
    ap.add_argument('--max', type=int, default=None, help="limiter le nombre de parties-avec-mat traitees (utile pour tester vite)")
    ap.add_argument('--categorie', default=None, help="ne garder qu'une categorie precise, ex. --categorie T4")
    args = ap.parse_args()

    print(f"Analyse de {args.pgn} ...")
    res = scanner_pgn(args.pgn, args.max, args.categorie)
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['categorie','n_pieces','types','white','black','whiteelo','blackelo','event','date','result','fen'], delimiter=';')
        w.writeheader()
        for r in res: w.writerow(r)

    print(f"\n{len(res)} parties classees -> {args.out}\n")
    c = Counter(r['categorie'] for r in res)
    for cat, n in c.most_common():
        print(f"  {n:4}  {cat}")
    print("\nPour inspecter le detail d'un mat precis (quelle piece couvre quelle case) :")
    print("  python3 -c \"from detecteur_metapieces import detail_case; detail_case('VOTRE_FEN_ICI')\"")
