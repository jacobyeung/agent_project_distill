"""Apply the measured encode:detect ratio to K1's amortized GPU rate."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'sb_mask_phrase/part2'))
import sam3_pass as G
ratio=6.5
k1_prompts_per_capture=19.0
# K1's 0.064 s includes encoding amortized across ~19 prompt calls.
detect_frame=.064/(1+ratio/k1_prompts_per_capture)
encode_capture=32*ratio*detect_frame
detect_call=32*detect_frame
new=json.loads(G.NEW.read_text())['phrases']
results={}
for name,aliases in [('default',False),('all_aliases',True)]:
    plan=G.plan(aliases)
    timed=[dict(encode=encode_capture,detect=G.distinct(calls)*detect_call,distinct_calls=G.distinct(calls)) for _,calls in plan[:10]]
    elapsed=sum(x['encode']+x['detect'] for x in timed)
    result=G.projection(timed,[calls for _,calls in plan[10:]],new,elapsed)
    result.update(captures=len(plan),calls=sum(G.distinct(calls) for _,calls in plan),calls_without_new=sum(G.distinct(calls,new) for _,calls in plan),
                  captures_timed=10,calls_in_first_ten=sum(x['distinct_calls'] for x in timed),
                  fits_default_stop=result['projected_gpu_h']<=G.HARD_GPU_H,
                  consequence='W_new MISSING; retain raw/chosen phrases and R_cond' if result['drop_new'] else 'keep all phrases')
    results[name]=result
paths=[Path(__file__),Path(G.__file__),G.NEW,G.HERE/'in/v3/KIT_SPEC_mask_phrase_v2.md',ROOT/'work/ph2rev_probes/REVIEW_VERDICT.md',ROOT/'work/ph2rev_probes/plan_counts.json',ROOT/'work/ph2rev_probes/cpu_first_batch.jsonl']
record=dict(status='ESTIMATE',command='bash sb_mask_phrase/run.sh ../work/estimate_ph2fix2.py',encode_detect_ratio=ratio,
            k1_prompts_per_capture_approx=k1_prompts_per_capture,k1_amortized_prompt_frame_s=.064,detect_frame_s=detect_frame,
            formula='detect_frame_s = 0.064 / (1 + 6.5 / 19); total_s = 32 * detect_frame_s * (6.5 * captures + calls)',
            limitation='Ratio extrapolation, not a GPU measurement. Excludes loading and STEP5; the hard 4320 s timeout includes them. Ten-capture projection keeps the new-phrase work already spent.',
            estimates=results,input_sha256={str(p):G.sha(p) for p in paths})
(ROOT/'out/GPU_ESTIMATE_PH2FIX2.json').write_text(json.dumps(record,indent=1)+'\n')
print(json.dumps(results,indent=1))
