D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817; cd $D; date -u +%TZ
sha256sum k_*.json receipt.json materialization.json routing_selection.json | cut -c1-16,65- | tr '\n' ' '; echo
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24t/work/tree_r1c; ls -d $T >/dev/null && grep -rn "source_not_final" $T --include=*.py | cut -c1-250 | head -12
grep -rn "moved_to_vqa_store" $T --include=*.py | cut -c1-250 | head -6
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
r=json.load(open('routing_selection.json')); print('RS keys', list(r)[:30]); print(json.dumps(r.get('inputs_pinned',{}))[:800])
PY
