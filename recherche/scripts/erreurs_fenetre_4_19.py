#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
erreurs_fenetre_4_19.py -- taux d'erreurs graves selon le nombre de pieces (fenetre 4 a 19 pieces).
Stockfish profondeur 10 ; perte d'un coup = baisse d'evaluation pour le joueur au trait ; erreurs >= 150 et >= 300 centipions ;
positions deja decidees (|eval| > 600) comptees a part. Reprend ou il s'est arrete (fichier d'etat .json).
USAGE : python3 erreurs_fenetre_4_19.py <budget_en_secondes>      (twic1637.pgn et twic1662.pgn dans le dossier courant)
"""
import re, io, random, time, json, os, sys, math
import chess, chess.pgn, chess.engine
STATE='donnees/err_state.json'
BINS=[(16,19,"16-19"),(12,15,"12-15"),(8,11,"8-11"),(4,7,"4-7")]
def tr(n):
    for a,b,nom in BINS:
        if a<=n<=b: return nom
random.seed(11)
parties=[]; vus=set()
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
        if '[Result "*' in bloc: continue
        parties.append(bloc)
random.shuffle(parties)
st=json.load(open(STATE)) if os.path.exists(STATE) else {"i":0,"bins":{b[2]:{"n":0,"ouvert":0,"perte":0.0,"g150":0,"g300":0,"decide":0} for b in BINS}}
eng=chess.engine.SimpleEngine.popen_uci(os.environ.get("STOCKFISH","/usr/games/stockfish")); eng.configure({"Threads":1,"Hash":64})
def ev(b):
    s=eng.analyse(b,chess.engine.Limit(depth=10))['score'].white().score(mate_score=1000); return max(-1000,min(1000,s))
BUDGET=float(sys.argv[1]); t0=time.time(); ng=0
while st["i"]<len(parties) and time.time()-t0<BUDGET:
    bloc=parties[st["i"]]; st["i"]+=1
    try: g=chess.pgn.read_game(io.StringIO(bloc)); mv=list(g.mainline_moves())
    except Exception: continue
    b=g.board(); e0=None; ng+=1
    for m in mv:
        n=len(b.piece_map()); blanc=b.turn
        if 4<=n<=19:
            if e0 is None: e0=ev(b)
            b.push(m); e1=ev(b); nom=tr(n); B=st["bins"][nom]; B["n"]+=1
            if abs(e0)>600: B["decide"]+=1
            else:
                perte=max(0,(e0-e1) if blanc else (e1-e0)); B["ouvert"]+=1; B["perte"]+=perte
                B["g150"]+= perte>=150; B["g300"]+= perte>=300
            e0=e1
        else:
            b.push(m); e0=None
eng.quit(); json.dump(st,open(STATE,'w'))
print(f"parties traitées dans cette passe : {ng} | total traité : {st['i']}/{len(parties)} | durée {time.time()-t0:.0f} s")
tot=sum(B["n"] for B in st["bins"].values()); print("coups évalués au total :",tot)
