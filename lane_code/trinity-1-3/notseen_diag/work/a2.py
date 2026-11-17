import json,collections,re
F='f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
R=[json.loads(l) for l in open(F)]
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
def status(c):
    r=c.get('response')
    if not c.get('served'): return 'unserved'
    if r is None: return 'none'
    if r.startswith('error'): return 'error'
    if c['family']=='ground':
        m=re.match(r'^(.*?): (not seen|unresolved|box unavailable)$',r.strip())
        if m: return m[2]
        return 'seen' if ': frames' in r else 'other:'+r[:40]
    if c['family']=='gap':
        if r.strip() in ('not seen','unresolved','box unavailable'): return r.strip()
        return 'value' if re.search(r'\d',r) else 'other:'+r[:40]
    return 'other'
rows=[]
for x in R:
    it=I[x['id']]
    recs=x['output']['calls']['records']
    for j,c in enumerate(recs):
        name=None
        m=re.search(r'obj="([^"]*)"',c['call'])
        if m: name=m[1]
        rows.append(dict(id=x['id'],mode=x['mode'],j=j,family=c['family'],name=name,st=status(c),call=c['call'],dataset=it['dataset'],cap=it['native'],q=it['question'],finish=x['output']['finish'],score=x['measurements']['M2']['task_accuracy']))
json.dump(rows,open('calls.json','w'))
C=collections.Counter((r['mode'],r['family'],r['st']) for r in rows)
for k in sorted(C): print(k,C[k])
