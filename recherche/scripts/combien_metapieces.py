#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
combien_metapieces.py -- combien de Métapièces faut-il construire contre un Roi pour le mater ?
DÉFINITIONS (première approximation, à corriger par l'auteur) :
  zone du Roi = sa case + les cases adjacentes ; attaquants = Cavaliers, Fous, Tours, Dames qui attaquent au moins une case de la zone ;
  groupe relié = attaquants reliés de proche en proche par une case de la zone attaquée en commun ; Métapièce = le plus grand groupe relié (au moins 2 pièces) ;
  identité = suivi de chaque pièce coup après coup ; une Métapièce CONSTRUITE = un noyau d'au moins 2 mêmes pièces qui reste relié au moins P demi-coups
  (une interruption de 3 demi-coups au plus est tolérée) ; un nouveau noyau = moins de 2 pièces communes avec le précédent.
  Chaque camp est suivi contre le Roi adverse : on compare le camp qui MATE et le camp MATÉ (qui attaque aussi).
USAGE : cd donnees ; python3 ../recherche/scripts/combien_metapieces.py"""
import re, io, chess, chess.pgn, numpy as np, collections, statistics, time
t0=time.time(); PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def groupe_max(att):                       # att : {case: ensemble de cases de la zone} -> ensemble des cases du plus grand groupe relié
    ks=list(att); seen=set(); best=set()
    for k in ks:
        if k in seen: continue
        pile=[k]; seen.add(k); g=set()
        while pile:
            u=pile.pop(); g.add(u)
            for v in ks:
                if v not in seen and att[u]&att[v]: seen.add(v); pile.append(v)
        if len(g)>len(best): best=g
    return best
def partie(g):
    b=g.board(); ids={s:i for i,s in enumerate(b.piece_map())}; mv=list(g.mainline_moves()); trk={chess.WHITE:dict(core=None,debut=0,vu=0,taille=0,fait=[]),chess.BLACK:dict(core=None,debut=0,vu=0,taille=0,fait=[])}
    def clore(c,t):
        T=trk[c]
        if T['core'] is not None: T['fait'].append((T['debut'],T['vu'],T['taille'],t)); T['core']=None
    for t,m in enumerate(mv,1):
        f,to=m.from_square,m.to_square; pid=ids.pop(f,None)
        if b.is_en_passant(m): ids.pop(chess.square(chess.square_file(to),chess.square_rank(f)),None)
        else: ids.pop(to,None)
        if b.is_castling(m):
            r=chess.square_rank(to)
            if chess.square_file(to)==6: ids[chess.square(5,r)]=ids.pop(chess.square(7,r),None)
            else: ids[chess.square(3,r)]=ids.pop(chess.square(0,r),None)
        ids[to]=pid; b.push(m)
        if t<10: continue
        for col in (chess.WHITE,chess.BLACK):
            dk=b.king(not col)
            if dk is None: continue
            z=[dk]+list(b.attacks(dk)); pa={}
            for sq in z:
                for s in b.attackers(col,sq):
                    if b.piece_type_at(s) in PCS: pa.setdefault(s,set()).add(sq)
            G=groupe_max(pa) if len(pa)>=2 else set(); G={ids.get(s) for s in G} if len(G)>=2 else set(); T=trk[col]
            if G:
                if T['core'] is not None and len(G&T['core'])>=2: T['core']=G; T['vu']=t; T['taille']=max(T['taille'],len(G))
                else:
                    clore(col,t); T['core']=G; T['debut']=t; T['vu']=t; T['taille']=len(G)
            elif T['core'] is not None and t-T['vu']>=4: clore(col,t)
    fin=len(mv)
    actif={}
    for col in (chess.WHITE,chess.BLACK):
        T=trk[col]; actif[col]=T['core'] is not None and fin-T['vu']<=3
        clore(col,fin)
    return b,trk,actif,fin
res=[]; vus=set()
def fichiers_pgn(defaut=('twic1637.pgn','twic1662.pgn')):
    """Fichiers PGN à analyser : ceux donnés en arguments (jokers acceptés, par exemple parties*.pgn),
    sinon les deux numéros TWIC par défaut, placés dans le dossier courant."""
    import sys, glob
    demandes=[a for a in sys.argv[1:] if a.lower().endswith('.pgn') or ('*' in a and '.pgn' in a.lower())]
    liste=[]
    for a in demandes: liste+=sorted(glob.glob(a)) or [a]
    return liste or list(defaut)

for fn in fichiers_pgn():
    c=open(fn,encoding='utf-8',errors='ignore').read()
    for bloc in re.split(r'\n\n(?=\[Event)',c):
        cle=re.sub(r'\s+',' ',bloc.split('\n\n',1)[-1])
        if cle in vus: continue
        vus.add(cle); r=re.search(r'\[Result "([^"]+)"\]',bloc)
        if not r or r.group(1) not in ('1-0','0-1') or '#' not in cle: continue
        try: g=chess.pgn.read_game(io.StringIO(bloc)); b,trk,actif,fin=partie(g)
        except Exception: continue
        if not b.is_checkmate(): continue
        mat=not b.turn; mate=b.turn
        res.append(dict(fin=fin,fait={c:trk[c]['fait'] for c in trk},actif=actif,mat=mat,mate=mate))
print(f"{len(res)} parties terminées par un mat analysées ({time.time()-t0:.0f} s)")
def dist(vals):
    n=len(vals); cn=collections.Counter(min(v,4) for v in vals)
    return " | ".join(f"{k if k<4 else '4+'} : {100*cn.get(k,0)/n:4.1f} %" for k in range(5)), statistics.median(vals), sum(vals)/n
for P in (2,4,6):
    print(f"\n=== MÉTAPIÈCES CONSTRUITES (noyau relié au moins {P} demi-coups) ===")
    vm=[sum(1 for (d,v,tl,t) in x['fait'][x['mat']] if v-d+1>=P) for x in res]
    vd=[sum(1 for (d,v,tl,t) in x['fait'][x['mate']] if v-d+1>=P) for x in res]
    s,md,mo=dist(vm); print(f"   camp qui MATE  : {s}   médiane {md:.0f}, moyenne {mo:.2f}")
    s,md,mo=dist(vd); print(f"   camp MATÉ      : {s}   médiane {md:.0f}, moyenne {mo:.2f}")
    prem=sum(1 for a,b_ in zip(vm,vd) if a>b_); egal=sum(1 for a,b_ in zip(vm,vd) if a==b_); moins=sum(1 for a,b_ in zip(vm,vd) if a<b_)
    print(f"   dans la même partie, le camp qui mate en construit : plus {100*prem/len(res):.0f} % | autant {100*egal/len(res):.0f} % | moins {100*moins/len(res):.0f} %")
act=sum(1 for x in res if x['actif'][x['mat']])/len(res); print(f"\nAu moment du mat, une Métapièce reliée est ACTIVE pour le camp qui mate dans {100*act:.0f} % des parties (au sens de la convergence : rappel, la complémentarité conclut).")
P=4; fm=[ [v-d+1 for (d,v,tl,t) in x['fait'][x['mat']] if v-d+1>=P] for x in res]; tailles=[[tl for (d,v,tl,t) in x['fait'][x['mat']] if v-d+1>=P] for x in res]
nonvide=[l for l in fm if l]; print(f"Durée d'une Métapièce construite (P = 4) : médiane {statistics.median([d for l in nonvide for d in l]):.0f} demi-coups ; taille maximale médiane {statistics.median([s for l in tailles for s in l]):.0f} pièces ; parties avec au moins une : {100*len(nonvide)/len(res):.0f} %.")
long=[x['fin'] for x in res]; print(f"Longueur médiane des parties : {statistics.median(long)/2:.0f} coups.")
