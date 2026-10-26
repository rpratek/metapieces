#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
erreurs_config.py -- erreurs graves selon la configuration de roque et le nombre de pieces (Stockfish, profondeur 10).
USAGE : python3 erreurs_config.py <OPP|PP|CC> <budget_en_secondes> <nb_parties_a_selectionner>
Etape 1 : lancer avec un budget de 1 s pour creer la selection ; etape 2 : lancer avec ~250 s, autant de fois que necessaire
(le script reprend ou il s'est arrete). Chaque appel doit rester sous 300 s.
"""
import re, io, random, time, json, os, sys
import chess, chess.pgn, chess.engine
CFG=sys.argv[1]; BUDGET=float(sys.argv[2]); NMAX=int(sys.argv[3]) if len(sys.argv)>3 else 600
STATE=f'donnees/err_cfg_{CFG}.json'
BINS=[(28,32,"28-32"),(24,27,"24-27"),(20,23,"20-23"),(16,19,"16-19"),(12,15,"12-15"),(8,11,"8-11")]
def tr(n):
    for a,b,nom in BINS:
        if a<=n<=b: return nom
def config(mv,b0):
    b=b0.copy(); r={True:None,False:None}
    for m in mv:
        if b.is_castling(m): r[b.turn]='c' if chess.square_file(m.to_square)==2 else 'p'
        b.push(m)
    if r[True] and r[False]: return ('CC' if r[True]=='c' else 'PP') if r[True]==r[False] else 'OPP'
    return 'incomplet'
if not os.path.exists(f'donnees/parties_{CFG}.json'):
    random.seed(23); sel=[]; vus=set()
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
            vus.add(cle)
            try: g=chess.pgn.read_game(io.StringIO(bloc)); mv=list(g.mainline_moves())
            except Exception: continue
            if len(mv)>=20 and config(mv,g.board())==CFG: sel.append(bloc)
    random.shuffle(sel); json.dump(sel[:NMAX],open(f'donnees/parties_{CFG}.json','w'))
parties=json.load(open(f'donnees/parties_{CFG}.json'))[:400]
st=json.load(open(STATE)) if os.path.exists(STATE) else {"i":0,"bins":{b[2]:{"n":0,"ouvert":0,"perte":0.0,"g150":0,"g300":0,"decide":0} for b in BINS}}
eng=chess.engine.SimpleEngine.popen_uci(os.environ.get("STOCKFISH","/usr/games/stockfish")); eng.configure({"Threads":1,"Hash":64})
def ev(b):
    s=eng.analyse(b,chess.engine.Limit(depth=10))['score'].white().score(mate_score=1000); return max(-1000,min(1000,s))
t0=time.time(); ng=0
while st["i"]<len(parties) and time.time()-t0<BUDGET:
    bloc=parties[st["i"]]; st["i"]+=1
    g=chess.pgn.read_game(io.StringIO(bloc)); mv=list(g.mainline_moves()); b=g.board(); e0=None; ng+=1
    for m in mv:
        n=len(b.piece_map()); blanc=b.turn
        if 8<=n<=32:
            if e0 is None: e0=ev(b)
            b.push(m); e1=ev(b); B=st["bins"][tr(n)]; B["n"]+=1
            if abs(e0)>600: B["decide"]+=1
            else:
                perte=max(0,(e0-e1) if blanc else (e1-e0)); B["ouvert"]+=1; B["perte"]+=perte; B["g150"]+=perte>=150; B["g300"]+=perte>=300
            e0=e1
        else: b.push(m); e0=None
eng.quit(); json.dump(st,open(STATE,'w'))
print(f"{CFG} : {st['i']}/{len(parties)} parties traitées | {sum(B['n'] for B in st['bins'].values())} coups | {time.time()-t0:.0f} s")
