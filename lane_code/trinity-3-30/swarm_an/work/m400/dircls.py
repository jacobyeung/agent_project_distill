"""Classify direction traces (toward/away) at steps 544,100,200,400. Read-only."""
import sys,re,json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter, defaultdict
def opening(t):
    l=t.strip().split('\n')[0]
    if l.startswith('Seen:'): return 'Seen:'
    if l.startswith('Step 1: locate'): return 'Step1:locate'
    if l.startswith('Step 1: find'): return 'Step1:find-then' if ' then ' in l else 'Step1:find'
    if l.startswith('Step 1: I find'): return 'Step1:I-find'
    if l.startswith('Step 1:'): return 'Step1:other'
    return 'other:'+l[:20]
def rel(s):
    s=s.lower(); fb=None; lr=None
    if 'behind' in s or 'at my back' in s or 'to my back' in s: fb='back'
    elif 'in front' in s or 'ahead of me' in s: fb='front'
    if re.search(r'\bleft\b',s): lr='left'
    if re.search(r'\bright\b',s): lr='right' if lr is None else 'both'
    return fb,lr
def lab(s):
    s=s.lower().strip().rstrip('.')
    m=re.search(r'(front-left|front-right|back-left|back-right)',s)
    if m: return m.group(1)
    m=re.findall(r'\b(left|right|back)\b',s)
    return m[-1] if m else None
def classify(r):
    q=r['question']; away=bool(re.search(r'away from|opposite direction|back to|turned away|back toward', q))
    t=(r['text'] or ''); th=t.split('</think>')[0]
    L=[l.strip() for l in th.strip().split('\n') if l.strip()]
    o=opening(th) if L else 'empty'
    relline=None; form=None
    for l in L[1:] if o=='Seen:' else L:
        if 'If I stood' in l or 'would be' in l: relline=l; form='ifstood'; break
        if l.startswith('Standing at') and ' I find' in l: relline=l; form='standing'; break
        if 'degrees' in l and 'straight ahead' in l: relline=l; form='deg'; break
        if 'I stand at' in l and 'I find' in l: relline=l; form='stand'; break
        if l.startswith('Step 1: I find') or ('I find' in l and 'when I stand' in l): relline=l; form='find-when'; break
    tl=[l for l in L if l.startswith('The question has me')]
    tl=tl[0] if tl else ''
    if not tl: turn='none-line'
    elif ('half turn' in tl or 'swap' in tl) and ('keep' in tl or 'no turn' in tl): turn='mixed'
    elif 'half turn' in tl or 'swap' in tl: turn='turn'
    elif 'keep' in tl or 'no turn' in tl: turn='keep'
    else: turn='other'
    fin=[l for l in L if l.startswith('So ')]; fin=lab(fin[-1]) if fin else None
    fb,lr=rel(relline) if relline else (None,None)
    if form=='deg' and relline and 'turn of less than' in relline: fb='side'
    if form=='deg' and relline and 'turn of at' in relline: fb='back'
    opts={o_[0]:o_[3:].strip() for o_ in r['options']}
    pred=opts.get((r['pred'] or '').strip()[:1]); truth=opts.get(str(r['gt']).strip()[:1], r['gt'])
    return dict(id=r['id'],type=r['type'][len('object_rel_direction_'):],away=away,open=o,form=form,turn=turn,fb=fb,lr=lr,final=fin,pred=pred,truth=truth,
                right=(r['score'] or 0)>0.5,follows=(fin==pred),fc=r['forced_close'],relline=relline,tl=tl)
def load(run,st,setname):
    if setname in ('away','forward'): rows=K.facing(run,st,setname)
    else: rows=[r for r in K.direct(run,st,setname) if 'direction' in r['type']]
    return [classify(r) for r in rows]
if __name__=='__main__':
    out={}
    for run,st,s in (('S1',544,'forward'),('R1',200,'forward'),('R1',400,'forward'),('S1',544,'away'),('R1',200,'away'),('R1',400,'away'),
                     ('S1',544,'dev-S1'),('R1',100,'dev-S1'),('R1',200,'dev-S1'),('R1',400,'dev-S1'),
                     ('S1',544,'R0-dev'),('R1',100,'R0-dev'),('R1',200,'R0-dev'),('R1',400,'R0-dev')):
        out['%s|%d|%s'%(run,st,s)]=load(run,st,s)
    json.dump(out,open('/tmp/san_dircls.json','w'))
    for k,v in out.items():
        print(k,len(v),'open',dict(Counter(x['open'] for x in v)),'form',dict(Counter(x['form'] for x in v)),'turn',dict(Counter(x['turn'] for x in v)),
              'final None',sum(x['final'] is None for x in v),'fb None',sum(x['fb'] is None and x['form']!=None for x in v),'nofollow',sum(not x['follows'] for x in v))
