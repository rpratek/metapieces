#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
couple_moteur_exemple.py -- EXEMPLE VÉRIFIABLE du Couple Moteur de la Métapièce (formule du livre, page 44).

Aucune bibliothèque à installer. Lancer :  python3 couple_moteur_exemple.py

La formule est celle de couple_moteur_v2.py (régression logistique sur 297 709 positions de roque, TWIC 1637 et 1662),
écrite ici sous la forme de trois facteurs, avec les coefficients ARRONDIS à deux décimales comme dans le livre :

    cotes de mat = base x PUISSANCE x COOPÉRATION x EMBRAYAGE        probabilité = cotes / (1 + cotes)

    PUISSANCE   = 1,45 ^ attaquants  x  1,28 ^ attaquants lourds  x  2,41 ^ Dame (0 ou 1)
    COOPÉRATION = 1,45 ^ cases doublement visées  x  1,08 ^ plus grand groupe d'attaquants reliés
    EMBRAYAGE   = 0,57 ^ défenseurs (pièces + pions du bouclier)  x  0,66 ^ fuites libres du Roi        (toujours entre 0 et 1)

ATTENTION : proposition de lecture mesurée, pas une loi. Deux numéros de TWIC, Rois roqués, mat dans les 10 demi-coups.
Les coefficients du script complet (pleine précision) peuvent différer légèrement de ces valeurs arrondies.
"""
import math

BASE = math.exp(-3.28)          # 0,038 environ
FACTEURS = {                     # facteur multiplicatif par unité (e puissance coefficient)
    "attaquant":        math.exp(0.37),   # 1,45
    "case_doublement":  math.exp(0.37),   # 1,45
    "groupe_relie":     math.exp(0.08),   # 1,08
    "lourd":            math.exp(0.25),   # 1,28
    "dame":             math.exp(0.88),   # 2,41
    "defenseur":        math.exp(-0.57),  # 0,57
    "fuite":            math.exp(-0.42),  # 0,66
}

def couple_moteur(attaquants, cases_doublement_visees, groupe_relie, lourds, dame, defenseurs, fuites):
    puissance   = FACTEURS["attaquant"]**attaquants * FACTEURS["lourd"]**lourds * FACTEURS["dame"]**dame
    cooperation = FACTEURS["case_doublement"]**cases_doublement_visees * FACTEURS["groupe_relie"]**groupe_relie
    embrayage   = FACTEURS["defenseur"]**defenseurs * FACTEURS["fuite"]**fuites
    cotes = BASE * puissance * cooperation * embrayage
    return puissance, cooperation, embrayage, cotes / (1 + cotes)

EXEMPLES = [
    ("A. Attaque forte",   (5, 4, 4, 2, 1, 4, 1)),
    ("B. Attaque faible",  (2, 0, 1, 1, 0, 6, 2)),
    ("C. Dame enfermée",   (4, 1, 2, 2, 1, 8, 3)),
]

if __name__ == "__main__":
    print("%-20s %10s %12s %10s %12s" % ("Position", "Puissance", "Coopération", "Embrayage", "Mat (10 coups)"))
    for nom, args in EXEMPLES:
        p, c, e, prob = couple_moteur(*args)
        print("%-20s %10.1f %12.2f %10.3f %11.1f %%" % (nom, p, c, e, 100 * prob))
    print("\nParamètres de chaque exemple : attaquants, cases doublement visées, groupe relié, attaquants lourds, Dame (0/1), défenseurs, fuites")
    for nom, args in EXEMPLES:
        print("  ", nom, args)
