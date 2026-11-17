import json,collections
L=[json.loads(l) for l in open('a0_recovery_copy.jsonl')]
ds=collections.Counter(r['dataset'] for r in L)
nmiss=collections.Counter(len(r['provenance']['details']['simulated_misses']) for r in L)
op=collections.Counter(r['provenance']['details']['missed_operand'] for r in L)
names=collections.Counter(m if isinstance(m,str) else json.dumps(m) for r in L for m in r['provenance']['details']['simulated_misses'])
print('rows',len(L),'datasets',dict(ds)); print('misses per row',dict(nmiss)); print('missed operand index',dict(op))
print('top simulated names',names.most_common(25)); print('distinct names',len(names))
ncalls=collections.Counter(r['target'].count('<ground ') for r in L); print('ground calls per row',dict(ncalls))
gaps=collections.Counter(r['target'].count('<gap ') for r in L); print('gap calls per row',dict(gaps))
adm=collections.Counter(r.get('training_admitted') for r in L); print('training_admitted',dict(adm))
# real failure names for comparison
P=json.load(open('pairs_cache.json'))
real=collections.Counter(o['name'] for o in P if o['h1']=='not seen')
sim=set(names); print('real ns names in simulated set:',sum(v for k,v in real.items() if k in sim),'of',sum(real.values()))
print('real names absent from simulated:',[(k,v) for k,v in real.most_common() if k not in sim])
# per-name share of rows in simulated vs real
for k,v in real.most_common(12): print(k,'real',v,'sim rows',names.get(k,0))
