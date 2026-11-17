import json,collections,re
d=json.load(open('n2r/full_c8r/x/native/R1.json'))
def gstat(resp):
    r=(resp or '').strip()
    m=re.match(r'^(.*?): (not seen|unresolved|box unavailable)$',r)
    if m: return m[2]
    if ': frames' in r: return 'seen'
    if r.startswith('error'): return 'error'
    return 'other:'+r[:30]
out={}
for arm in ('unflagged','scripted'):
    A=[a for a in d['arms'][arm] if a['question_type']=='object_abs_distance']
    recs={}
    for a in A:
        key=a['key'].split(':',1)[1]
        if 'decode' not in a: recs[key]=dict(refused=a.get('geometry_refusal'),calls=[]); continue
        calls=a['decode'].get('calls') or []
        cs=[]
        for c in calls:
            m=re.search(r'obj="([^"]*)"',c.get('call') or '')
            st=gstat(c.get('response')) if c.get('kind')=='ground' else ((c.get('response') or '').strip()[:40])
            cs.append(dict(kind=c.get('kind'),name=m[1] if m else None,st=st,call=c.get('call')))
        recs[key]=dict(calls=cs,finish=a['decode'].get('finish'),score=a['scores'],capped=a.get('capped'))
    out[arm]=recs
json.dump(out,open('n2r_calls.json','w'))
for arm in out:
    C=collections.Counter(c['st'] for r in out[arm].values() for c in r['calls'] if c['kind']=='ground'); print(arm,'ground statuses',C)
    G=collections.Counter(c['st'] if c['st'] in ('not seen','unresolved','box unavailable') else ('value' if re.search(r'\d',c['st']) else c['st']) for r in out[arm].values() for c in r['calls'] if c['kind']=='gap'); print(arm,'gap',G)
