#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metapiece_territoire.py -- Metapiece et Territoire : une page HTML5 interactive tiree d'un fichier PGN.

Pour chaque demi-coup de la partie, et pour chaque camp, le programme calcule :
  - le TERRITOIRE de chaque piece (Cavalier, Fou, Tour, Dame) = les cases qu'elle attaque ou protege ;
  - la METAPIECE EN COURS = les pieces dont les territoires convergent (au moins une case attaquee par deux pieces
    du meme camp) ; sinon la piece dont le territoire est le plus etendu (un Monome) ;
  - les CASES DE FUITE du Roi adverse : libres (aucune piece du camp ne les attaque), fermees (attaquees),
    ou occupees par ses propres pieces ;
  - le FLUX : somme des poids des cases du territoire (4 coeur, 3 zone c3-f6, 2 couronne, 1 bord), hors cases occupees par ses propres pieces.
La page produite est autonome (aucun serveur, aucune connexion) : on l'ouvre en double-cliquant.

LIMITES : definition operationnelle de la Metapiece (convergence des territoires), les pions ne forment pas de territoire,
clouages et echecs ignores pour les cases de fuite. C'est un outil de lecture, non une evaluation.

USAGE   : python3 metapiece_territoire.py partie.pgn [-o sortie.html] [--partie N]
DEPEND. : python-chess (pip install chess)
"""
import sys, json, argparse, collections, html
import chess, chess.pgn, chess.svg
NOMS={chess.KNIGHT:'N',chess.BISHOP:'B',chess.ROOK:'R',chess.QUEEN:'Q'}
NOMS_P=dict(NOMS); NOMS_P[chess.PAWN]='P'
FR=str.maketrans({'K':'R','Q':'D','R':'T','B':'F','N':'C'})
def poids(s):
    f,r=chess.square_file(s),chess.square_rank(s)
    if f in (3,4) and r in (3,4): return 4
    if 2<=f<=5 and 2<=r<=5: return 3
    if 1<=f<=6 and 1<=r<=6: return 2
    return 1
nom=chess.square_name
def avance(sq,couleur):
    """pion avance : a franchi la moitie de l'echiquier (5e rangee ou plus pour les Blancs, 4e ou moins pour les Noirs)"""
    r=chess.square_rank(sq); return r>=4 if couleur==chess.WHITE else r<=3
def composantes(cases):
    """tailles des zones d'un seul tenant (cases voisines, diagonales comprises), de la plus grande a la plus petite"""
    reste=set(cases); tailles=[]
    while reste:
        pile=[reste.pop()]; n=1
        while pile:
            c=pile.pop()
            for t in [t for t in reste if chess.square_distance(c,t)==1]: reste.discard(t); pile.append(t); n+=1
        tailles.append(n)
    return sorted(tailles,reverse=True)
def analyser(board,couleur,pions=False):
    NM=NOMS_P if pions else NOMS
    ennemi=not couleur; pieces=[]
    # Le Roi adverse est retire du calcul des attaques : une piece a longue portee qui lui donne echec controle aussi
    # la case situee DERRIERE lui sur la meme ligne (il ne peut pas fuir en restant sur la ligne de l'echec).
    sans_roi=board.copy(); K0=board.king(ennemi)
    if K0 is not None: sans_roi.remove_piece_at(K0)
    for sq,p in board.piece_map().items():
        if p.color==couleur and p.piece_type in NM and (p.piece_type!=chess.PAWN or avance(sq,couleur)): pieces.append((sq,p.piece_type,set(sans_roi.attacks(sq))))
    cnt=collections.Counter(s for _,_,a in pieces for s in a); conv={s for s,n in cnt.items() if n>=2}
    membres=[x for x in pieces if x[2]&conv]
    if not membres and pieces: membres=[max([x for x in pieces if x[1]!=chess.PAWN] or pieces,key=lambda x:sum(poids(s) for s in x[2]))]
    cnt2=collections.Counter(s for _,_,a in membres for s in a)
    union=set().union(*[a for _,_,a in membres]) if membres else set()
    propres=board.occupied_co[couleur]
    flux=sum(poids(s) for s in union if not (propres>>s)&1)
    K=board.king(ennemi); fu={'libres':[],'fermees':[],'propres':[]}
    if K is not None:
        for s in chess.SQUARES:
            if chess.square_distance(s,K)!=1: continue
            occ=board.piece_at(s)
            if occ and occ.color==ennemi: fu['propres'].append(nom(s))
            elif sans_roi.is_attacked_by(couleur,s): fu['fermees'].append(nom(s))
            else: fu['libres'].append(nom(s))
    return {'membres':[{'case':nom(sq),'piece':NM[pt],'att':sorted(nom(s) for s in a)} for sq,pt,a in sorted(membres,key=lambda x:-x[1])],
            'conv':{nom(s):n for s,n in cnt2.items() if n>=2},'flux':flux,'cases':len(union),
            'roi_adverse':nom(K) if K is not None else None,'fuites':fu,'union':sorted(nom(s) for s in union),'zones':composantes(union)}
