#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
variantes_partie_8_5.py -- contrôles complémentaires de la partie commentée de la section 8.5
(Vachier-Lagrave - Nepomniachtchi, Julius Baer Generation Cup 2024).

Pour les coups blancs 28 à 32, puis pour les deux variantes du coup 31, ce script mesure :
  - combien de coups blancs restent à moins d'un pion du meilleur coup (le « tunnel ») ;
  - combien de coups conservent la victoire (évaluation >= +3) parmi les coups légaux ;
  - l'évaluation après 31.Qh4 (le coup naturel) et après 31.Re8 (le coup de la partie), avec la meilleure réponse noire.

MOTEUR : Stockfish, UN SEUL FIL, PROFONDEUR FIXE (22 par défaut), mémoire du moteur vidée avant chaque analyse.
Les valeurs varient avec la profondeur et la version du moteur : un résultat sans sa profondeur n'est pas une mesure.
USAGE : python3 variantes_partie_8_5.py vachier_lagrave_nepomniachtchi_2024.pgn [--profondeur 22]
Durée : une dizaine de minutes à la profondeur 22.
"""
import sys,argparse,chess,chess.pgn,chess.engine
ap=argparse.ArgumentParser(); ap.add_argument('pgn'); ap.add_argument('--profondeur',type=int,default=22); a=ap.parse_args()
g=chess.pgn.read_game(open(a.pgn,encoding='utf-8')); mv=list(g.mainline_moves())
eng=chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish' if __import__('os').path.exists('/usr/games/stockfish') else 'stockfish'); eng.configure({"Threads":1,"Hash":128})
def ana(b,**kw):
    eng.configure({"Clear Hash":None}); return eng.analyse(b,chess.engine.Limit(depth=a.profondeur),**kw)
print(f"Stockfish, un seul fil, profondeur {a.profondeur}\n")
b=g.board()
for m in mv:
    if b.turn==chess.WHITE and b.fullmove_number in (28,29,30,31,32):
        nb=b.legal_moves.count(); infos=ana(b,multipv=min(nb,40))
        sc=sorted([(i['score'].white().score(mate_score=10000),b.san(i['pv'][0])) for i in infos if i.get('pv')],reverse=True); best=sc[0][0]
        print(f"coup {b.fullmove_number}. : meilleur {sc[0][1]} ({best/100:+.2f}) ; coups à moins d'un pion du meilleur : {sum(1 for s,_ in sc if best-s<=100)} sur {nb} ; coups à + 3 ou plus : {sum(1 for s,_ in sc if s>=300)}",flush=True)
    b.push(m)
b=g.board()
for m in mv[:60]: b.push(m)          # position avant 31.Re8 (après 30...Qd8), Blancs au trait
for san in ('Qh4','Re8'):
    c=b.copy(); c.push(c.parse_san(san)); infos=ana(c,multipv=3)
    print(f"31.{san} : meilleures réponses noires : "+", ".join(f"{c.san(i['pv'][0])} ({i['score'].white().score(mate_score=10000)/100:+.2f})" for i in infos),flush=True)
eng.quit()
