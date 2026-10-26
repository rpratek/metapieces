#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagramme_charte_bleue.py -- diagrammes « bleu et blanc » des Métapièces, reconstitués d'après les diagrammes existants du livre.
CHARTE MESURÉE sur image_ex2t_1.png (800 x 800 px) :
  toile blanche ; plateau de 768 px à partir de (32, 32) ; cases de 96 px
  cases claires #FFFFFF, cases sombres #D0E2F5 ; bord du plateau #9DB7D5 (3 px)
  coordonnées : LETTRES EN HAUT (a-h), CHIFFRES À GAUCHE (8-1), couleur #506D93, rien en bas ni à droite
  flèches et cercle des Tours #A63A3A ; cercle du Fou #A66A3A ; (Dame #6A3FA0 et Cavalier #2E6DB4 : choix provisoires, non mesurés)
  cases de fuite : rose translucide, #E6B9D4 sur case claire, #CCA9CF sur case sombre
  flèche numérotée : pastille blanche cerclée de rouge au milieu de la flèche
Pièces : jeu par défaut de python-chess (chess.svg), proche de celui du livre.
Dépendances : python-chess, cairosvg, Pillow.
USAGE : from diagramme_charte_bleue import dessiner ; dessiner(fen, 'sortie.png', fleches=[(case_depart, case_arrivee, numero)], cercles=[cases], zones=[cases_de_fuite], orientation=chess.WHITE ou chess.BLACK)
Orientation chess.BLACK : plateau vu du cote des Noirs (lettres h a a en haut, chiffres 1 a 8 a gauche).
"""
import chess, chess.svg, cairosvg, io
from PIL import Image, ImageDraw, ImageFont
COUL={chess.ROOK:'#A63A3A',chess.BISHOP:'#A66A3A',chess.QUEEN:'#6A3FA0',chess.KNIGHT:'#2E6DB4',chess.PAWN:'#A63A3A',chess.KING:'#6A3FA0'}
CLAIR,SOMBRE,BORD,TEXTE,ROUGE='#FFFFFF','#D0E2F5','#9DB7D5','#506D93','#A63A3A'
X0=Y0=32; TB=768; CASE=96
def _c(sq,u=45,ori=chess.WHITE):
    f,r=chess.square_file(sq),chess.square_rank(sq)
    return (u*f+u/2, u*(7-r)+u/2) if ori==chess.WHITE else (u*(7-f)+u/2, u*r+u/2)
def dessiner(fen,fichier,fleches=(),cercles=(),zones=(),orientation=chess.WHITE):
    b=chess.Board(fen)
    fill={z:('#E6B9D4' if (chess.square_file(z)+chess.square_rank(z))%2==1 else '#CCA9CF') for z in zones}
    svg=chess.svg.board(b,size=TB,coordinates=False,fill=fill,arrows=[chess.svg.Arrow(a,c,color=ROUGE) for a,c,n in fleches],
                        colors={'square light':CLAIR,'square dark':SOMBRE},orientation=orientation)
    ins=''.join(f'<circle cx="{_c(s,45,orientation)[0]}" cy="{_c(s,45,orientation)[1]}" r="20" fill="none" stroke="{COUL[b.piece_type_at(s)]}" stroke-width="3.2"/>' for s in cercles)
    for a,c,n in fleches:
        (x1,y1),(x2,y2)=_c(a,45,orientation),_c(c,45,orientation); mx,my=(x1+x2)/2,(y1+y2)/2
        ins+=f'<circle cx="{mx}" cy="{my}" r="9" fill="#FFFFFF" stroke="{ROUGE}" stroke-width="2"/><text x="{mx}" y="{my+4}" font-size="12" font-weight="bold" text-anchor="middle" fill="{ROUGE}" font-family="sans-serif">{n}</text>'
    svg=svg.replace('</svg>',ins+'</svg>')
    plateau=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=TB,output_height=TB))).convert('RGB')
    toile=Image.new('RGB',(800,800),'#FFFFFF'); toile.paste(plateau,(X0,Y0))
    d=ImageDraw.Draw(toile); d.rectangle([X0-1,Y0-1,X0+TB,Y0+TB],outline=BORD,width=3)
    try: f=ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',22)
    except Exception: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    lettres='abcdefgh' if orientation==chess.WHITE else 'hgfedcba'
    chiffres=[str(8-j) for j in range(8)] if orientation==chess.WHITE else [str(j+1) for j in range(8)]
    for i,l in enumerate(lettres): 
        w=d.textlength(l,font=f); d.text((X0+CASE*i+CASE/2-w/2,5),l,font=f,fill=TEXTE)
    for j in range(8):
        t=chiffres[j]; w=d.textlength(t,font=f); d.text((16-w/2,Y0+CASE*j+CASE/2-13),t,font=f,fill=TEXTE)
    toile.save(fichier)
