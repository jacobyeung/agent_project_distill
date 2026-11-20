cd /scratch/jjyeung
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,collections,os
m=json.load(open('orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
caps=m['captures'] if isinstance(m,dict) and 'captures' in m else m
print(type(m), list(m)[:10] if isinstance(m,dict) else len(m))
c=caps[0]; print({k:(str(v)[:150]) for k,v in c.items()})
roots=collections.Counter()
for c in caps:
    p=c.get('gt',{}).get('path') if isinstance(c.get('gt'),dict) else None
    if p: roots[os.path.dirname(os.path.dirname(p))]+=1
print(roots.most_common(10))
PY
grep -n "scratch/jjyeung" orch_n30/k1_ops3/work/e3gd/harness.py | head -20
grep -n "scratch/jjyeung" orch_n30/sb_kbox4/*.py | cut -c1-220 | head -30
grep -n "scratch/jjyeung" orch_n30/geo_k1/harness/*.py 2>/dev/null | cut -c1-200 | head -10
ls n30_mirror/tower_redecide n30_mirror/gt_audit/gt_audit | head; du -s --block-size=1M orch_cd/evalx/work/milestone/native_package_s24_05 orch_cd/evalx/work/milestone/native_package_s24_05/sources 2>/dev/null
ls orch_n30/b04host3 | head -20
PY=1
