import sys,os,itertools,math,json;sys.path.insert(0,'.')
os.environ['BOXFILE']='data/boxes13.json'
import render as R,search as S,engine as E
from functools import lru_cache
U=E.W/50.0
E.MAYS=True
def prep(page):
    E.set_boxes([E.Box(d) for d in S.ORD[page]])
    for b in E.BOXES:
        if b.n>=1 and sum(b.asp)/b.n>1.7 and b.n<=3: E.STACK.add(tuple(b.asp))
    E.layout.cache_clear()
def ixp(pre):
    for i,b in enumerate(E.BOXES):
        if b.title.startswith(pre): return i
    raise KeyError(pre)
@lru_cache(None)
def sc(page,i,wu,rows):
    w=int(wu*U);h=E.RH*rows
    L=E.layout(i,w,h,1.2 if rows==2 else 1.0)
    if not L: return -9,0,0
    area,rr,cols,hr,ov,ovv=L['fit']
    fill=area/(w*h);share=min(0.95,hr*(1+(rr-1)*(1-ovv))/h)
    s=fill+0.4*share-1.5*max(0,0.42-fill)
    return s,fill,share
def boxscore(page,i,wu,rows):
    s=sc(page,i,wu,rows)[0]; return s*wu*rows
MINW,MAXW=7,36
MB={};MX={}
HR=(10,41)
BETA=30
EQ=False
MAXC=6
EXC=set()
@lru_cache(None)
def rowdp(page,idx,avail):
    k=len(idx)
    if k==0: return (0,()) if avail==0 else (-1e9,())
    los=[max(MINW,MB.get(i,MINW)) for i in idx]
    his=[min(50 if k==1 else MX.get(i,MAXW),avail) for i in idx]
    best=(-1e9,())
    def rec(j,rem,ws):
        nonlocal best
        if j==k:
            if rem==0 and (not EQ or (lambda q:(not q) or max(q)-min(q)<=1)([w for i,w in zip(idx,ws) if i not in EXC])):
                sh=[sc(page,i,w,1)[2] for i,w in zip(idx,ws)]
                v=sum(boxscore(page,i,w,1) for i,w in zip(idx,ws))-BETA*(max(sh)-min(sh))*(1 if k>1 else 0)
                if v>best[0]: best=(v,tuple(ws))
            return
        mrest=sum(los[j+1:])
        for w in range(los[j],min(his[j],rem-mrest)+1):
            rec(j+1,rem-w,ws+[w])
    rec(0,avail,[])
    return best
def comps(n,rowsn,mn,mx,fixed):
    for c in itertools.product(range(mn,mx+1),repeat=rowsn):
        if sum(c)==n and all(c[r]==f for r,f in fixed.items()): yield c
def solve(page,heroes,seqpre,rowfix=None,permute=False,topk=3):
    """heroes: [(prefix,side,r0)] ; seqpre: ordered prefixes of non-hero boxes"""
    prep(page)
    H=[(ixp(p),side,r0) for p,side,r0 in heroes]
    seq0=[ixp(p) for p in seqpre]
    res=[]
    orders=itertools.permutations(seq0) if permute else [tuple(seq0)]
    for seq in orders:
        n=len(seq)
        hrange=[range(*HR)]*len(H)
        for hw in itertools.product(*hrange):
            occ=[0]*4
            for (hi_,side,r0),w in zip(H,hw):
                occ[r0]+=w;occ[r0+1]+=w
            if any(50-MINW*2<o<50 for o in occ): continue
            hs=sum(boxscore(page,hi_,w,2) for (hi_,_,_),w in zip(H,hw))
            for c in comps(n,4,0,MAXC,rowfix or {}):
                tot=hs;rows=[];pos=0;ok=True
                for r in range(4):
                    mem=seq[pos:pos+c[r]];pos+=c[r]
                    if not mem:
                        if occ[r]!=50: ok=False;break
                        rows.append((0,()));continue
                    v,ws=rowdp(page,tuple(mem),50-occ[r])
                    if v<-1e8: ok=False;break
                    tot+=v;rows.append((mem,ws))
                if not ok: continue
                res.append((tot,hw,c,rows,seq))
    res.sort(key=lambda t:-t[0])
    return H,res[:topk]
def to_spec(page,H,r):
    tot,hw,c,rows,seq=r
    spec=[];occL=[0]*4;occR=[0]*4
    for (hi_,side,r0),w in zip(H,hw):
        x=0 if side=='L' else None
        if side=='L':
            x=occL[r0]; 
            for k in (r0,r0+1): occL[k]+=w
        else:
            for k in (r0,r0+1): occR[k]+=w
            x=50-occR[r0]
        spec.append((hi_,x,w,r0,r0+1))
    for rr,(mem,ws) in enumerate(rows):
        if not mem: continue
        x=occL[rr]
        for i,w in zip(mem,ws): spec.append((i,x,w,rr,rr));x+=w
    return spec
def render(page,spec,name):
    import gen53lib as G
    return G.build(page,[466]*4,spec,name)
