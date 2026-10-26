#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poker_proba.py -- frequences exactes des mains de 5 cartes (jeu de 52 cartes, sans joker), par enumeration complete des 2 598 960 mains.
Sert d'etayage chiffre au chapitre 6 (jeux de cartes) : plus un ensemble de cartes coordonnees est grand, plus il est rare.
USAGE : python3 poker_proba.py
"""
import itertools, collections
vals=range(13); mains=collections.Counter(); total=0
cartes=[(v,s) for v in vals for s in range(4)]
for h in itertools.combinations(cartes,5):
    total+=1
    v=sorted(c[0] for c in h); s=len({c[1] for c in h})
    cnt=sorted(collections.Counter(v).values(),reverse=True)
    suite=(len(set(v))==5 and (v[4]-v[0]==4 or v==[0,1,2,3,12]))
    if suite and s==1: m='quinte flush'
    elif cnt==[4,1]: m='carré'
    elif cnt==[3,2]: m='full'
    elif s==1: m='couleur'
    elif suite: m='quinte'
    elif cnt==[3,1,1]: m='brelan'
    elif cnt==[2,2,1]: m='double paire'
    elif cnt==[2,1,1,1]: m='paire'
    else: m='carte haute'
    mains[m]+=1
print(total,"mains")
for m,n in sorted(mains.items(),key=lambda z:z[1]):
    print(f"{m:14} {n:9} mains  {n/total*100:9.4f} %  (1 sur {total/n:,.0f})".replace(',',' '))
