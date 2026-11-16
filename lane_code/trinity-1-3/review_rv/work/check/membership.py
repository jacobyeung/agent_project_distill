import json,sys
from pathlib import Path
from collections import Counter
K=Path('/scratch/jjyeung/orch_n30/review_rv/work/fresh')
for d in ('reader','reader/evaluator','cohort','launcher'):sys.path.insert(0,str(K/d))
import official_adapter as A
spec=A.dataset(K/'inputs/revsi999_rows_t32.json')
cfg=dict(datasets=[spec],roots=dict(revsi_video_root='/x/v0'))
ts=A.membership(cfg)
print(len(ts), dict(Counter(t['question_type'] for t in ts))==A.COUNTS, len({t['scene'] for t in ts}))
co=[json.loads(l) for l in open(K/'cohort/COHORT_REVSI5.jsonl')]
print('order equals cohort', [t['example_id'] for t in ts]==[c['qid'] for c in co])
# unfiltered prompt equality for kept items
spec0={k:v for k,v in spec.items() if k!='question_types'}
import data
full={t['example_id']:t for t in data.tasks_for(spec0,cfg['roots'])}
from evalpath.official import build_prompt_context
print('kept rows identical to unfiltered', all(full[t['example_id']]==t for t in ts), 'prompts equal', all(build_prompt_context(dict(full[t['example_id']]),'ours')==build_prompt_context(dict(t),'ours') for t in ts))
print('label-free prompt sample:', repr(build_prompt_context(dict(ts[0]),'ours')[:300]))
gt_in=[t['example_id'] for t in ts if t['options']==[] and str(t['ground_truth']) in build_prompt_context(dict(t),'ours').split()]
print('numeric GT token appearing in prompt (count)',len(gt_in))
