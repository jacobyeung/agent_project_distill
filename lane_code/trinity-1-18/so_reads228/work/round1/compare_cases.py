import json
import math
import os
from pathlib import Path
import sys
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');K=L/'work/round1/kit'
sys.path.insert(0,str(K/'tests'))
import test_review as T
from common228 import read,write
print(subprocess.check_output(['date','-u'],text=True).strip())
cases={}
for name in ('local_identical','orchard_vs_orchard','one_answer_changed','one_call_moved','stage1_one_ulp'):
    root=T.REFERENCE if name=='orchard_vs_orchard' else T.candidate()
    if name not in ('local_identical','orchard_vs_orchard'):
        path=root/'metadata/reads/0/metadata/journals/3/0/items.jsonl'
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if name=='one_answer_changed':
            row=next(r for r in rows if r['output']['finish']!='max_calls');row['output']['text']+='<answer>changed CPU fixture answer</answer>'
        elif name=='one_call_moved':
            row=next(r for r in rows if r['output']['calls']['records']);row['output']['calls']['records'][0]['at_token']+=1
        else:
            record=next(r for row in rows for r in row['output']['calls']['records'] if isinstance(r.get('stage1',{}).get('sam3',{}).get('max_score'),float))
            record['stage1']['sam3']['max_score']=math.nextafter(record['stage1']['sam3']['max_score'],math.inf)
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    got=T.result(root);write(L/'work/round1/checks'/('compare_'+name+'.json'),got)
    cases[name]={k:got[k] for k in ('verdict','eligible','identical','ineligibility_reasons')}
write(L/'work/round1/checks/COMPARE_CASES.json',dict(synthetic_cpu_fixtures=True,actual_device_runs=0,cases=cases))
print(json.dumps(cases,sort_keys=True))