SYM={chess.PAWN:'P',chess.KNIGHT:'N',chess.BISHOP:'B',chess.ROOK:'R',chess.QUEEN:'Q'}
def attaques_pieces(board,couleur):
    """{case: (type, cases controlees)} pour les pieces de la couleur (Roi exclu), le Roi adverse etant retire du calcul"""
    sr=board.copy(); K=board.king(not couleur)
    if K is not None: sr.remove_piece_at(K)
    return {s:(p.piece_type,set(sr.attacks(s))) for s,p in board.piece_map().items() if p.color==couleur and p.piece_type!=chess.KING}
def fins(s,t,cases):
    """pointes de fleches : pour une piece a longue portee, la case la plus eloignee de chaque direction ; sinon chaque case"""
    if t in (chess.BISHOP,chess.ROOK,chess.QUEEN):
        best={}
        for c in cases:
            df=chess.square_file(c)-chess.square_file(s); dr=chess.square_rank(c)-chess.square_rank(s)
            d=((df>0)-(df<0),(dr>0)-(dr<0)); dist=max(abs(df),abs(dr))
            if d not in best or dist>best[d][0]: best[d]=(dist,c)
        return sorted(nom(c) for _,c in best.values())
    return sorted(nom(c) for c in cases)
def fleches_coup(prev,cur,coup,couleur,complet=False):
    """cases gagnees et perdues par chaque piece de la couleur, a ce demi-coup (la piece deplacee est comparee a elle-meme)"""
    A0=attaques_pieces(prev,couleur); A1=attaques_pieces(cur,couleur)
    corr={s:s for s in A1}
    p_to=cur.piece_at(coup.to_square)
    if p_to is not None and p_to.color==couleur: corr[coup.to_square]=coup.from_square
    if prev.is_castling(coup) and prev.turn==couleur:
        r=chess.square_rank(coup.from_square); kingside=chess.square_file(coup.to_square)>chess.square_file(coup.from_square)
        corr[chess.square(5 if kingside else 3,r)]=chess.square(7 if kingside else 0,r)
    utilises=set(); out=[]; pg=pp=0
    for s1,(t1,a1) in A1.items():
        s0=corr.get(s1,s1)
        if s0 in A0: t0,a0=A0[s0]; utilises.add(s0)
        else: a0=set()
        g=a1-a0; l=a0-a1
        if g or l:
            wg=sum(poids(c) for c in g); wl=sum(poids(c) for c in l); pg+=wg; pp+=wl
            e={'de':nom(s1),'de0':nom(s0),'piece':SYM[t1],'gagne':fins(s1,t1,g),'perdu':fins(s0,t1,l),'pg':wg,'pp':wl,'pris':False}
            if complet: e['g']=g; e['l']=l
            out.append(e)
    for s0,(t0,a0) in A0.items():
        if s0 not in utilises and a0:
            wl=sum(poids(c) for c in a0); pp+=wl
            e={'de':nom(s0),'piece':SYM[t0],'gagne':[],'perdu':fins(s0,t0,a0),'pg':0,'pp':wl,'pris':True}
            if complet: e['g']=set(); e['l']=a0
            out.append(e)
    return out,pg,pp
def donnees(game):
    b=game.board(); plies=[]
    def entree(b,coup,san,num):
        return {'fen':b.board_fen(),'de':nom(coup.from_square) if coup else None,'a':nom(coup.to_square) if coup else None,
                'trait':None,'san':san,'num':num,'B':analyser(b,chess.WHITE),'N':analyser(b,chess.BLACK),'Bp':analyser(b,chess.WHITE,True),'Np':analyser(b,chess.BLACK,True)}
    plies.append(entree(b,None,'Position initiale',''))
    for coup in game.mainline_moves():
        blanc=b.turn==chess.WHITE; num=f"{b.fullmove_number}."+('' if blanc else '..'); san=b.san(coup).translate(FR)
        prec=b.copy(); b.push(coup); e=entree(b,coup,san,num); e['trait']='B' if blanc else 'N'
        for c,col in (('B',chess.WHITE),('N',chess.BLACK)):
            f,pg,pp=fleches_coup(prec,b,coup,col)
            for k in (c,c+'p'): e[k]['fleches']=f; e[k]['pg']=pg; e[k]['pp']=pp
        plies.append(e)
    for i,e in enumerate(plies):
        for c in ('B','N','Bp','Np'):
            cur=set(e[c]['union']); prec=set(plies[i-1][c]['union']) if i>0 else cur
            e[c]['nouvelles']=sorted(cur-prec); e[c]['eteintes']=sorted(prec-cur)
    h=game.headers
    return {'titre':f"{h.get('White','?')} – {h.get('Black','?')}",'sous_titre':' · '.join(x for x in (h.get('Event',''),h.get('Site',''),h.get('Date',''),h.get('Result','')) if x and x not in ('?','????.??.??')),'plies':plies}
