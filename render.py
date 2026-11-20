import sys,html,os,json
sys.path.insert(0,'.')
import engine as E, search as S
from PIL import Image
t16=Image.open('data/t16-1.png').convert('RGB')
os.makedirs('out/trim',exist_ok=True)
t16.crop((0,0,E.W,E.HEAD)).save('out/head.png');t16.crop((0,E.FOOT,E.W,t16.height)).save('out/foot.png')
import shutil
TRIM=os.environ.get('TRIM','trim')  # folder of trimmed product photos named <artikel>.png (not in repo)
os.makedirs('out/trim',exist_ok=True)
for f in (os.listdir(TRIM) if os.path.isdir(TRIM) else []): shutil.copy(TRIM+'/'+f,'out/trim/'+f)
CSS=f'''*{{box-sizing:border-box;margin:0}} body{{width:{E.W}px;height:{t16.height}px;position:relative;background:#fff;font-family:'Liberation Sans',Arial,sans-serif;overflow:hidden}}
.box{{position:absolute;border-left:3px solid #111;border-top:3px solid #111;overflow:hidden;background:#fff}} .box img{{position:absolute}}
.txt{{position:absolute;line-height:1.15}} .m{{font-weight:700}} .t{{font-weight:700;margin-top:2px}} .g{{margin-top:4px}} .v{{font-weight:700;margin-top:6px;line-height:1.15}}
.price{{position:absolute;right:0;top:0;background:#e30613;border-bottom-left-radius:26px;display:flex;align-items:center;justify-content:center;gap:8px}}
.price span{{font-family:Poppins,sans-serif;font-weight:700;color:#111;-webkit-text-stroke:7px #fff;paint-order:stroke fill;letter-spacing:-2px;line-height:1}}
.price i{{font-style:normal;border-radius:50%;background:#fff;color:#e30613;font-weight:700;display:flex;align-items:center;justify-content:center;font-family:Poppins}}'''
def geometry(page,r):
    tot,pl,hws,cs,bands=r
    unit=E.W/50.0
    hero={h:(b,s,wu) for (h,b,s),wu in zip(pl,hws)}
    boxes=[]
    for b in range(4):
        idx,ws=bands[b]
        offL=sum(wu for h,(hb,s,wu) in hero.items() if hb==b-1 and s=='L')
        lst=[]
        x=offL
        for h,(hb,s,wu) in hero.items():
            if hb==b and s=='L': lst.append((h,wu,True)); 
        for i,w in zip(idx,ws): lst.append((i,w,False))
        for h,(hb,s,wu) in hero.items():
            if hb==b and s=='R': lst.append((h,wu,True))
        x=0;
        if offL: x=offL
        # sol hero b bandında x=0'dan başlar
        xs=0 if not offL else offL
        cur=0
        for (i,w,hh) in lst:
            if not hh and offL and cur==0: cur=offL
            boxes.append((i,cur*unit,E.HEAD+b*E.RH,w*unit,E.RH*(2 if hh else 1),hh))
            cur+=w
    return boxes
