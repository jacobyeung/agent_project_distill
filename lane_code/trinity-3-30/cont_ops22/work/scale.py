import gzip,json,math,statistics,sys
def load(f,arm='tower'):
    out={}
    for l in gzip.open(f):
        r=json.loads(l)
        if r['question_type'] not in ('camera_displacement','camera_rotation'): continue
        a=r['arms'].get(arm)
        if not a: continue
        try: p=float(a['answer']); t=float(r['truth']['scored'])
        except Exception: continue
        if p>0 and t>0: out[r['item_id']]=(r['question_type'],math.log(p/t))
    return out
runs={k:load(v) for k,v in [('s400','6ed2c7aa_s400_devS1_routed_A10b.jsonl.gz'),('s544','469ddece_s544_devS1_routed_b1.r0.jsonl.gz'),('s600','6ed2c7aa_s600_devS1cam_c600_173348.jsonl.gz')]}
for t in ('camera_displacement','camera_rotation'):
    ids=set.intersection(*[set(i for i,(q,_) in r.items() if q==t) for r in runs.values()])
    line=[t,len(ids)]
    for k,r in runs.items():
        v=[r[i][1] for i in ids]; line.append('%s median ratio %.3f mean log %.3f'%(k,math.exp(statistics.median(v)),statistics.mean(v)))
    d=[runs['s600'][i][1]-runs['s400'][i][1] for i in ids]; line.append('600-400 paired median ratio %.3f'%math.exp(statistics.median(d)))
    print(' | '.join(map(str,line)))
