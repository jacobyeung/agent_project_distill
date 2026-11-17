from pathlib import Path
import sys,json,collections
W=Path.cwd();O=W/'out'
sys.path.insert(0,str(W.parent/'b1/in/eat1'));import scan
files=['b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','h1eval/h10/perception_own.py','h1eval/perception.py','b/e2e_reader/real.py','b/e2e_reader/parity.py','b/e2e_reader/perception_memo.py']
key=lambda r:(r['rel'],r['function'],r['rule'],r['detail'])
res={};raw={}
for label,root in [('bf94',W.parent/'b1p/out/baseline'),('e47',O/'baseline'),('c91',W.parent/'b1m/out/src'),('new',O/'src')]:
 rows,suppressed=scan.scan([root/n for n in files if (root/n).exists()],root=root)
 raw[label]=rows;res[label]=collections.Counter(key(r) for r in rows if r['clause'] in ('A3','A4'))
 (O/f'EAT1_{label}.json').write_text(json.dumps(dict(findings=rows,suppressed=suppressed),indent=2)+'\n')
deltas={label:dict(before=sum(res[label].values()),after=sum(res['new'].values()),added=list((res['new']-res[label]).elements()),removed=list((res[label]-res['new']).elements())) for label in ('bf94','e47','c91')}
(O/'EAT1_DELTA.json').write_text(json.dumps(deltas,indent=2)+'\n');print(json.dumps(deltas,indent=2))
