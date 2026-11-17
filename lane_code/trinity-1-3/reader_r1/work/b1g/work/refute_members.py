import sys,json,uuid
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/reader_r1/work/b1g/out/src/orchard_h10/vendor')
import chain_save as S
r=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1g/work/tmp/r_'+uuid.uuid4().hex[:8])
def w(p,s='x'):p=r/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
w('metadata/IDENTITY.json');w('metadata/RETURN_ID.json');w('SUMMARY.json');w('logs/1.log')
for i,t in ((0,3),(0,0),(0,1),(0,2),(0,4),(1,3)):
    w(f'metadata/reads/{i}/metadata/0.json');w(f'metadata/reads/{i}/metadata/IDENTITY.json')
    w(f'metadata/reads/{i}/metadata/journals/{t}/0/items.jsonl');w(f'metadata/reads/{i}/metadata/journals/{t}/0/environment.json')
    w(f'metadata/reads/{i}/metadata/journals/{t}/0/SUMMARY.json');w(f'metadata/reads/{i}/metadata/journals/{t}/0/STEPS.jsonl');w(f'metadata/reads/{i}/metadata/journals/{t}/0/logs/{t}0.log')
m=sorted(S.members(r))
print('\n'.join(m))
print('journals returned:',[x for x in m if 'journals' in x])
