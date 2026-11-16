import json,sys
d=json.load(open(sys.argv[1]))
def big(c): return any(k in c['name'] for k in ('6000','A40','L40'))
for n,v in d.items():
    if not v['permitted']: continue
    free=[c['id'] for c in v['cards'] if big(c) and not c['users'] and (c['avail'] or 0)>45000]
    if not free: continue
    try: u,t=[int(x.rstrip('GB')) for x in v['scratch'].split('/')]
    except: continue
    a=int(t-u-0.05*t)  # df Avail is about 5% of total below total-used (root reserve)
    if n in ('trinity-1-3','trinity-1-18') or a>=250:
        print(f"CANDIDATE {n} free={free} scratch_avail~{a}GB upd={v['updated']}")
