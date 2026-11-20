import json,re,itertools,math,sys
from functools import lru_cache
from PIL import ImageFont
W=1587;HEAD=258;FOOT=2122;RH=466;PAD=4
BW0,BH0=232,84
FB='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
FR='/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
ph={int(k):v for k,v in json.load(open('data/ph.json')).items()}
DIA={'sigir':'Sığır','aci':'Acı','acili':'Acılı','cokelek':'Çökelek','corek':'Çörek','salcasi':'Salçası','tatli':'Tatlı','kirmizi':'Kırmızı',
'findik':'Fındık','findikli':'Fındıklı','fistikli':'Fıstıklı','pasa':'Paşa','kadayif':'Kadayıf','kaplamali':'Kaplamalı','cikolatali':'Çikolatalı',
'eksi':'Ekşi','icecek':'İçecek','cilek':'Çilek','visne':'Vişne','seftali':'Şeftali','kayisi':'Kayısı','camasir':'Çamaşır','sodasi':'Sodası',
'yesil':'Yeşil','cizik':'Çizik','dogal':'Doğal','yagli':'Yağlı','nigde':'Niğde','sise':'Şişe','gazozu':'Gazozu','kirma':'Kırma','sabunlu':'Sabunlu',
'sosu':'Sosu','soya':'Soya','biberli':'Biberli','kokulu':'Kokulu','biber':'Biber','salcasi':'Salçası','vanilyali':'Vanilyalı','isot':'Isot','pasam':'Paşam','inci':'İnci','cekirdegi':'Çekirdeği','tuzsuz':'Tuzsuz','mandalinali':'Mandalinalı','dolunay':'Dolunay','orman':'Orman','meyveli':'Meyveli'}
def fold(x): return x.lower().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c').replace('i̇','i')
def dia(s):
    return ' '.join(DIA.get(w.lower(),w) for w in s.split())
def gramfmt(g):
    m=re.match(r'\s*(\d+)\s*x\s*([\d\.,]+)\s*(g|kg|l|ml)\s*$',g or '')
    if not m: return ''
    n,v,u=m.groups();u={'g':'gr'}.get(u,u)
    if n=='1': return f'{v} {u}/Stück'
    return f'{n}x{v} {u}/Stück'
OVR={"Gazoz 6'lı (2 çeşit)":['Niğde Gazoz 6x250 ml','Zafer Gazoz Cam Şişe 6x200 ml'],
'Sos Çeşitleri (2 çeşit)':['Aiko Soya Sosu Premium 250 ml','Tat Acı Biber Sosu 100 ml'],
'Biber Salçası (3 çeşit)':['Tatlı Biber Salçası Cam 550 gr','Acılı Biber Salçası Cam 580 gr','Köy Mix Tatlı Biber Salçası Cam 560 gr'],
'Taze Çökelek (2 çeşit)':['Taze Çökelek','Taze Çökelek Çörek Otlu']}
class Box:
    def __init__(s,d):
        s.__dict__.update(d)
        s.arts=[i['art'] for i in s.items]
        s.asp=[ph[a]['w']/ph[a]['h'] for a in s.arts]
        s.orig=[ph[a]['h'] for a in s.arts]
        s.n=len(s.arts)
        grams=[gramfmt(i['gram']) for i in s.items]
        s.var=[];s.gline=''
        if s.n==1 or len(set(grams))==1: s.gline=grams[0]
        if 2<=s.n<=4 and 'Snack' not in s.title:
            mk=fold(s.marka).split()
            for i,g in zip(s.items,grams):
                words=i['name'].split()
                if [fold(x) for x in words[:len(mk)]]==mk: words=words[len(mk):]
                elif fold(words[0])==mk[0]: words=words[1:]
                nm=dia(' '.join(words))
                if len(set(grams))>1 and g: nm+=' '+g.replace('/Stück','')
                s.var.append(nm)
        if s.title in OVR: s.var=OVR[s.title]
        s.price=float(s.price)
def eur(p): return f'{p:.2f}'.replace('.',',')
@lru_cache(None)
def font(bold,size): return ImageFont.truetype(FB if bold else FR,size)
def wrap(txt,f,w):
    lines=[];cur=''
    for wd in txt.split():
        t=(cur+' '+wd).strip()
        if f.getlength(t)<=w or not cur: cur=t
        else: lines.append(cur);cur=wd
    if cur: lines.append(cur)
    return lines
FS=dict(m=20,t=27,g=18,v=16)
def text_h(b,tw,sc=1.0):
    h=0;w=tw-14
    for txt,k,bold in ((b.marka,'m',1),(b.title,'t',1),(' '.join(b.var),'v',1),(b.gline,'g',0)):
        for wd in txt.split():
            if font(bold,max(8,round(FS[k]*sc))).getlength(wd)>w-(10 if k=='v' else 0): return 1e9
    for wd in b.title.split():
        if font(1,max(8,round(FS['t']*sc))).getlength(wd)>w: return 1e9
    f=lambda k,bold:font(bold,max(8,round(FS[k]*sc)))
    h+=len(wrap(b.marka,f('m',1),w))*f('m',1).size*1.15+2
    h+=len(wrap(b.title,f('t',1),w))*f('t',1).size*1.15+4
    if b.gline: h+=len(wrap(b.gline,f('g',0),w))*f('g',0).size*1.15+3
    for v in b.var: h+=len(wrap('• '+v,f('v',1),w))*f('v',1).size*1.15
    if b.var: h+=6
    return h+10
