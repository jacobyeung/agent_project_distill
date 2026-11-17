import sys,json,collections
from pathlib import Path
W=Path.cwd();sys.path.insert(0,str(W/'in/eat1'));import scan
A=W/'in/pkg/p';B=W/'work/p'
changed=[str(p.relative_to(B)) for p in B.rglob('*.py') if not (A/p.relative_to(B)).exists() or p.read_bytes()!=(A/p.relative_to(B)).read_bytes()]
outputs={}
for label,root in [('before',A),('after',B)]:
 files=[root/n for n in changed if (root/n).exists()]
 fs,sup=scan.scan(files,root=root)
 outputs[label]=fs
 (W/'out'/('EAT1_'+label+'.json')).write_text(json.dumps(dict(files=changed,findings=fs,suppressed=sup),indent=2))
 print(label,len(fs),dict(collections.Counter(x['rule'] for x in fs)))
def key(x):return x['rel'],x['function'],x['rule'],x['detail'],x['text']
c=collections.Counter(key(x) for x in outputs['before']);new=[]
for x in outputs['after']:
 k=key(x)
 if c[k]:c[k]-=1
 else:new.append(x)
(W/'out/EAT1_new.json').write_text(json.dumps(new,indent=2))
for x in new:print(x['rel'],x['function'],x['rule'],x['text'])
decision={'b/e2e_reader/stage1.py','b/e2e_reader/grounding.py','b/e2e_reader/servers.py','h1eval/h10/perception_own.py','h1eval/perception.py'}
def semantic(x):return x['rel'],x['function'],x['rule'],x['detail']
before=collections.Counter(semantic(x) for x in outputs['before'] if x['rel'] in decision)
after=collections.Counter(semantic(x) for x in outputs['after'] if x['rel'] in decision)
new_semantic=list((after-before).elements())
gate=dict(scope=sorted(decision),before_findings=sum(before.values()),after_findings=sum(after.values()),
 new_findings=new_semantic,passed=not new_semantic,
 matching='file, function, rule, detail multiset; line and source text may shift',
 exclusions={'h1eval/h10/depth_snapshot.py':'writes and hashes output after generator returns',
             'orchard_h10/build.py':'build-time payload inventory',
             'h1eval/h10/launch.py':'read orchestration and journal persistence',
             'orchard_h10/job.py':'job setup', 'orchard_h10/runner.py':'job setup', 'orchard_h10/prepare.py':'read setup'},
 no_allowlist_changes=True,whole_reader_EAT1_pass=False)
(W/'out/EAT1_GATE.json').write_text(json.dumps(gate,indent=2)+'\n')
print('G3 decision-path delta',json.dumps(gate))
assert not new_semantic