def box_html(i,x,y,w,h,hh):
    b=E.BOXES[i];sc=1.2 if hh else 1.0
    L=E.layout(i,int(w),int(h),sc)
    if L is None: return f'<div class="box" style="left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.1f}px">YER YOK</div>',None
    area,rr,cols,hr,ov,ovv=L['fit']
    rx,ry,rw,rh=L['reg'];BW,BH=L['BW'],L['BH']
    ha=L['halign']
    rects,(gx,gy,gw,gh)=E.place(b.asp,rr,cols,hr,rx,ry,rw,rh,'b',ha,ov,ovv)
    mode=L['mode']
    if mode=='left': tx=gx+gw+10;tw=w-6-tx;ty=BH+6
    elif mode=='right': tx=E.PAD+4;tw=gx-10-tx;ty=E.PAD+4
    else: tx=L['tx'];tw=L['tw'];ty=L['ty']
    s=L['sc']
    fs={k:max(8,round(v*s)) for k,v in E.FS.items()}
    txt=f'<div class="m" style="font-size:{fs["m"]}px">{html.escape(b.marka)}</div><div class="t" style="font-size:{fs["t"]}px">{html.escape(b.title)}</div>'
    if b.gline: txt+=f'<div class="g" style="font-size:{fs["g"]}px">{html.escape(b.gline)}</div>'
    if b.var: txt+=f'<div class="v" style="font-size:{fs["v"]}px">'+'<br>'.join('• '+html.escape(v) for v in b.var)+'</div>'
    LB=os.environ.get('LABELS')
    imgs=''.join(f'<img src="trim/{a}.png" style="left:{px:.0f}px;top:{py:.0f}px;width:{pw:.0f}px;height:{ph:.0f}px">' for a,(px,py,pw,ph) in zip(b.arts,rects))
    if LB: imgs+=''.join(f'<div style="position:absolute;left:{px+3:.0f}px;top:{py+ph-27:.0f}px;background:#111;color:#fff;font:700 21px Liberation Sans,Arial;padding:1px 7px;border-radius:5px;opacity:.88;z-index:5">{a}</div>' for a,(px,py,pw,ph) in zip(b.arts,rects))
    d=BH*0.74
    price=f'<div class="price" style="width:{BW}px;height:{BH}px;padding-left:10px"><span style="font-size:{d:.0f}px">{E.eur(b.price)}</span><i style="width:{BH*0.46:.0f}px;height:{BH*0.46:.0f}px;font-size:{BH*0.34:.0f}px">€</i></div>'
    return (f'<div class="box" style="left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.1f}px"><div class="txt" style="left:{tx:.0f}px;top:{ty:.0f}px;width:{tw:.0f}px">{txt}</div>{imgs}{price}</div>'),dict(mode=mode,fill=area/(w*h),gx=gx,gy=gy,gw=gw,gh=gh)
def page_html(page,r):
    E.set_boxes([E.Box(d) for d in S.ORD[page]])
    out=[];stats=[]
    for g in geometry(page,r):
        h,st=box_html(*g);out.append(h);stats.append((g[0],st))
    frame=f'<div style="position:absolute;left:0;top:{E.HEAD}px;width:{E.W}px;height:{E.FOOT-E.HEAD}px;border-right:3px solid #111;border-bottom:3px solid #111"></div>'
    return f'<!doctype html><meta charset=utf-8><style>{CSS}</style><img src="head.png" style="position:absolute;left:0;top:0;width:{E.W}px;height:{E.HEAD}px">'+''.join(out)+frame+f'<img src="foot.png" style="position:absolute;left:0;top:{E.FOOT}px;width:{E.W}px;height:{t16.height-E.FOOT}px">',stats
PROBS={}
def shoot(jobs):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch();pg=b.new_page(viewport={'width':E.W,'height':t16.height})
        for name,hm in jobs:
            open(f'out/{name}.html','w').write(hm)
            pg.goto(f'file://out/{name}.html');pg.wait_for_timeout(300)
            pg.screenshot(path=f'out/{name}.png')
            probs=pg.evaluate('''()=>{const out=[];const R=e=>e.getBoundingClientRect();
            document.querySelectorAll('.box').forEach((bx,i)=>{const b=R(bx);const t=bx.querySelector('.txt');if(!t)return;const tr=R(t);
              const ps=R(bx.querySelector('.price'));
              const kids=[...t.children];let tb=0,tR=0;kids.forEach(k=>{const r=R(k);tb=Math.max(tb,r.bottom);tR=Math.max(tR,r.right)});
              const nm=t.querySelector('.t').textContent.slice(0,18);
              if(tb>b.bottom+1)out.push(nm+': yazı kutu altından taşıyor');
              if(t.scrollWidth>t.clientWidth+1)out.push(nm+': yazı yana taşıyor');
              const bad=(a,c)=>!(a.right<=c.left+1||c.right<=a.left+1||a.bottom<=c.top+1||c.bottom<=a.top+1);
              kids.forEach(k=>{const kr=R(k);if(bad(kr,ps))out.push(nm+': yazı fiyat etiketine biniyor');
                bx.querySelectorAll('img').forEach(im=>{if(bad(kr,R(im)))out.push(nm+': yazı fotoğrafa biniyor')})});
              bx.querySelectorAll('img').forEach(im=>{const r=R(im);if(r.right>b.right+2||r.bottom>b.bottom+2||r.left<b.left-2)out.push(nm+': foto kutudan taşıyor');
                if(bad(r,ps))out.push(nm+': foto fiyat etiketine biniyor')});
            });return out}''')
            PROBS[name]=probs
            im=Image.open(f'out/{name}.png');im.thumbnail((800,1130));im.save(f'out/th_{name}.png')
        b.close()
