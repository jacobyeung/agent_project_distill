echo "== $(hostname -s) $(date -u +%T)"
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, os, collections
b = json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'))
for k, v in b['inputs'].items(): print('input', k, v[:12], os.path.exists(k))
print('physical_groups prefixes', collections.Counter(g.split('/')[0] for g in b['physical_groups']))
print('scenes prefixes', collections.Counter(s.split('/')[0] for s in b['scenes']))
bb = collections.Counter(); 
for s, m in b['members'].items():
    for x in m['benchmarks']: bb[x] += 1
print('members by benchmark', dict(bb)); print('counts', b['counts']); print('rule', b['rule'][:800])
print('benchmark', b['benchmark'])
r0 = open('/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt').read().split()
print('R0 prefixes', collections.Counter(x.split('/')[0] for x in r0), r0[-3:])
d = json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json'))
print('dev natives prefixes', collections.Counter(x.split('/')[0] for x in d['natives']), 'pg', collections.Counter(x.split('/')[0] for x in d['physical_groups']))
t = json.load(open('/scratch/jjyeung/orch_n30/sb_alias2/work/TEACHER_K1.raw'))
c = t['captures'][0]; print('teacher capture keys', sorted(c))
print('teacher split counter', collections.Counter(x.get('split') for x in t['captures']))
PY
