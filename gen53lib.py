import sys,os;sys.path.insert(0,'.')
import render as R,search as S,engine as E
U=E.W/50.0
def build(page,rows,spec_,name):
    ys=[E.HEAD]
    for h in rows: ys.append(ys[-1]+h)
    out=[];st=[]
    for (i,x,w,r0,r1) in spec_:
        h,s=R.box_html(i,x*U,ys[r0],w*U,ys[r1+1]-ys[r0],r1>r0);out.append(h);st.append((i,s,(i,x,w,r0,r1)))
    t=R.t16
    frame=f'<div style="position:absolute;left:0;top:{E.HEAD}px;width:{E.W}px;height:{E.FOOT-E.HEAD}px;border-right:3px solid #111;border-bottom:3px solid #111"></div>'
    hm=f'<!doctype html><meta charset=utf-8><style>{R.CSS}</style><img src="head.png" style="position:absolute;left:0;top:0;width:{E.W}px;height:{E.HEAD}px">'+''.join(out)+frame+f'<img src="foot.png" style="position:absolute;left:0;top:{E.FOOT}px;width:{E.W}px;height:{t.height-E.FOOT}px">'
    f=[];print(name)
    for i,sx,sp in st:
        if sx:
            hh=(sp[4]-sp[3]+1)*466;ww=sp[2]*U;f.append(sx['fill'])
            print('   %-26s w=%2d fill %.2f H %.2f W %.2f'%(E.BOXES[i].title[:26],sp[2],sx['fill'],sx['gh']/hh,sx['gw']/ww))
    print('  avg fill %.2f'%(sum(f)/len(f)))
    return name,hm
