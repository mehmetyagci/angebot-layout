import sys,json,itertools,time
sys.path.insert(0,'.')
import engine as E
from functools import lru_cache
U=W_U=E.W/50.0   # 1 birim = %2
MINU,MAXU=7,50
MINC=int(__import__('os').environ.get('MINC','2'))
BF2='boxes' in __import__('os').environ.get('BOXFILE','')
def order_pages():
    raw=json.load(open(__import__('os').environ.get('BOXFILE','data/boxes13.json')))
    pages={}
    for d in raw: pages.setdefault(d['page'],[]).append(d)
    out={}
    for p,L in pages.items():
        # reyon sırası: alt grup no (çay/pirinç başta), aynı alt grupta pahalı önde
        if p==3: key=lambda d:({401:0,304:1,701:2,705:3}.get(d['altn'],10+d['altn']),-float(d['price']))
        elif p==4 and BF2: key=lambda d:(d['altn']+(10000 if d['altn'] in (903,904) else 0),-float(d['price']))
        else: key=lambda d:(d['altn'],-float(d['price']))
        out[p]=sorted(L,key=(lambda d:d['ord']) if 'ord' in L[0] else key)
    return out
def run(page,hero_ok,K=6,maxhero=2,verbose=False,must=None,sizes=None,together=None,wmul=None,dpen=9000,eq=False):
    E.set_boxes([E.Box(d) for d in ORD[page]])
    n=len(E.BOXES);maxp=max(b.price for b in E.BOXES)
    wt=[(0.75+0.5*b.price/maxp)*(wmul or {}).get(i,1) for i,b in enumerate(E.BOXES)]
    if eq: wt=[1.0*(wmul or {}).get(i,1) for i in range(n)]
    scale=lambda hero:1.2 if hero else 1.0
    @lru_cache(None)
    def A(i,wu,rows):
        w=wu*E.W/50.0;h=E.RH*rows
        hero=rows==2
        return E.area_of(i,int(w),h,scale(hero))
    def score(i,wu,rows):
        a=A(i,wu,rows);box=int(wu*E.W/50)*E.RH*rows
        if a==0: return -1e9
        fill=a/box
        pen=max(0,0.60-fill)*box*3.0
        return wt[i]*a-pen
    @lru_cache(None)
    def rowdp(idx,avail):
        k=len(idx)
        if k==0: return (0,()) if avail==0 else None
        if avail<MINU*k: return None
        NEG=-1e18;dp=[[NEG]*(avail+1) for _ in range(k+1)];ch=[[0]*(avail+1) for _ in range(k+1)];dp[0][0]=0
        for j in range(1,k+1):
            for r in range(MINU*j,avail+1):
                for w in range(MINU,min(MAXU if k==1 else 36,r-MINU*(j-1))+1):
                    p=dp[j-1][r-w]
                    if p<=NEG/2: continue
                    v=p+score(idx[j-1],w,1)
                    if v>dp[j][r]:dp[j][r]=v;ch[j][r]=w
        if dp[k][avail]<=NEG/2: return None
        ws=[];r=avail
        for j in range(k,0,-1):w=ch[j][r];ws.append(w);r-=w
        return dp[k][avail],tuple(reversed(ws))
    cands=[i for i in range(n) if hero_ok(E.BOXES[i])]
    res=[]
    herosets=[()]
    for h in cands: herosets.append((h,))
    if maxhero>=2:
        for a,b in itertools.combinations(cands,2): herosets.append((a,b))
    HW=range(8,23,2)
    for hs in herosets:
        if must is not None and not set(must)<=set(hs): continue
        if sizes is not None and len(hs) not in sizes: continue
        rest=[i for i in range(n) if i not in hs]
        m=len(rest)
        placements=[()] if not hs else None
        if hs:
            placements=[]
            for bands in itertools.product((0,2),repeat=len(hs)):
                if len(hs)==2 and bands[0]==bands[1]: continue
                for sides in itertools.product('LR',repeat=len(hs)):
                    placements.append(tuple(zip(hs,bands,sides)))
        for pl in placements:
            for hws in itertools.product(HW,repeat=len(hs)):
                avail=[50]*4;hsc=0
                for (h,b,s),wu in zip(pl,hws):
                    avail[b]-=wu;avail[b+1]-=wu
                    hsc+=score(h,wu,2)
                if min(avail)<MINU: continue
                for cs in itertools.product(range(1,5),repeat=4):
                    if sum(cs)!=m: continue
                    if MINC>1 and any(cs[bb]+sum(1 for (h,hb,sd) in pl if hb in (bb,bb-1))<MINC or cs[bb]+sum(1 for (h,hb,sd) in pl if hb in (bb,bb-1))>4 for bb in range(4)): continue
                    pos=0;tot=hsc;bands=[];ok=True
                    for b in range(4):
                        idx=tuple(rest[pos:pos+cs[b]]);pos+=cs[b]
                        r=rowdp(idx,avail[b])
                        if r is None: ok=False;break
                        tot+=r[0];bands.append((idx,r[1]))
                    if not ok: continue
                    if together and not all(any(a in bd[0] and c in bd[0] for bd in bands) for a,c in together): continue
                    # hero sıra cezası
                    disp=0
                    for (h,b,s) in pl:
                        before=sum(cs[:b])+(0 if s=='L' else cs[b])+sum(1 for (h2,b2,s2) in pl if h2!=h and (b2<b or (b2==b and s2=='L' and s=='R')) )
                        disp+=abs(before-h)
                    tot-=disp*dpen
                    res.append((tot,pl,hws,cs,bands))
    res.sort(key=lambda x:-x[0])
    # farklı yapı seç
    seen=set();out=[]
    for r in res:
        sig=(tuple((h,b,s) for h,b,s in r[1]),r[3])
        hsig=tuple(h for h,b,s in r[1])
        if (hsig,) in seen and len(out)>=2 and len([o for o in out if tuple(h for h,b,s in o[1])==hsig])>=1: continue
        seen.add((hsig,));out.append(r)
        if len(out)>=K: break
    return out
ORD=order_pages()
def to_plan(page,r):
    tot,pl,hws,cs,bands=r
    items=[]
    bx=ORD[page]
    hero={h:(b,s,wu) for (h,b,s),wu in zip(pl,hws)}
    for b in range(4):
        idx,ws=bands[b]
        lst=[]
        for h,(hb,s,wu) in hero.items():
            if hb==b and s=='L': lst.append((h,wu,True,'hero'))
        for i,w in zip(idx,ws): lst.append((i,w,False,''))
        for h,(hb,s,wu) in hero.items():
            if hb==b and s=='R': lst.append((h,wu,True,'hero'))
        x=0
        # hero üst bant solundan/sağından kalan band için x ofseti
        offL=sum(wu for h,(hb,s,wu) in hero.items() if hb==b-1 and s=='L')
        for k,(i,w,hh,_) in enumerate(lst):
            pass
        items.append((b,lst))
    return items
