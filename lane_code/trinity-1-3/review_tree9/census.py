import json,re,sys,glob,collections
from decimal import Decimal,ROUND_HALF_EVEN
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_tree9')
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w')
ST=('not seen','unresolved','box unavailable')
out={}
for p in sorted(glob.glob(str(L/'work/rows_slices/slices_final/*.jsonl')))+sorted(glob.glob(str(L/'work/rows_slices/slices_v3/*.jsonl'))):
    name=Path(p).stem
    if name in out: name='v3:'+name
    c=collections.Counter()
    for line in open(p):
        r=json.loads(line);c['rows']+=1
        t=str(r.get('target',r.get('suffix','')))
        spans=re.findall(r'<tool_response>([\s\S]*?)</tool_response>',t)
        ev=r.get('ground_record',{}).get('events',[]) or []
        for s in ST:
            if any(s in x.lower() for x in spans):
                sims=[e.get('audit',{}).get('simulated') for e in ev if s in str(e.get('response','')).lower()]
                k='sim' if sims and all(v is True for v in sims) else ('notsim' if sims and all(v is False for v in sims) else 'unknown')
                c[s+'|'+k]+=1
            # status outside spans (model text)
            if s in re.sub(r'<tool_response>[\s\S]*?</tool_response>','',t).lower(): c[s+'|outside']+=1
    out[name]=dict(c)
units=collections.Counter();bad=[];byqid={}
for line in open(L/'work/rows_slices/slices_final/a0_units.jsonl'):
    r=json.loads(line);q=r['question'];t=r['target']
    u=re.search(r'\(in (centimeters|feet|inches)\)',q) or re.search(r'\b(centimeters|feet|inches)\b',q)
    unit={'centimeters':'cm','feet':'ft','inches':'in'}[u[1]] if u else None
    units[unit]+=1;byqid[r['qid']]=unit
    conv=[l for l in t.splitlines() if re.match(r'\s*Convert',l)]
    m=re.findall(r'<tool_response>[\s\S]*?([0-9.]+) m\s*</tool_response>',t)
    ans=re.search(r'<answer>([^<]*)</answer>\s*$',t)
    why=[]
    if len(conv)!=1: why.append('conv_lines=%d'%len(conv))
    else:
        g=re.search(r'([0-9.]+) x ([0-9.]+) = ([0-9]+(?:\.[0-9]+)?)\.?\s*$',conv[0])
        if not g or len(m)!=1 or Decimal(g[1])!=Decimal(m[0]): why.append('operand')
        elif ans is None or ans[1]!=g[3]: why.append('answer')
        else:
            f={'cm':Decimal(100),'ft':Decimal('3.28084'),'in':Decimal('39.3701')}[unit]
            if Decimal(g[2])!=f: why.append('const')
            q2=Decimal(1).scaleb(-len(g[3].split('.')[1]) if '.' in g[3] else 0)
            if (Decimal(g[1])*f).quantize(q2,ROUND_HALF_EVEN)!=Decimal(g[3]): why.append('arith')
    if ans and re.search(r'\b(m|meters|metres)\b',ans[1]): why.append('metre_answer')
    if ans and m and ans[1]==m[0] and unit!='m': why.append('unconverted_equal_metres')
    if why: bad.append((r['qid'],unit,why))
print(json.dumps(out,indent=0));print('units',dict(units),'bad',len(bad),bad[:5])
json.dump(dict(status=out,units=dict(units),bad=bad,byqid=byqid),open('/scratch/jjyeung/orch_n30/review_tree9/proofs/CENSUS.json','w'))
