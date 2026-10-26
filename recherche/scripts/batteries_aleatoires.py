#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batteries_aleatoires.py -- valeur statique (NNUE Stockfish) d'une batterie, sur 120 structures de pions tirees au hasard.
(1) TOURS doublees sur la colonne d (d1+d2) vs cote a cote (d1+e1) vs dispersees (a1+h1), avec un obstacle noir sur la colonne d :
    aucun ; pion d5 non protege ; d5+c6 ; d5+c6+e6 ; imprenable en d3, d4, d6.
(2) DAME + FOU sur la diagonale b2-g7 : Dame b2 derriere Fou c3 (doublees) vs Dame e2 + Fou c3 (cote a cote) vs Dame d1 + Fou f1 (dispersees),
    avec un obstacle noir sur la diagonale : aucun ; pion e5 non protege ; e5+d6 ; e5+d6+f6 ; pion f6 protege par g7 ; f6 protege par g7 et e7.
Chaque structure sert de sa propre reference. Moyennes et erreurs types sur les structures valides.
Squelette : pions blancs tires sur les colonnes a, b, f, g, h (tours) ou a, f, g, h (dame+fou) ; pions noirs de base f7 g7 h7, plus a7 b7 c7 tires au hasard.
LIMITES : valeurs d'un reseau de neurones ; positions artificielles ; la protection et la distance ne sont pas independantes de la structure de soutien.
USAGE : python3 batteries_aleatoires.py <chemin_stockfish> <nb_structures>
"""
import sys, re, subprocess, random, statistics, chess
random.seed(2026)
sf=sys.argv[1]; N=int(sys.argv[2])
def squelette(fw,fn):
    blancs=[]; noirs=[]
    for f in fw:
        if random.random()<0.85: blancs.append(f+str(random.choice([2,2,3,4])))
    for f in fn:
        if random.random()<0.85: noirs.append(f+str(random.choice([7,7,6,5])))
    return blancs,noirs
def poser(b,liste,sym):
    for c in liste: b.set_piece_at(chess.parse_square(c),chess.Piece.from_symbol(sym))
def position(blancs,noirs,pieces_blanches,noirs_sup,pieces_noires_sup=()):
    b=chess.Board(None)
    poser(b,['g1'],'K'); poser(b,blancs,'P'); poser(b,pieces_blanches[0],'R') if pieces_blanches[1]=='R' else None
    return b
def batch_eval(fens):
    entree="uci\n"+''.join(f"position fen {f}\neval\nisready\n" for f in fens)+"quit\n"
    r=subprocess.run([sf],input=entree,capture_output=True,text=True,timeout=270)
    blocs=r.stdout.split("readyok")
    out=[]
    for bl in blocs[:len(fens)]:
        m=re.search(r"Final evaluation\s+([+-]?\d+\.\d+)",bl) or re.search(r"NNUE evaluation\s+([+-]?\d+\.\d+)",bl)
        out.append(float(m.group(1)) if m else None)
    return out
def stats(v):
    v=[x for x in v if x is not None]; 
    return (statistics.mean(v),statistics.stdev(v)/len(v)**0.5,len(v)) if len(v)>2 else (float('nan'),float('nan'),len(v))
# ---------- (1) TOURS
CASR=[("aucun obstacle",[]),("d5 seul (prenable)",['d5']),("d5 + c6 (1 soutien)",['d5','c6']),("d5 + c6 + e6 (imprenable)",['d5','c6','e6']),
      ("d3 imprenable (c4, e4)",['d3','c4','e4']),("d4 imprenable (c5, e5)",['d4','c5','e5']),("d6 imprenable (c7, e7)",['d6','c7','e7'])]
CONFR=[['d1','d2'],['d1','e1'],['a1','h1']]
def pos_tours(bl,nr,rooks,sup):
    b=chess.Board(None); poser(b,['g1'],'K'); poser(b,bl,'P'); poser(b,rooks,'R'); poser(b,['g8'],'k')
    noirs_pos=[c for c in nr if c not in sup]
    # retire du squelette tout pion noir sur les cases d'obstacle/soutien de la colonne c-e (reservees)
    poser(b,['f7','g7','h7'],'p'); poser(b,nr,'p'); poser(b,sup,'p'); poser(b,['a8','h8'],'r'); b.turn=chess.WHITE; return b
def structures_tours():
    out=[]
    while len(out)<N:
        bl,nr=squelette('abfgh','abfgh')
        # les pions c et e noirs sont réservés aux soutiens ; on s'assure que les cases de soutien sont libres
        out.append((bl,nr))
    return out
# ---------- (2) DAME + FOU
CASQ=[("aucun obstacle",[]),("e5 seul (prenable)",['e5']),("e5 + d6 (1 soutien)",['e5','d6']),("e5 + d6 + f6 (2 soutiens)",['e5','d6','f6']),
      ("f6 protégé par g7",['f6']),("f6 protégé par g7 et e7",['f6','e7'])]
CONFQ=[(['b2'],['c3']),(['e2'],['c3']),(['d1'],['f1'])]   # (Dame, Fou)
def pos_qf(bl,nr,conf,sup):
    b=chess.Board(None); poser(b,['g1'],'K'); poser(b,bl,'P'); poser(b,conf[0],'Q'); poser(b,conf[1],'B'); poser(b,['g8'],'k')
    poser(b,['f7','g7','h7'],'p'); poser(b,nr,'p'); poser(b,sup,'p'); poser(b,['a8','h8'],'r'); b.turn=chess.WHITE; return b
def lancer(nom,cas,conf,fabrique,fw,fn):
    fens=[]; idx=[]
    for s in range(N):
        bl,nr=squelette(fw,fn)
        for ci,(cn,sup) in enumerate(cas):
            for ki,cf in enumerate(conf):
                b=fabrique(bl,nr,cf,sup)
                if b.is_valid() and not b.is_check() and len(b.pieces(chess.PAWN,chess.BLACK))<=8 and len(b.pieces(chess.PAWN,chess.WHITE))<=8:
                    fens.append(b.fen()); idx.append((s,ci,ki))
    ev=batch_eval(fens); D={}
    for (s,ci,ki),e in zip(idx,ev):
        if e is not None: D.setdefault((s,ci),{})[ki]=e
    print(f"\n{nom} ({N} structures tirées ; {len(fens)} positions évaluées)")
    print(f"  {'obstacle':34}{'alignement':>14}{'activité':>14}{'gain batterie':>16}   n")
    for ci,(cn,sup) in enumerate(cas):
        al=[];ac=[];ga=[]
        for s in range(N):
            d=D.get((s,ci))
            if d and len(d)==3: al.append(d[0]-d[1]); ac.append(d[1]-d[2]); ga.append(d[0]-d[2])
        a=stats(al);c=stats(ac);g=stats(ga)
        print(f"  {cn:34}{a[0]:+8.2f} ±{a[1]:4.2f}{c[0]:+8.2f} ±{c[1]:4.2f}{g[0]:+10.2f} ±{g[1]:4.2f}  {a[2]}")
lancer("(1) TOURS doublées sur la colonne d",CASR,CONFR,pos_tours,'abfgh','abfgh')
lancer("(2) DAME + FOU sur la diagonale b2-g7",CASQ,CONFQ,pos_qf,'afgh','abc')
