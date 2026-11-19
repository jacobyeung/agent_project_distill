"""Inside sbx.sh scopy: recompute the GPU estimate by hand and through sam3_pass.projection; check they agree."""
import json, sys
from pathlib import Path
KIT = Path('/scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase')
sys.path.insert(0, str(KIT/'part2'))
import sam3_pass as G  # noqa: E402

ratio, k1_prompts = 6.5, 19.0
d = .064/(1+ratio/k1_prompts)
enc, call = 32*ratio*d, 32*d
new = json.loads(G.NEW.read_text())['phrases']
out = dict(detect_frame_s=d, encode_s=enc, call_s=call, hard=G.HARD_GPU_H, timed=G.TIMED)
for name, aliases in (('default', False), ('all_aliases', True)):
    plan = G.plan(aliases)
    calls = [G.distinct(k) for _, k in plan]
    calls_wo = [G.distinct(k, new) for _, k in plan]
    first = sum(calls[:10])
    elapsed = 10*enc + first*call
    full = (elapsed + sum(enc + call*c for c in calls[10:]))/3600
    without = (elapsed + sum(enc + call*c for c in calls_wo[10:]))/3600
    timed = [dict(encode=enc, detect=c*call, distinct_calls=c) for c in calls[:10]]
    p = G.projection(timed, [k for _, k in plan[10:]], new, elapsed)
    out[name] = dict(captures=len(plan), calls=sum(calls), calls_without_new=sum(calls_wo), first_ten=first,
                     first_ten_without_new=sum(calls_wo[:10]), by_hand_full=full, by_hand_without=without,
                     projection=p, agree=abs(p['projected_gpu_h']-full) < 1e-9 and abs(p['projected_gpu_h_without_new']-without) < 1e-9,
                     spec_rate_gpu_h=sum(calls)*32*.064/3600)
Path('/scratch/jjyeung/orch_n30/sb_ph2chk/work/ESTIMATE_CHECK.json').write_text(json.dumps(out, indent=1))
print(json.dumps({k: (v if not isinstance(v, dict) else {x: y for x, y in v.items() if x != 'projection'} | {'drop_new': v['projection']['drop_new'], 'stop': v['projection']['stop']}) for k, v in out.items()}, indent=1))