def rowlen(r,h,ov):
    return sum(r)*h-sum(ov*0.5*(r[i]+r[i+1])*h for i in range(len(r)-1))
STACK=set()
MAYS=False
HCAP={}
UPMAP={}
NARROW=set()
OVMAP={}
def fit(asp,orig,rw,rh):
    if rw<30 or rh<30: return None
    n=len(asp);best=None
    ov=0.12 if n>=3 else 0.0
    ovv=0.06 if n>=4 else 0.0
    ov,ovv=OVMAP.get(tuple(asp),(ov,ovv))
    for rr in range(1,min(n,3)+1):
        if n<=3 and rr>1 and tuple(asp) not in STACK: continue
        if tuple(asp) in STACK and rr==1 and not MAYS: continue
        if n==4 and rr==2 and rw<0.75*rh: continue
        cols=math.ceil(n/rr);rowsets=[asp[i:i+cols] for i in range(0,n,cols)]
        if len(rowsets)!=rr: continue
        mxu=max(rowlen(r,1.0,ov) for r in rowsets)
        hv=(1+(rr-1)*(1-ovv))
        h=min(rh/hv,rw/mxu,max(orig)*UPMAP.get(tuple(asp),2.4),HCAP.get(tuple(asp),1e9))
        if h<20: continue
        area=sum(sum(r) for r in rowsets)*h*h*(1-0.5*ov)
        if best is None or area>best[0]: best=(area,rr,cols,h,ov,ovv)
    return best
def place(asp,rr,cols,h,rx,ry,rw,rh,align='b',halign='c',ov=0.0,ovv=0.0):
    rows=[asp[i:i+cols] for i in range(0,len(asp),cols)]
    gh=h*(1+(rr-1)*(1-ovv));gw=max(rowlen(r,h,ov) for r in rows)
    y0=ry+rh-gh if align=='b' else ry+(rh-gh)/2
    x0={'c':rx+(rw-gw)/2,'l':rx,'r':rx+rw-gw}[halign]
    out=[];yy=y0
    for r in rows:
        rwid=rowlen(r,h,ov);xx=x0+(gw-rwid)/2
        for k,a in enumerate(r):
            out.append((xx,yy,a*h,h))
            xx+=a*h-(ov*0.5*(r[k]+r[k+1])*h if k+1<len(r) else 0)
        yy+=h*(1-ovv)
    return out,(x0,y0,gw,gh)
def rects_hit(a,b): return not(a[0]+a[2]<=b[0] or b[0]+b[2]<=a[0] or a[1]+a[3]<=b[1] or b[1]+b[3]<=a[1])
@lru_cache(None)
def layout(bi,w,h,sc0,boxes_id=0):
    best=None
    for fac in (1.0,0.88,0.76):
        L=layout1(bi,w,h,sc0,sc0*fac)
        if L is None: continue
        sc=1.0 if fac==1.0 else (0.88 if fac==0.88 else 0.76)
        v=L['area']*(0.84+0.16*fac)
        if best is None or v>best[0]: best=(v,L)
    return best[1] if best else None
def layout1(bi,w,h,scb,sc):
    b=BOXES[bi];ks=(0.8 if w<300 else (0.87 if (bi in NARROW and w<420) else 1.0));BW=int(BW0*ks*scb**0.5);BH=int(BH0*ks*scb**0.5)
    badge=(w-BW-2,0,BW+2,BH+4)
    best=None
    def consider(mode,tx,ty,tw,th,regions,halign):
        nonlocal best
        for (rx,ry,rw,rh) in regions:
            subs=[(rx,ry,rw,rh)]
            if rects_hit((rx,ry,rw,rh),badge):
                subs=[(rx,max(ry,BH+8),rw,ry+rh-max(ry,BH+8)),(rx,ry,min(rw,badge[0]-6-rx),rh)]
            for sr in subs:
                f=fit(b.asp,b.orig,sr[2],sr[3])
                if not f: continue
                if best is None or f[0]>best['area']:
                    best=dict(area=f[0],mode=mode,tx=tx,ty=ty,tw=tw,th=th,reg=sr,fit=f,halign=halign,BW=BW,BH=BH,sc=sc)
    tws=range(100,int(min(420,w*0.62)),10)
    for tw in tws:
        th=text_h(b,tw,sc)
        if th<=h-BH-12:
            consider('left',w-tw-PAD-4,BH+6,tw,th,[(PAD,PAD,w-tw-2*PAD-6,h-2*PAD)],'l')
        if th<=h-14:
            consider('right',PAD+4,PAD+4,tw,th,[(tw+PAD+10,PAD,w-tw-2*PAD-10,h-2*PAD)],'r')
    tw=w-BW-16
    if tw>=100:
        th=text_h(b,tw,sc)
        y0=max(th+PAD+6,0)
        if th<h*0.6:
            consider('top',PAD+4,PAD+4,tw,th,[(PAD,y0,w-2*PAD,h-y0-PAD)],'c')
    return best
BOXES=[]
def set_boxes(L):
    global BOXES
    BOXES=L;layout.cache_clear()
def area_of(bi,w,h,sc):
    L=layout(bi,w,h,sc)
    return L['area'] if L else 0
