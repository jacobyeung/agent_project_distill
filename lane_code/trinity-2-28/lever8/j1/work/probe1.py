import sys, json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever7/gtcd/kit')
import gtc_common as G
R=G.load_relift(); R.dependencies()
refs={r['item_id']:r for r in json.loads(G.ITEMS.read_text())['items']}
rows=R.read_records(R.BASE/'cap/t1.gz',refs)
iid=next(iter(rows)); row=rows[iid]
print('row keys',sorted(row.keys()))
print('meta', {k:(v if not isinstance(v,(list,dict)) else type(v).__name__) for k,v in row.items() if k not in ('objects','calls')})
o=row['objects'][0]
print('obj keys',sorted(o.keys()))
for k,v in o.items():
    if k in ('proposals','candidates','selected_masks'):
        print(k,type(v).__name__,len(v))
    else: print(k, str(v)[:300])
p=o['proposals'][0]; print('proposal keys',sorted(p.keys())); print({k:(str(v)[:200]) for k,v in p.items()})
m=R.unrle(p['mask']); print('mask shape',m.shape)
c=o['candidates'][0] if o['candidates'] else None
if c: print('cand keys',sorted(c.keys()), {k:str(v)[:150] for k,v in c.items() if k!='masks'})
for c in row['calls'][:6]: print('call',{k:str(v)[:200] for k,v in c.items()})