MODELE=r'''<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Métapièce et Territoire — __TITRE__</title>
<style>
:root{--bleu:#1F3864;--brun:#7F4F1F;--gris:#595959}
body{font-family:"Times New Roman",serif;margin:0;background:#fff;color:#222}
header{padding:10px 18px;border-bottom:3px solid #C09060}
h1{margin:0;font-size:22px;color:var(--bleu)} h2{margin:2px 0 0;font-size:14px;font-weight:normal;color:var(--gris);font-style:italic}
main{display:flex;flex-wrap:wrap;gap:18px;padding:14px 18px;align-items:flex-start}
#gauche{flex:0 0 auto} #droite{flex:1 1 340px;min-width:320px;max-width:640px}
fieldset{border:1px solid #C09060;border-radius:4px;margin:0 0 10px;padding:6px 10px}
legend{color:var(--brun);font-weight:bold;font-size:13px} label{margin-right:14px;font-size:15px;cursor:pointer}
button{font-size:16px;padding:4px 12px;margin-right:4px;cursor:pointer;border:1px solid #C09060;background:#F7F1E8;border-radius:4px}
input[type=range]{width:100%}
#info{font-size:14px;line-height:1.45} #info .bloc{border-left:5px solid #ccc;padding:2px 8px;margin:0 0 8px;background:#fafafa}
#info .B{border-color:#1f6fb2} #info .N{border-color:#c0392b}
#coups{max-height:170px;overflow:auto;font-size:14px;line-height:1.7;border:1px solid #ddd;padding:4px 8px}
#coups span{cursor:pointer;padding:1px 3px;border-radius:3px} #coups span:hover{background:#eee} #coups span.cur{background:#C09060;color:#fff}
.legende{font-size:12.5px;color:var(--gris);margin-top:6px} .puce{display:inline-block;width:12px;height:12px;margin:0 3px -1px 8px;border:1px solid #888}
.allume{animation:allume .6s ease-out both} @keyframes allume{from{opacity:0}to{opacity:1}}
.ombre{animation:ombre 1.4s ease-in-out infinite alternate} @keyframes ombre{from{stroke-opacity:.3}to{stroke-opacity:1}}
.note{font-size:12px;color:var(--gris);font-style:italic;margin-top:10px}
</style></head><body>
<header><h1>Métapièce et Territoire — __TITRE__</h1><h2>__SOUS__</h2></header>
<main>
 <div id="gauche"><div id="plateau"></div><div class="legende" id="legende"></div></div>
 <div id="droite">
  <fieldset><legend>Camp à visualiser</legend>
   <label><input type="radio" name="camp" value="B" checked> Blancs</label>
   <label><input type="radio" name="camp" value="N"> Noirs</label>
   <label><input type="radio" name="camp" value="2"> Les deux camps (superposition)</label>
   <div style="margin-top:4px"><label><input type="checkbox" id="seul"> Ne parcourir que les coups du camp choisi</label></div>
  </fieldset>
  <fieldset><legend>Affichage</legend>
   <label><input type="radio" name="mode" value="bal" checked> Salle de bal (cases éclairées)</label>
   <label><input type="radio" name="mode" value="analyse"> Analyse (une couleur par pièce)</label>
   <div style="margin-top:4px"><label><input type="checkbox" id="pions"> Avec les pions (seuls les pions avancés, au-delà de la 4e rangée, comptent dans la Métapièce)</label></div>
   <div style="margin-top:4px">Ce que fait le coup :
    <label><input type="radio" name="quoi" value="rien"> rien</label>
    <label><input type="radio" name="quoi" value="cases" checked> cases (+ / −)</label>
    <label><input type="radio" name="quoi" value="fleches"> flèches (gagné / perdu)</label></div>
  </fieldset>
  <fieldset><legend>Demi-coup</legend>
   <button id="debut" title="Début">⏮</button><button id="prec" title="Précédent (←)">◀</button><button id="lecture" title="Lecture automatique">▶ Lecture</button><button id="suiv" title="Suivant (→)">▶</button><button id="fin" title="Fin">⏭</button>
   <input type="range" id="curseur" min="0" max="0" value="0"><div id="etiq" style="font-size:15px;margin-top:2px"></div>
  </fieldset>
  <div id="info"></div>
  <div id="graphe"></div>
  <div id="coups"></div>
  <div class="note">Territoire d’une pièce : cases qu’elle attaque ou protège. Métapièce en cours : pièces dont les territoires convergent (au moins une case attaquée par deux d’entre elles). Cases de fuite : voisines du Roi adverse. Flux : somme des poids des cases du territoire (4 cœur, 3 zone c3-f6, 2 couronne, 1 bord). Outil de lecture, non une évaluation.</div>
 </div>
</main>
<svg width="0" height="0" style="position:absolute"><defs><!--__DEFS__--></defs></svg>
<script>
const DATA = /*__DATA__*/null;
const COUL = {B:{N:'#1f6fb2',B:'#2e9e4f',R:'#7b4fb0',Q:'#12a5b8',P:'#c9a227'}, N:{N:'#c0392b',B:'#e67e22',R:'#b8a400',Q:'#d36aa8',P:'#8a6d9b'}};
const NOMPIECE = {N:'Cavalier',B:'Fou',R:'Tour',Q:'Dame',P:'Pion'}, LETTRE = {N:'C',B:'F',R:'T',Q:'D',P:'P'};
const NOMES = ['Aucune Métapièce','Monôme','Binôme','Trinôme','Quadrinôme','Pentanôme'];
let AFF = 'cases';
const S = 70, M = 32;
function xy(sq){ return [M + 'abcdefgh'.indexOf(sq[0])*S, M + (7-(parseInt(sq[1])-1))*S]; }
function camps(camp){ return camp==='2' ? ['B','N'] : [camp]; }
function nome(n){ return n<NOMES.length ? NOMES[n] : n+' pièces'; }
function pieceSymbole(c){ return ({p:'pawn',n:'knight',b:'bishop',r:'rook',q:'queen',k:'king'})[c.toLowerCase()]; }
function placement(fen){
  const out = []; const rangs = fen.split('/');
  for (let r=0;r<8;r++){ let f=0; for (const ch of rangs[r]){ if (/\d/.test(ch)) f+=parseInt(ch); else { out.push({sq:'abcdefgh'[f]+(8-r), id:(ch===ch.toUpperCase()?'white-':'black-')+pieceSymbole(ch)}); f++; } } }
  return out;
}
function marquesDiff(p, liste, neon){
  const vert = neon ? '#4cff9a' : '#1b9e4b', rouge = neon ? '#ff6b6b' : '#d62728'; let s='';
  for (const c of liste){ const d=p[c];
    for (const q of (d.eteintes||[])){ const [x,y]=xy(q); s += `<rect class="allume" x="${x+3}" y="${y+3}" width="${S-6}" height="${S-6}" fill="${rouge}" fill-opacity=".13" stroke="${rouge}" stroke-width="2.5" stroke-dasharray="6 4" rx="4"/><text x="${x+S/2}" y="${y+S/2+9}" text-anchor="middle" font-size="26" font-weight="bold" fill="${rouge}" opacity=".9">−</text>`; }
    for (const q of (d.nouvelles||[])){ const [x,y]=xy(q); s += `<rect class="allume" x="${x+3}" y="${y+3}" width="${S-6}" height="${S-6}" fill="none" stroke="${vert}" stroke-width="3.2" rx="4"/><text x="${x+10}" y="${y+22}" font-size="20" font-weight="bold" fill="${vert}">+</text>`; } }
  return s;
}
function marquesFleches(p, liste, neon){
  const vert = neon ? '#4cff9a' : '#1b9e4b', rouge = neon ? '#ff6b6b' : '#d62728', k = neon ? 'n' : 'c';
  let s = `<defs><marker id="ptV${k}" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="13" refY="8" orient="auto"><path d="M0,1 L15,8 L0,15 z" fill="${vert}"/></marker><marker id="ptR${k}" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="13" refY="8" orient="auto"><path d="M0,1 L15,8 L0,15 z" fill="${rouge}"/></marker></defs>`;
  const fl = (x0,y0,q,coul,mk,tirets)=>{ const [x1,y1]=ctr(q); const dx=x1-x0, dy=y1-y0, L=Math.hypot(dx,dy)||1, a=22/L, b=14/L;
    return `<line x1="${x0+dx*a}" y1="${y0+dy*a}" x2="${x1-dx*b}" y2="${y1-dy*b}" stroke="${coul}" stroke-width="4.5" stroke-linecap="round" ${tirets?'stroke-dasharray="8 6"':''} marker-end="url(#${mk})" opacity=".95" class="allume"/>`; };
  for (const c of liste){ for (const f of (p[c].fleches||[])){ const [x0,y0]=ctr(f.de);
    { const [xa,ya]=ctr(f.de0||f.de); for (const q of f.perdu) s += fl(xa,ya,q,rouge,'ptR'+k,true); }
    for (const q of f.gagne) s += fl(x0,y0,q,vert,'ptV'+k,false);
    if (f.pris) s += `<text x="${x0}" y="${y0+9}" text-anchor="middle" font-size="26" font-weight="bold" fill="${rouge}">✕</text>`; } }
  return s;
}
function svgAnalyse(idx, camp){
  const p = DATA.plies[idx], liste = camps(camp), taille = M + 8*S + 6;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${taille} ${taille}" width="${taille}" height="${taille}" font-family="Arial,sans-serif">`;
  s += `<defs><pattern id="hach" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" stroke="#6a1b9a" stroke-width="3.2"/></pattern></defs>`;
  for (let r=0;r<8;r++) for (let f=0;f<8;f++) s += `<rect x="${M+f*S}" y="${M+r*S}" width="${S}" height="${S}" fill="${(f+r)%2===0?'#FFFFFF':'#D0E2F5'}"/>`;
  s += `<rect x="${M-1}" y="${M-1}" width="${8*S+2}" height="${8*S+2}" fill="none" stroke="#9DB7D5" stroke-width="3"/>`;
  for (let i=0;i<8;i++){ s += `<text x="${M+i*S+S/2}" y="${M-9}" text-anchor="middle" font-size="17" fill="#506D93">${'abcdefgh'[i]}</text>`;
    s += `<text x="${M-14}" y="${M+i*S+S/2+6}" text-anchor="middle" font-size="17" fill="#506D93">${8-i}</text>`; }
  if (p.de){ for (const c of [p.de,p.a]){ const [x,y]=xy(c); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="#ffe066" fill-opacity="0.45"/>`; } }
  const dansTerr = {};
  for (const c of liste){ const d = p[c];
    for (const m of d.membres){ for (const q of m.att){ const [x,y]=xy(q); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="${COUL[c][m.piece]}" fill-opacity="0.27"/>`; (dansTerr[q]=dansTerr[q]||new Set()).add(c); } } }
  if (liste.length===2){ for (const q in dansTerr){ if (dansTerr[q].size===2){ const [x,y]=xy(q); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="url(#hach)" fill-opacity="0.55"/>`; } } }
  for (const c of liste){ const d = p[c];
    for (const q in d.conv){ const [x,y]=xy(q); s += `<rect x="${x+2}" y="${y+2}" width="${S-4}" height="${S-4}" fill="none" stroke="${c==='B'?'#0b3d91':'#8e1b10'}" stroke-width="3"/>`; s += `<text x="${x+S-8}" y="${y+16}" text-anchor="end" font-size="14" font-weight="bold" fill="${c==='B'?'#0b3d91':'#8e1b10'}">${d.conv[q]}</text>`; } }
  for (const c of liste){ const f = p[c].fuites;
    for (const q of f.libres){ const [x,y]=xy(q); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="#E6B9D4" fill-opacity="0.75"/><circle cx="${x+S/2}" cy="${y+S/2}" r="${S/2-6}" fill="none" stroke="#b0179b" stroke-width="3.5" stroke-dasharray="7 5"/>`; }
    for (const q of f.fermees){ const [x,y]=xy(q); s += `<path d="M${x+14} ${y+14} L${x+S-14} ${y+S-14} M${x+S-14} ${y+14} L${x+14} ${y+S-14}" stroke="#333" stroke-width="4" stroke-linecap="round" opacity="0.75"/>`; }
    for (const q of f.propres){ const [x,y]=xy(q); s += `<rect x="${x+6}" y="${y+6}" width="${S-12}" height="${S-12}" fill="none" stroke="#777" stroke-width="2.5" stroke-dasharray="3 4"/>`; } }
  if (AFF==='cases') s += marquesDiff(p, liste, false); else if (AFF==='fleches') s += marquesFleches(p, liste, false);
  for (const o of placement(p.fen)){ const [x,y]=xy(o.sq); s += `<use xlink:href="#${o.id}" href="#${o.id}" transform="translate(${x},${y}) scale(${S/45})"/>`; }
  for (const c of liste){ for (const m of DATA.plies[idx][c].membres){ const [x,y]=xy(m.case); s += `<rect x="${x+1.5}" y="${y+1.5}" width="${S-3}" height="${S-3}" fill="none" stroke="${COUL[c][m.piece]}" stroke-width="4" rx="6"/>`; } }
  return s + '</svg>';
}

const LUM = {B:{c:'#ffcf5a',b:'#ffe08a',g:'luB',p:'poolB'}, N:{c:'#6aa2ff',b:'#9ec1ff',g:'luN',p:'poolN'}};
function ctr(sq){ const [x,y]=xy(sq); return [x+S/2,y+S/2]; }
function svgBal(idx, camp){
  const p = DATA.plies[idx], liste = camps(camp), taille = M + 8*S + 6;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${taille} ${taille}" width="${taille}" height="${taille}" font-family="Arial,sans-serif">`;
  s += `<defs>`
    + `<radialGradient id="luB"><stop offset="0" stop-color="#fff6d0" stop-opacity=".95"/><stop offset=".4" stop-color="#ffcf5a" stop-opacity=".5"/><stop offset="1" stop-color="#ffcf5a" stop-opacity="0"/></radialGradient>`
    + `<radialGradient id="luN"><stop offset="0" stop-color="#e3eeff" stop-opacity=".95"/><stop offset=".4" stop-color="#6aa2ff" stop-opacity=".5"/><stop offset="1" stop-color="#6aa2ff" stop-opacity="0"/></radialGradient>`
    + `<radialGradient id="poolB"><stop offset="0" stop-color="#ffcf5a" stop-opacity=".6"/><stop offset="1" stop-color="#ffcf5a" stop-opacity="0"/></radialGradient>`
    + `<radialGradient id="poolN"><stop offset="0" stop-color="#6aa2ff" stop-opacity=".6"/><stop offset="1" stop-color="#6aa2ff" stop-opacity="0"/></radialGradient>`
    + `<filter id="halo" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="0" dy="0" stdDeviation="2.3" flood-color="#ffffff" flood-opacity="0.95"/></filter></defs>`;
  s += `<rect width="${taille}" height="${taille}" fill="#0e1226"/>`;
  for (let r=0;r<8;r++) for (let f=0;f<8;f++) s += `<rect x="${M+f*S}" y="${M+r*S}" width="${S}" height="${S}" fill="${(f+r)%2===0?'#2b3358':'#1f2646'}"/>`;
  s += `<rect x="${M-1}" y="${M-1}" width="${8*S+2}" height="${8*S+2}" fill="none" stroke="#b8963e" stroke-width="3"/>`;
  for (let i=0;i<8;i++){ s += `<text x="${M+i*S+S/2}" y="${M-9}" text-anchor="middle" font-size="17" fill="#c9b27a">${'abcdefgh'[i]}</text>`;
    s += `<text x="${M-14}" y="${M+i*S+S/2+6}" text-anchor="middle" font-size="17" fill="#c9b27a">${8-i}</text>`; }
  if (p.de){ for (const c of [p.de,p.a]){ const [x,y]=xy(c); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="#ffe066" fill-opacity="0.16"/>`; } }
  const eclaire = {};
  s += `<g style="isolation:isolate">`;
  for (const c of liste){ for (const m of p[c].membres){ const [cx,cy]=ctr(m.case);
    for (const q of m.att){ const [x,y]=xy(q), [qx,qy]=ctr(q);
      s += `<line class="allume" x1="${cx}" y1="${cy}" x2="${qx}" y2="${qy}" stroke="${LUM[c].c}" stroke-opacity=".11" stroke-width="5" stroke-linecap="round" style="mix-blend-mode:screen"/>`;
      s += `<rect class="allume" x="${x}" y="${y}" width="${S}" height="${S}" fill="${LUM[c].c}" fill-opacity=".27" style="mix-blend-mode:screen"/>`;
      s += `<rect class="allume" x="${x}" y="${y}" width="${S}" height="${S}" fill="url(#${LUM[c].p})" style="mix-blend-mode:screen"/>`;
      eclaire[q]=eclaire[q]||{}; eclaire[q][c]=(eclaire[q][c]||0)+1; } } }
  for (const c of liste){ for (const q in p[c].conv){ const [x,y]=xy(q);
    s += `<rect class="allume" x="${x}" y="${y}" width="${S}" height="${S}" fill="url(#${LUM[c].p})" style="mix-blend-mode:screen"/>`; } }
  s += `</g>`;
  for (const c of liste){ for (const m of p[c].membres){ const [cx,cy]=ctr(m.case); s += `<circle class="allume" cx="${cx}" cy="${cy}" r="${S*0.8}" fill="url(#${LUM[c].g})" style="mix-blend-mode:screen"/>`; } }
  for (const c of liste){ const d=p[c];
    for (const q in d.conv){ const [x,y]=xy(q); s += `<rect class="allume" x="${x+3}" y="${y+3}" width="${S-6}" height="${S-6}" fill="none" stroke="${LUM[c].b}" stroke-width="2.5" rx="5"/><text x="${x+S-9}" y="${y+17}" text-anchor="end" font-size="14" font-weight="bold" fill="#fff3c4">${d.conv[q]}</text>`; }
    for (const q of d.fuites.libres){ const [x,y]=xy(q); s += `<rect x="${x}" y="${y}" width="${S}" height="${S}" fill="#000" fill-opacity=".6"/><circle class="ombre" cx="${x+S/2}" cy="${y+S/2}" r="${S/2-6}" fill="none" stroke="#ff3d8b" stroke-width="3.5" stroke-dasharray="7 5"/>`; }
    for (const q of d.fuites.fermees){ const [x,y]=xy(q); s += `<path d="M${x+16} ${y+16} L${x+S-16} ${y+S-16} M${x+S-16} ${y+16} L${x+16} ${y+S-16}" stroke="#fff" stroke-width="3.5" stroke-linecap="round" opacity="0.8"/>`; }
    for (const q of d.fuites.propres){ const [x,y]=xy(q); s += `<rect x="${x+6}" y="${y+6}" width="${S-12}" height="${S-12}" fill="none" stroke="#8a93b8" stroke-width="2.5" stroke-dasharray="3 4"/>`; } }
  if (liste.length===2){ for (const q in eclaire){ if (eclaire[q].B && eclaire[q].N){ const [x,y]=xy(q); s += `<rect x="${x+1.5}" y="${y+1.5}" width="${S-3}" height="${S-3}" fill="none" stroke="#fff" stroke-width="1.8" stroke-dasharray="4 3"/>`; } } }
  if (AFF==='cases') s += marquesDiff(p, liste, true); else if (AFF==='fleches') s += marquesFleches(p, liste, true);
  for (const o of placement(p.fen)){ const [x,y]=xy(o.sq); s += `<use xlink:href="#${o.id}" href="#${o.id}" ${o.id.startsWith('black')?'filter="url(#halo)"':''} transform="translate(${x},${y}) scale(${S/45})"/>`; }
  for (const c of liste){ for (const m of p[c].membres){ const [x,y]=xy(m.case); s += `<rect x="${x+1.5}" y="${y+1.5}" width="${S-3}" height="${S-3}" fill="none" stroke="${LUM[c].b}" stroke-width="2.5" rx="6"/>`; } }
  return s + '</svg>';
}
function construireSVG(idx, camp, mode){ return mode==='analyse' ? svgAnalyse(idx,camp) : svgBal(idx,camp); }
function legendeBal(camp){
  let h=''; for (const c of camps(camp)) h+=`<div><span class="puce" style="background:${LUM[c].c}"></span><b>Lumière des ${c==='B'?'Blancs':'Noirs'}</b> : chaque pièce de la Métapièce est un lustre qui éclaire les cases qu’elle contrôle ; les lumières s’additionnent</div>`;
  h+=`<div><span class="puce" style="background:#000;border:2px dashed #ff3d8b"></span>zone d’ombre = fuite libre du Roi adverse <span class="puce" style="background:#555;color:#fff;text-align:center;line-height:11px;font-size:10px">✕</span>case éclairée : fuite fermée <span class="puce" style="background:#fff;border:3px solid #ffe08a"></span>plusieurs lustres convergent (chiffre = nombre de pièces)</div>`;
  if (camp==='2') h+=`<div><span class="puce" style="background:#fff;border:2px dashed #888"></span>cadre blanc pointillé : case éclairée par les deux camps</div>`;
  return h;
}
function libelleMeta(c, d){
  const pieces = d.membres.map(m=>LETTRE[m.piece]+m.case).join(', ');
  const conv = Object.keys(d.conv).length;
  const nm = d.membres.length>=2 || conv ? nome(d.membres.length) : (d.membres.length===1 ? 'Monôme' : 'Aucune Métapièce');
  const z=d.zones||[], nn=(d.nouvelles||[]).length, ee=(d.eteintes||[]).length;
  const cont = z.length ? (z.length>1 ? `${z.length} zones éclairées séparées (la plus grande : ${z[0]} cases)` : `une seule zone éclairée d’un seul tenant (${z[0]} cases)`) : 'aucune case éclairée';
  const pgn=d.pg||0, ppn=d.pp||0;
  const fle = (AFF==='fleches' && (pgn||ppn)) ? `<br>Ce coup : <b style="color:#1b9e4b">+${pgn} gagné</b>, <b style="color:#c0392b">−${ppn} perdu</b> (poids 4/3/2/1), solde <b>${pgn-ppn>=0?'+':''}${pgn-ppn}</b>` : '';
  const dif = (AFF==='cases' && (nn||ee)) ? `<br>Ce coup : <b style="color:#1b9e4b">+${nn} case(s) éclairée(s)</b>, <b style="color:#c0392b">−${ee} éteinte(s)</b>` : '';
  return `<b>${c==='B'?'Blancs':'Noirs'}</b> — ${nm}${pieces?' : '+pieces:''}<br>Territoire : ${d.cases} cases · flux pondéré : <b>${d.flux}</b> · cases où deux pièces convergent : ${conv}<br>Continuité : ${cont}${dif}${fle}`;
}
function libelleFuites(c, d){
  const f=d.fuites, roi=c==='B'?'noir':'blanc';
  if (!d.roi_adverse) return '';
  const lst = a => a.length ? a.join(', ') : '—';
  return `Roi ${roi} en ${d.roi_adverse} : <b>${f.libres.length} fuite(s) libre(s)</b> (${lst(f.libres)}) · fermées : ${f.fermees.length} (${lst(f.fermees)}) · occupées par ses pièces : ${f.propres.length}`;
}
function construireInfo(idx, camp){
  const p = DATA.plies[idx];
  return camps(camp).map(c=>`<div class="bloc ${c}">${libelleMeta(c,p[c])}<br>${libelleFuites(c,p[c])}</div>`).join('');
}
function construireGraphe(idx, camp){
  const W=620,H=96,P=14,n=DATA.plies.length; let max=1;
  for (const c of camps(camp)) for (const q of DATA.plies) max=Math.max(max,q[c].flux);
  const X=i=>P+(W-2*P)*i/Math.max(1,n-1), Y=v=>H-P-(H-2*P)*v/max;
  let s=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px;border:1px solid #ddd;margin:4px 0" font-family="Arial,sans-serif">`;
  s+=`<text x="${P}" y="11" font-size="11" fill="#555">Flux pondéré de la Métapièce, demi-coup par demi-coup (maximum ${max})</text>`;
  for (const c of camps(camp)){ let pts=''; DATA.plies.forEach((q,i)=>{pts+=`${X(i).toFixed(1)},${Y(q[c].flux).toFixed(1)} `;}); s+=`<polyline points="${pts}" fill="none" stroke="${c==='B'?'#1f6fb2':'#c0392b'}" stroke-width="2.2"/>`; }
  s+=`<line x1="${X(idx)}" y1="${P}" x2="${X(idx)}" y2="${H-P}" stroke="#C09060" stroke-width="2"/>`;
  return s+`</svg>`;
}
function legendeAnalyse(camp){
  let h=''; for (const c of camps(camp)){ h+=`<div><b>${c==='B'?'Blancs':'Noirs'}</b> :`; for (const t of ['N','B','R','Q','P']) h+=`<span class="puce" style="background:${COUL[c][t]};opacity:.6"></span>${NOMPIECE[t]}`; h+='</div>'; }
  h+=`<div><span class="puce" style="background:#E6B9D4;border:2px dashed #b0179b"></span>fuite libre du Roi adverse <span class="puce" style="background:#fff;border-color:#333">✕</span>fuite fermée <span class="puce" style="background:#fff;border:2px dashed #777"></span>occupée par ses pièces</div>`;
  h+=`<div><span class="puce" style="background:#fff;border:3px solid #0b3d91"></span>case où deux pièces convergent (chiffre = nombre de pièces)${camp==='2'?' <span class="puce" style="background:repeating-linear-gradient(45deg,#6a1b9a 0 3px,#fff 3px 7px)"></span>flux des deux camps superposés':''}</div>`;
  return h;
}
function construireLegende(camp, mode){ return (mode==='analyse' ? legendeAnalyse(camp) : legendeBal(camp)) + (AFF==='cases' ? `<div><span class="puce" style="background:#fff;border:3px solid #1b9e4b"></span>+ case qui vient de s’éclairer <span class="puce" style="background:#fff;border:2px dashed #d62728"></span>− case qui vient de s’éteindre (par ce coup, ou parce qu’une pièce adverse a coupé le rayon)</div>` : (AFF==='fleches' ? `<div><span class="puce" style="background:#1b9e4b"></span>flèche pleine : cases que la pièce vient de gagner <span class="puce" style="background:#fff;border:2px dashed #d62728"></span>flèche en tirets : cases qu’elle vient de perdre (✕ = pièce prise)</div>` : '')); }
function construireCoups(){
  let h=''; DATA.plies.forEach((q,i)=>{ if(i===0) return; h+=`<span data-i="${i}">${q.trait==='B'?q.num+'&nbsp;':''}${q.san}</span> `; }); return h;
}
function suivant(idx, camp, sens, seul){
  let i=idx+sens; if(!seul || camp==='2') return Math.max(0,Math.min(DATA.plies.length-1,i));
  while(i>=0 && i<DATA.plies.length){ if(i===0 || DATA.plies[i].trait===camp) return i; i+=sens; }
  return idx;
}
function init(){
  const el=id=>document.getElementById(id); let idx=0, camp='B', mode='bal', minuterie=null;
  const cur=el('curseur'); cur.max=DATA.plies.length-1;
  DATA.plies.forEach(q=>{ q.B0=q.B; q.N0=q.N; });
  const maj=()=>{ cur.value=idx; el('plateau').innerHTML=construireSVG(idx,camp,mode); el('info').innerHTML=construireInfo(idx,camp); el('graphe').innerHTML=construireGraphe(idx,camp); el('legende').innerHTML=construireLegende(camp,mode);
    const q=DATA.plies[idx]; el('etiq').textContent = idx===0 ? 'Position initiale' : (q.trait==='B'?q.num+' ':q.num+' ')+q.san+'  (demi-coup '+idx+' sur '+(DATA.plies.length-1)+')';
    document.querySelectorAll('#coups span').forEach(sp=>sp.classList.toggle('cur', parseInt(sp.dataset.i)===idx)); };
  el('coups').innerHTML=construireCoups();
  const aller=i=>{ idx=Math.max(0,Math.min(DATA.plies.length-1,i)); maj(); };
  const pas=s=>aller(suivant(idx,camp,s,el('seul').checked));
  el('suiv').onclick=()=>pas(1); el('prec').onclick=()=>pas(-1); el('debut').onclick=()=>aller(0); el('fin').onclick=()=>aller(DATA.plies.length-1);
  cur.oninput=()=>aller(parseInt(cur.value));
  el('lecture').onclick=()=>{ if(minuterie){clearInterval(minuterie);minuterie=null;el('lecture').textContent='▶ Lecture';} else { el('lecture').textContent='⏸ Pause'; minuterie=setInterval(()=>{ const n=suivant(idx,camp,1,el('seul').checked); if(n===idx){clearInterval(minuterie);minuterie=null;el('lecture').textContent='▶ Lecture';} else aller(n); },900); } };
  document.querySelectorAll('input[name=camp]').forEach(r=>r.onchange=()=>{ camp=r.value; maj(); });
  el('pions').onchange=()=>{ const ap=el('pions').checked; DATA.plies.forEach(q=>{ q.B=ap?q.Bp:q.B0; q.N=ap?q.Np:q.N0; }); maj(); };
  document.querySelectorAll('input[name=quoi]').forEach(r=>r.onchange=()=>{ AFF=r.value; maj(); });
  document.querySelectorAll('input[name=mode]').forEach(r=>r.onchange=()=>{ mode=r.value; maj(); });
  el('coups').onclick=e=>{ const t=e.target.closest('span'); if(t) aller(parseInt(t.dataset.i)); };
  document.addEventListener('keydown',e=>{ if(e.key==='ArrowRight') pas(1); else if(e.key==='ArrowLeft') pas(-1); });
  el('graphe').onclick=e=>{ const r=e.currentTarget.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width; aller(Math.round(x*(DATA.plies.length-1))); };
  maj();
}
if (typeof document!=='undefined' && document.getElementById('plateau')) init();
if (typeof module!=='undefined') module.exports={construireSVG,construireInfo,construireGraphe,construireLegende,suivant,DATA};
</script></body></html>
'''
def main():
    ap=argparse.ArgumentParser(description="Métapièce et Territoire : page HTML5 interactive tirée d'un PGN")
    ap.add_argument('pgn'); ap.add_argument('-o','--sortie'); ap.add_argument('--partie',type=int,default=1)
    a=ap.parse_args()
    with open(a.pgn,encoding='utf-8',errors='ignore') as f:
        g=None
        for _ in range(a.partie): g=chess.pgn.read_game(f)
    if g is None: sys.exit("Aucune partie trouvée dans le fichier.")
    d=donnees(g); defs=''.join(chess.svg.PIECES.values())
    page=MODELE.replace('<!--__DEFS__-->',defs).replace('/*__DATA__*/null',json.dumps(d,ensure_ascii=False)).replace('__TITRE__',html.escape(d['titre'])).replace('__SOUS__',html.escape(d['sous_titre']))
    sortie=a.sortie or a.pgn.rsplit('.',1)[0]+'_territoire.html'
    open(sortie,'w',encoding='utf-8').write(page); print(f"{len(d['plies'])-1} demi-coups analysés → {sortie} ({len(page)//1024} Ko)")
if __name__=='__main__': main()
