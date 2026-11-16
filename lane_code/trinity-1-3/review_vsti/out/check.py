import sys,json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_vsti/work/c')
import scorer,s0
from collections import Counter
C='/scratch/jjyeung/orch_n30/native_r4/in/comparators/'
r=scorer.comparator_check([C+'f17.per_question_scores.jsonl',C+'p1m200.per_question_scores.jsonl'],'/scratch/jjyeung/orch_n30/review_vsti/work/sc/SCORER_CHECK_rerun.json')
for k,v in r.items():print(k,v['primary_pct'],v['official_fuzzy_primary_pct'],len(v['mismatches']),v['collapse'])
# kit score() vs recorded strict score
items={str(i['id']):i for i in json.load(open('/scratch/jjyeung/orch_n30/native_r4/in/vsti/vstibench_repr_450_v3.json'))} if True else {}
for name in ('f17','p1m200'):
    rows=[json.loads(l) for l in open(C+name+'.per_question_scores.jsonl')]
    diff=Counter();ex=[]
    for row in rows:
        it=items[row['example_id']]
        t=row['response_text']
        # mimic final_text on a decoded dict
        ft=scorer.final_text(dict(text=t)) if '</think>' in t else t.strip()
        v=scorer.score(ft,dict(options=it['options'],ground_truth=it['ground_truth']))
        if v['score']!=row['score']:diff['vs_strict']+=1;ex.append((row['example_id'],row['question_type'],repr(t[-80:]),row['score'],v['score']))
        if v['score']!=row['official_fuzzy_score']:diff['vs_fuzzy']+=1
        if row['score']!=row['official_fuzzy_score']:diff['strict_ne_fuzzy_recorded']+=1
    print(name,dict(diff),ex[:5])
