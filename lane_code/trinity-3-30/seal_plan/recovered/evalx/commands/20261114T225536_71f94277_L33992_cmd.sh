<!-- recovered by seal_plan: transcript=71f94277 line=33992 utc=2026-11-14T22:55:36.735Z kind=commands original_path=(bash command)  -->
P=/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_02/pilot_candidate_advanced; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
c=json.load(open('$P/CONFIG.json'))
print({k:c.get(k) for k in ('mode','partition','step','token','build_only')})
w=c.get('worker',{}); print('artifact',json.dumps(w.get('artifact'))[:200]); print('family',c['family']['sha256'])
print('pilot_selection',json.dumps(w.get('pilot_selection'))[:500])
"; cat $P/ORDER.md | cut -c1-300