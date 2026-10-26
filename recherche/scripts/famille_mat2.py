#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
famille_mat2.py -- generalise le premier exemple (bbr3k1/1R5p/7B/8/8/5B2/7P/6K1) : mat en 2 construit par un echec qui pousse le Roi sur sa seule case de repli.
Recherche evolutive : on part de la position de reference et on la mute (type de piece, case, Roi noir, pions noirs, pieces noires « leurres »).
Schema retenu : 1.(echec) -> le Roi n'a qu'UNE reponse legale -> 2.(mat). Unicite verifiee : aucun autre premier coup des Blancs (echec ou non) ne donne mat en 2.
Pour chaque position : executant (piece du mat), controleurs (pieces blanches qui couvrent les cases voisines de la case de repli), soutien (pieces qui protegent l'executant).
USAGE : python3 famille_mat2.py <budget_secondes>
"""
import sys, random, time, chess, collections
random.seed(12)
BASE="bbr3k1/1R5p/7B/8/8/5B2/7P/6K1 w - - 0 1"
def schema(b):
    """retourne (coup1, case_refuge, coup2) si schema 'echec -> reponse unique -> mat' pour exactement un coup1 en 2 ; sinon None"""
    trouves=[]
    for m1 in list(b.legal_moves):
        if not b.gives_check(m1): continue
        b.push(m1); reps=list(b.legal_moves)
        if len(reps)==1:
            b.push(reps[0]); mats=[]
            for m2 in list(b.legal_moves):
                b.push(m2); ok=b.is_checkmate(); b.pop()
                if ok: mats.append(m2)
            b.pop()
            if mats: trouves.append((m1,reps[0],mats[0]))
        b.pop()
    return trouves
def mat2_autres(b,m1_ok):
    """vrai si un AUTRE premier coup (quelconque) force aussi un mat en 2 (alors pas d'unicite)"""
    for m1 in list(b.legal_moves):
        if m1==m1_ok: continue
        b.push(m1)
        if b.is_checkmate(): b.pop(); return True
        reps=list(b.legal_moves); tout=bool(reps)
        for r in reps:
            b.push(r); ok=False
            for m2 in list(b.legal_moves):
                b.push(m2); c=b.is_checkmate(); b.pop()
                if c: ok=True; break
            b.pop()
            if not ok: tout=False; break
        b.pop()
        if tout: return True
    return False
def muter(fen):
    b=chess.Board(fen); L=[s for s in chess.SQUARES if not b.piece_at(s)]
    for _ in range(random.choice([1,1,2,2,3])):
        op=random.random()
        blancs=[s for s,p in b.piece_map().items() if p.color==chess.WHITE and p.piece_type!=chess.KING]
        noirs=[s for s,p in b.piece_map().items() if p.color==chess.BLACK and p.piece_type!=chess.KING]
        L=[s for s in chess.SQUARES if not b.piece_at(s)]
        if op<0.30 and blancs:       # changer le type d'une piece blanche
            s=random.choice(blancs); p=b.piece_at(s)
            if p.piece_type!=chess.PAWN: b.set_piece_at(s,chess.Piece(random.choice([chess.QUEEN,chess.ROOK,chess.BISHOP,chess.KNIGHT]),chess.WHITE))
        elif op<0.60 and blancs:     # deplacer une piece blanche
            s=random.choice(blancs); p=b.piece_at(s); b.remove_piece_at(s); t=random.choice(L)
            if not(p.piece_type==chess.PAWN and chess.square_rank(t) in (0,7)): b.set_piece_at(t,p)
        elif op<0.72:                # deplacer le Roi noir
            k=b.king(chess.BLACK); b.remove_piece_at(k); b.set_piece_at(random.choice([chess.parse_square(c) for c in ('g8','h8','f8','h7','g7','a8','e8','b8')]),chess.Piece(chess.KING,chess.BLACK))
        elif op<0.82 and noirs:      # supprimer une piece noire
            b.remove_piece_at(random.choice(noirs))
        elif op<0.92:                # ajouter une piece noire (leurre ou obstacle)
            t=random.choice(L); pt=random.choice([chess.PAWN,chess.KNIGHT,chess.BISHOP,chess.ROOK])
            if not(pt==chess.PAWN and chess.square_rank(t) in (0,7)): b.set_piece_at(t,chess.Piece(pt,chess.BLACK))
        else:                        # ajouter une piece blanche
            t=random.choice(L); pt=random.choice([chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN,chess.PAWN])
            if not(pt==chess.PAWN and chess.square_rank(t) in (0,7)): b.set_piece_at(t,chess.Piece(pt,chess.WHITE))
    b.turn=chess.WHITE; return b
def roles(b,m1,rep,m2):
    c=b.copy(); c.push(m1); c.push(rep); c.push(m2)
    E=m2.to_square; K=c.king(chess.BLACK); piece=lambda s:chess.piece_name(c.piece_type_at(s))
    voisines=[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
    ctrl=[]; 
    for s,p in c.piece_map().items():
        if p.color!=chess.WHITE or s==E or p.piece_type in (chess.KING,chess.PAWN): continue
        if any(c.is_attacked_by(chess.WHITE,v) and (s in c.attackers(chess.WHITE,v)) for v in voisines): ctrl.append(piece(s))
    soutien=[piece(s) if c.piece_type_at(s)!=chess.KING else 'roi' for s in c.attackers(chess.WHITE,E) if s!=E]
    return piece(E),ctrl,soutien,(b.piece_at(m1.from_square).piece_type==c.piece_type_at(E) and m1.to_square==m2.from_square)
BUD=float(sys.argv[1]); t0=time.time(); pool=[BASE]; vus={BASE}; trouve={}; n=0
while time.time()-t0<BUD:
    fen=random.choice(pool); b=muter(fen); n+=1
    if not b.is_valid() or b.is_check() or not b.king(chess.BLACK) or b.occupied_co[chess.BLACK]==0: continue
    f=b.fen()
    if f in vus: continue
    vus.add(f); s=schema(b)
    if len(s)==1 and not mat2_autres(b,s[0][0]):
        trouve[f]=s[0]; pool.append(f)
print(f"{n} mutations en {time.time()-t0:.0f} s ; positions du schéma « échec → refuge unique → mat » à coup unique : {len(trouve)}\n")
EX=collections.Counter(); MEME=0; AVEC_SOUTIEN=0; NCTRL=collections.Counter(); R1=collections.Counter(); rows=[]
for f,(m1,rep,m2) in trouve.items():
    b=chess.Board(f); E,ctrl,sout,meme=roles(b,m1,rep,m2)
    EX[E]+=1; MEME+=meme; AVEC_SOUTIEN+= bool(sout); NCTRL[len(ctrl)]+=1; R1[chess.piece_name(b.piece_type_at(m1.from_square))]+=1
    rows.append((E,ctrl,sout,meme,f,b.san(m1),rep,m2))
print("Pièce qui donne le mat (l'exécutant) :",dict(EX))
print("Pièce qui joue le premier coup (l'échec) :",dict(R1))
print(f"Le même pièce joue l'échec puis le mat : {MEME}/{len(trouve)} ; l'exécutant est protégé par une autre pièce ou le Roi : {AVEC_SOUTIEN}/{len(trouve)}")
print("Nombre de contrôleurs (hors exécutant, hors pions) :",dict(sorted(NCTRL.items())))
import json; json.dump([(f,str(m1),str(rep),str(m2)) for f,(m1,rep,m2) in trouve.items()],open('resultats/famille_mat2.json','w'))
print("\n12 exemples variés (un par exécutant et par premier coup quand c'est possible) :")
vus_cat=set(); k=0
for E,ctrl,sout,meme,f,san1,rep,m2 in sorted(rows,key=lambda r:(r[0],len(r[1]))):
    cat=(E,len(ctrl),meme)
    if cat in vus_cat or k>=12: continue
    vus_cat.add(cat); k+=1; b=chess.Board(f); bb=b.copy(); bb.push_san(san1); bb.push(rep); san2=bb.san(m2)
    print(f"  {k:2}. exécutant {E:7} | contrôleurs {ctrl} | soutien {sout} | {'même pièce' if meme else 'pièces différentes'}\n      {f}\n      1.{san1} {chess.Board(f).san(chess.Move.from_uci(str(chess.Board(f).parse_san(san1))))[:0]}{bb.san(rep) if False else ''} … 2.{san2}")
