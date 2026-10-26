import chess, chess.svg, chess.pgn, chess.engine, io, json, cairosvg, os, sys
# Usage : python3 carlsen.py [chemin_vers_stockfish]   (par defaut : stockfish dans le PATH)
os.chdir(os.path.dirname(os.path.abspath(__file__))); os.makedirs('resultats',exist_ok=True)
SF=sys.argv[1] if len(sys.argv)>1 else 'stockfish'
COUL={chess.ROOK:'#A83232',chess.BISHOP:'#A8693A',chess.QUEEN:'#6A3FA0',chess.KNIGHT:'#2E6DB4'}
def ctr(sq,s=45,m=15): return (m+s*chess.square_file(sq)+s/2, m+s*(7-chess.square_rank(sq))+s/2)
def dessiner(fen,fichier,fleches=(),cercles=(),zones=()):
    b=chess.Board(fen); fill={z:'#E6B4D4' for z in zones}
    svg=chess.svg.board(b,size=390,coordinates=True,fill=fill,arrows=[chess.svg.Arrow(a,c,color='#A83232') for a,c,n in fleches],
        colors={'square light':'#FFFFFF','square dark':'#D0E2F5','margin':'#FFFFFF','coord':'#4A6FA5','inner border':'#A8BFDC','outer border':'#A8BFDC'})
    ins=''.join(f'<circle cx="{ctr(s)[0]}" cy="{ctr(s)[1]}" r="20" fill="none" stroke="{COUL[b.piece_type_at(s)]}" stroke-width="3.5"/>' for s in cercles)
    for a,c,n in fleches:
        (x1,y1),(x2,y2)=ctr(a),ctr(c); mx,my=(x1+x2)/2,(y1+y2)/2
        ins+=f'<circle cx="{mx}" cy="{my}" r="9" fill="#FFFFFF" stroke="#A83232" stroke-width="2"/><text x="{mx}" y="{my+4}" font-size="12" font-weight="bold" text-anchor="middle" fill="#A83232" font-family="sans-serif">{n}</text>'
    cairosvg.svg2png(bytestring=svg.replace('</svg>',ins+'</svg>').encode(),write_to=fichier,output_width=800,output_height=800)
g=chess.pgn.read_game(io.StringIO(open('carlsen-nakamura-2023.pgn',encoding='utf-8',errors='ignore').read()))
b=g.board(); pos=[]; coups=list(g.mainline_moves())
depart="r7/3R1p2/1pk1PBp1/2p3R1/4P3/1P3P2/1KQ5/r4q2 w"
FRN={'K':'R','Q':'D','R':'T','B':'F','N':'C'}
fr=lambda s: FRN[s[0]]+s[1:] if s[0] in FRN else s
lignes=[]; start=None
for i,m in enumerate(coups):
    if ' '.join(b.fen().split()[:2])==depart: start=i
    b.push(m)
b=g.board()
for i,m in enumerate(coups):
    if start is not None and i>=start: lignes.append((b.fullmove_number,b.turn,fr(b.san(m)),m,b.copy()))
    b.push(m)
FR_FEN=[]; rows=[]
eng=chess.engine.SimpleEngine.popen_uci(SF); eng.configure({"Threads":6,"Hash":256})
def mesures(bd):
    K=bd.king(chess.BLACK); n=bd.copy(); n.turn=chess.BLACK
    fuites=len([m for m in n.legal_moves if m.from_square==K])
    zone=[K]+[s for s in chess.SQUARES if chess.square_distance(s,K)==1]
    A={s for z in zone for s in bd.attackers(chess.WHITE,z) if bd.piece_type_at(s)!=chess.KING}
    D={s for z in zone for s in bd.attackers(chess.BLACK,z) if bd.piece_type_at(s)!=chess.KING}
    sc=eng.analyse(bd,chess.engine.Limit(time=18))['score'].white()
    ev=('mat en '+str(sc.mate())) if sc.is_mate() else f"{sc.score()/100:+.1f}".replace('.',',')
    return fuites,len(A),len(D),ev,[chess.square_name(m.to_square) for m in n.legal_moves if m.from_square==K]
bd=chess.Board(depart+" - - 0 40"); K=bd.king(chess.BLACK); n=bd.copy(); n.turn=chess.BLACK; zone=[K]+[q for q in chess.SQUARES if chess.square_distance(q,K)==1]; A={q for z in zone for q in bd.attackers(chess.WHITE,z) if bd.piece_type_at(q)!=chess.KING}; D={q for z in zone for q in bd.attackers(chess.BLACK,z) if bd.piece_type_at(q)!=chess.KING}; rows.append(("Départ (avant 40.Txc5+)",len([m for m in n.legal_moves if m.from_square==K]),len(A),len(D),"mat en 11")); print("départ",rows[-1])
for (num,tr,san,m,bb) in lignes:
    if tr!=chess.WHITE: bb.push(m); continue
    bb.push(m); f,a,d,ev,fl=mesures(bb); rows.append((f"{num}.{san}",f,a,d,ev)); print(num,san,f,a,d,ev,fl)
    if num==40: pass
eng.quit()
json.dump(rows,open('resultats/carlsen_rows.json','w'),ensure_ascii=False)
# diagrammes
fin=chess.Board("rk6/5p2/4P1p1/3QB3/4P3/1P3P2/1K6/r4q2 b - - 4 44")
ap42=[l for l in lignes if l[0]==42 and l[1]==chess.WHITE][0][4].copy()
dessiner(depart+" - - 0 40",'resultats/image_carlsen_1.png',fleches=[(chess.G5,chess.C5,1),(chess.D7,chess.C7,2)],cercles=[chess.G5,chess.D7,chess.C2,chess.F6],zones=[chess.B5])
dessiner(ap42.fen(),'resultats/image_carlsen_2.png',cercles=[chess.C5,chess.F6],zones=[chess.B7,chess.B8])
dessiner(fin.fen(),'resultats/image_carlsen_3.png',fleches=[(chess.E5,chess.D4,1)],cercles=[chess.D5,chess.E5],zones=[chess.A7,chess.C8])
print("diagrammes écrits ; position après 42.Dxc5+ :",ap42.fen())
