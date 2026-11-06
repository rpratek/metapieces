#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyse_partie_metapieces.py — analyse d'une partie avec le concept de Métapièce (lecture seule).
USAGE : python3 analyse_partie_metapieces.py partie.pgn [--profondeur 18] [--sortie PREFIXE]
MOTEUR : Stockfish, UN SEUL FIL, PROFONDEUR FIXE (résultats reproductibles sur une même version du moteur ; ils varient avec la profondeur : un résultat sans sa profondeur n'est pas une mesure).
Produit : PREFIXE_courbes.png (évaluation du moteur + nombre d'attaquants A de la zone du roi) et PREFIXE_rapport.md.
LIMITE : A n'est calculé qu'à partir du 20e demi-coup et pour un Roi roqué encore sur son aile (comme dans le livre).
DÉFINITIONS (identiques à recherche/scripts/seuil_roque.py du dépôt) : zone du Roi = 12 cases (voisines du Roi + les trois cases
devant lui à deux rangs) ; A = nombre de pièces adverses (Cavalier, Fou, Tour, Dame) qui attaquent au moins une case de la zone ;
D = pièces du Roi qui la défendent ; le livre (Livre III, § 6.3) donne la probabilité de mat à dix demi-coups selon A : 0,36 % (A = 1), 1,21 % (A = 2), 3,02 % (A = 3), 5,27 % (A = 4).
Événements repérés : échange de Dames (Cahier n° 11 : les échanges de pièces majeures dissolvent les Métapièces offensives), Tours doublées
sur une colonne ou une rangée, Tour qui change d'aile par la 3ᵉ/6ᵉ rangée, première apparition de A ≥ 3, plus fortes bascules d'évaluation (Cahier n° 17)."""
import sys,io,json,argparse,chess,chess.pgn,chess.engine
def ana(eng,b,lim,**kw):
    """Analyse une position SANS mémoire des positions précédentes (table de hachage vidée) : le résultat ne dépend que de la position."""
    eng.configure({"Clear Hash":None}); return eng.analyse(b,lim,**kw)
PCS=(chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
def zone(K,col):
    f,r=chess.square_file(K),chess.square_rank(K); z=set()
    for df in (-1,0,1):
        for dr in (-1,0,1):
            ff,rr=f+df,r+dr
            if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    d=1 if col==chess.WHITE else -1
    for df in (-1,0,1):
        ff,rr=f+df,r+2*d
        if 0<=ff<8 and 0<=rr<8: z.add(chess.square(ff,rr))
    return z
def AD(b,col):
    K=b.king(col); Z=zone(K,col)
    A={s for sq in Z for s in b.attackers(not col,sq) if b.piece_type_at(s) in PCS}
    D={s for sq in Z for s in b.attackers(col,sq) if b.piece_type_at(s) in PCS}
    return len(A),len(D)
def unites9(b,col):
    """Définition de la section 10.5 : unités de `col` (pièces, pions, Roi) qui attaquent au moins une des NEUF cases du Roi adverse."""
    K=b.king(not col); Z={K}|set(chess.SquareSet(chess.BB_KING_ATTACKS[K]))
    return sum(1 for s_,p in b.piece_map().items() if p.color==col and any(t in Z for t in b.attacks(s_)))
def tours_doublees(b,col):
    R=list(b.pieces(chess.ROOK,col)); out=[]
    for i in range(len(R)):
        for j in range(i+1,len(R)):
            a,c=R[i],R[j]
            if chess.square_file(a)==chess.square_file(c) or (chess.square_rank(a)==chess.square_rank(c) and chess.square_rank(a) not in (0,7)):
                if all(b.piece_at(s) is None for s in chess.SquareSet(chess.between(a,c))): out.append((chess.square_name(a),chess.square_name(c)))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pgn'); ap.add_argument('--profondeur',type=int,default=18); ap.add_argument('--sortie',default='partie')
    a=ap.parse_args(); txt=open(a.pgn,encoding='utf-8').read().replace('][',']\n['); import re as _re; txt=_re.sub(r'\]\s*(?=1\.)',']\n\n',txt,count=1); g=chess.pgn.read_game(io.StringIO(txt)); mv=list(g.mainline_moves())
    b=g.board(); eng=chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish'); eng.configure({"Threads":1,"Hash":128})
    L=[]; ev0=ana(eng,b,chess.engine.Limit(depth=a.profondeur))['score'].white().score(mate_score=10000); L.append(dict(n=0,san='-',ev=ev0,Aw=0,Dw=0,Ab=0,Db=0,evt=[]))
    roque={chess.WHITE:False,chess.BLACK:False}; etat_td={chess.WHITE:None,chess.BLACK:None}
    for n,m in enumerate(mv,1):
        san=b.san(m); mover=b.turn; cap=b.piece_at(m.to_square); evt=[]
        if cap is not None and cap.piece_type==chess.QUEEN and b.piece_at(m.from_square).piece_type==chess.QUEEN: evt.append('échange de Dames')
        if b.piece_at(m.from_square).piece_type==chess.ROOK and chess.square_rank(m.to_square)==(2 if mover==chess.WHITE else 5) and chess.square_rank(m.from_square)==(0 if mover==chess.WHITE else 7): evt.append('Tour levée sur la 3e/6e rangée')
        if b.is_castling(m): roque[mover]=True
        b.push(m)
        td=tours_doublees(b,mover); cle=tuple(sorted(td[0])) if td else None
        if cle and cle!=etat_td[mover]: evt.append('Tours doublées '+('Blancs' if mover==chess.WHITE else 'Noirs')+' '+'-'.join(td[0]))
        etat_td[mover]=cle
        s=ana(eng,b,chess.engine.Limit(depth=a.profondeur))['score'].white().score(mate_score=10000)
        def adr(col):
            K=b.king(col); f=chess.square_file(K)
            return AD(b,col) if (n>=20 and roque[col] and (f>=5 or f<=2)) else (None,None)
        Ab,Db=adr(chess.BLACK); Aw,Dw=adr(chess.WHITE)   # Ab = attaquants du Roi noir (par les Blancs)
        L.append(dict(n=n,san=san,ev=s,Ab=Ab,Db=Db,Aw=Aw,Dw=Dw,evt=evt,U=unites9(b,mover)))
    eng.quit(); json.dump(L,open(a.sortie+'_donnees.json','w'),ensure_ascii=False)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    x=[d['n']/2 for d in L]; ev=[max(-5,min(5,d['ev']/100)) for d in L]
    fig,(a1,a2)=plt.subplots(2,1,figsize=(10,7),dpi=110,sharex=True,gridspec_kw={'height_ratios':[3,2]})
    a1.axhline(0,color='#888',lw=1); a1.plot(x,ev,color='#1F3A6E',lw=2); a1.fill_between(x,ev,0,where=[v>=0 for v in ev],color='#cfe0ff',alpha=.6); a1.fill_between(x,ev,0,where=[v<0 for v in ev],color='#ffd9c2',alpha=.6)
    a1.set_ylim(-5.5,5.5); a1.set_ylabel('Évaluation (pions)\n+ : Blancs   − : Noirs')
    for d in L:
        if 'échange de Dames' in d['evt']: a1.axvline(d['n']/2,color='#9B1C1C',ls=':',lw=1.5); a1.text(d['n']/2+0.2,4.6,'échange\\nde Dames',fontsize=8,color='#9B1C1C')
    a2.step(x,[(d['Ab'] if d['Ab'] is not None else float('nan')) for d in L],where='post',color='#1F6FD1',lw=2,label='attaquants du Roi noir (par les Blancs)')
    a2.step(x,[(d['Aw'] if d['Aw'] is not None else float('nan')) for d in L],where='post',color='#F28C00',lw=2,label='attaquants du Roi blanc (par les Noirs)')
    a2.axhline(3,color='#555',ls='--',lw=1); a2.text(0.3,3.1,'A = 3 : 3,02 % de mats à 10 demi-coups (livre, § 6.3)',fontsize=8,color='#555')
    a2.set_ylabel('A : pièces qui menacent\nla zone du Roi'); a2.set_xlabel('Numéro du coup'); a2.legend(fontsize=8,loc='upper left'); a2.set_ylim(-0.2,max(5,max([d['Ab'] or 0 for d in L]+[d['Aw'] or 0 for d in L])+1))
    h=g.headers; a1.set_title(f"{h.get('White','?')} – {h.get('Black','?')} ({h.get('Event','?')}, {h.get('Date','?')}) : évaluation et attaquants",fontsize=10)
    plt.tight_layout(); plt.savefig(a.sortie+'_courbes.png')

    # --- RÉSERVE DE DÉFENSES : dans chaque position décidée (|éval| >= 1,5 pion), combien de coups évitent encore un mat forcé ?
    res=[]; b=g.board(); eng=chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish'); eng.configure({"Threads":1,"Hash":128})
    for n,m in enumerate(mv,1):
        b.push(m)
        if b.is_game_over(): break
        e=L[n]['ev']
        if abs(e)<150 or (e>0 and b.turn!=chess.BLACK) or (e<0 and b.turn!=chess.WHITE): continue   # le camp au trait est le défenseur
        nb=b.legal_moves.count(); k=min(nb,40)
        infos=ana(eng,b,chess.engine.Limit(depth=a.profondeur),multipv=k)
        if isinstance(infos,dict): infos=[infos]
        sc=[(i['pv'][0],i['score'].pov(b.turn)) for i in infos if i.get('pv')]
        nonmat=[(mv_,s_) for mv_,s_ in sc if not s_.is_mate() or s_.mate()>0]
        best=max(sc,key=lambda t:t[1].score(mate_score=10000)); 
        res.append(dict(n=n,coup=(n+1)//2,trait='Noirs' if b.turn==chess.BLACK else 'Blancs',legaux=nb,evalues=len(sc),evitent_mat=len(nonmat),meilleur=b.san(best[0]),ev_meilleur=best[1].score(mate_score=10000)/100))
    eng.quit()
    json.dump(res,open(a.sortie+'_defenses.json','w'),ensure_ascii=False)
    # rapport
    R=[f"# Analyse Métapièces : {h.get('White','?')} – {h.get('Black','?')}\n",f"{h.get('Event','?')} · {h.get('Date','?')} · résultat annoncé {h.get('Result','?')} · {len(mv)} coups · moteur Stockfish, un seul fil, profondeur {a.profondeur}.\n"]
    R.append("## Événements repérés\n")
    for d in L:
        if d['evt']: R.append(f"- coup {(d['n']+1)//2}{'...' if d['n']%2==0 else '.'} {d['san']} : {' ; '.join(d['evt'])}")
    prem=[d for d in L if (d['Ab'] or 0)>=3]; premw=[d for d in L if (d['Aw'] or 0)>=3]
    R.append("\n## Unités qui visent le Roi adverse (définition de la section 10.5 : neuf cases)\n"); R.append("| coup | unités du camp qui vient de jouer |\n|---|---|\n"+"\n".join(f"| {(d['n']+1)//2}{'...' if d['n']%2==0 else '.'} {d['san']} | {d['U']} |" for d in L[1:] if d['n']>=40))
    R.append("\n## Seuil A ≥ 3 (Livre III, § 6.3 du livre)\n")
    R.append(f"- Roi noir : première fois à A ≥ 3 : {('coup '+str((prem[0]['n']+1)//2)) if prem else 'jamais'} ; maximum {max([d['Ab'] or 0 for d in L])} (Roi roqué seulement).")
    R.append(f"- Roi blanc : première fois à A ≥ 3 : {('coup '+str((premw[0]['n']+1)//2)) if premw else 'jamais'} ; maximum {max([d['Aw'] or 0 for d in L])} (Roi roqué seulement).")
    sw=sorted([(abs(L[i]['ev']-L[i-1]['ev']),L[i]) for i in range(1,len(L))],key=lambda t:-t[0])[:5]
    R.append("\n## Plus fortes bascules d'évaluation (Cahier n° 17)\n")
    for dd,d in sw: R.append(f"- après {(d['n']+1)//2}{'...' if d['n']%2==0 else '.'} {d['san']} : {L[d['n']-1]['ev']/100:+.2f} → {d['ev']/100:+.2f}")
    if res:
        R.append("\n## Réserve de défenses (positions décidées, camp au trait = défenseur)\n")
        R.append("| coup | au trait | coups légaux | coups qui évitent le mat forcé | meilleure défense (éval., point de vue du défenseur) |\n|---|---|---|---|---|")
        for r_ in res: R.append(f"| {r_['coup']}{'...' if r_['trait']=='Noirs' else '.'} | {r_['trait']} | {r_['legaux']} | {r_['evitent_mat']} | {r_['meilleur']} ({r_['ev_meilleur']:+.1f}) |")
        zero=[r_ for r_ in res if r_['evitent_mat']<=0.2*r_['legaux'] and r_['ev_meilleur']<=-3]
        R.append("\nPoint de non-retour (au plus 20 % des coups légaux évitent le mat ET meilleure défense à − 3 pions ou moins, soit environ la Dame) : "+(f"coup {zero[0]['coup']}" if zero else "non atteint")+".")
    R.append("\n## Lecture à compléter par l'auteur\n- Initiative (prendre ou garder) :\n- Construire (territoire, Métapièces) :\n- Activer (le coup qui convertit) :\n- Dissolution (échanges) :\n- Acquis à retenir :\n")
    open(a.sortie+'_rapport.md','w',encoding='utf-8').write('\n'.join(R)); print("fichiers :",a.sortie+'_courbes.png',a.sortie+'_rapport.md',a.sortie+'_donnees.json')
if __name__=='__main__': main()
