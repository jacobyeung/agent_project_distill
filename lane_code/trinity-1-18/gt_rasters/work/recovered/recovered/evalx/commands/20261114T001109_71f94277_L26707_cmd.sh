<!-- recovered by seal_plan: transcript=71f94277 line=26707 utc=2026-11-14T00:11:09.498Z kind=commands original_path=(bash command)  -->
M=/scratch/jjyeung/orch_cd/evalx/work/milestone; grep -n 'def test_' $M/test_producer_error_ruling.py | cut -c1-160; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
v=json.load(open('$M/test_runs/producer_errors_step50_fixture.json'))
recs=v if isinstance(v,list) else v.get('records', v)
print(type(recs).__name__, (list(recs)[:6] if isinstance(recs,dict) else len(recs)))
def show(r):
    print({k:r.get(k) for k in ('key','qid','question_type','finish_reason','error_type','error_stage','derivation_error','forced_close','stopped_unclosed','budget','max_new_tokens','output_tokens','score','parse_failed','answer_cap_policy','thinking_tokens')})
    print(str(r.get('error'))[:300])
items = recs if isinstance(recs,list) else [x for x in recs.values() if isinstance(x,dict)]
for r in items[:4]:
    if isinstance(r,dict) and 'record' in r: show(r['record'])
    elif isinstance(r,dict): show(r)
"; grep -n 'tagged_continuations\|"producer_errors"' $M/RULING4_TAG_COUNTS_STEP50.json | cut -c1-120