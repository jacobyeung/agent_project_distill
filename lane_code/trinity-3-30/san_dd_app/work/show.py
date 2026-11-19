"""Compact view: objects labelled by truth rank (1 = seen first). Lane san_dd_app."""
import sys; sys.path.insert(0,'/scratch/jjyeung/orch_n30/san_dd_app/work'); import app as A, pred as Q
def line(p, truth, tag):
    rk={o:i+1 for i,o in enumerate(truth)}
    f=' '.join('%d:%g%s'%(rk[o],p['fr'][o],'*' if p['fr'][o]>32 else '') for o in truth)
    w=''.join(str(rk[o]) for o in p['w']); a=''.join(str(rk[o]) for o in p['op'][p['pred']])
    fo=''.join(str(rk[o]) for o in p['fo'])
    return '  %s f[%s] fo=%s w=%s%s a=%s%s%s'%(tag,f,fo,w,'' if p['w_opt'] else '(noopt)',a,' OK' if p['score']==1 else '','' if (p['w_opt'] or p['w_opt']==p['pred']) else '')
def show(ids, P544, P100, P200, opts=True):
    for k,i in enumerate(ids):
        p=P200[i]; t=p['truth']
        print('[%d] %s gt=%s q=%s truth: %s'%(k,i[:12],p['gt'],''.join(str(t.index(o)+1) for o in p['q']),' > '.join(x[:14] for x in t)))
        if opts: print('   opts: '+' '.join('%s=%s'%(L,''.join(str(t.index(o)+1) for o in v)) for L,v in sorted(p['op'].items())))
        for tag,P in (('544',P544),('100',P100),('200',P200)): print(line(P[i],t,tag))
