"""Independent recompute of the 'recovery' population against BENCH v2 (no r1_rooms, no alias table)."""
import csv, hashlib, json, re, sys
from collections import Counter

BENCH = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w12/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'
VISITS = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/657020f2d1119220b5068176ffc7298a8585076468407b60d8f5e3e6223442ca.json'
ROWS = sys.argv[1] if len(sys.argv) > 1 else '/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl'
SCOPE = ('VSI-Bench', 'VSTI', 'ReVSI')
NATIVE = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def token(native, scene):
    return 'v' + hashlib.sha256(('rung1 scene ' + native + '/' + scene).encode()).hexdigest()[:12]


bench = json.load(open(BENCH))
with open(VISITS) as f:
    visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(f)}

# Bench captures, tokens and physical rooms, per bank.
cap, tok, room = ({b: set() for b in SCOPE} for _ in range(3))
mine_tokens = set()
for name, facts in bench['members'].items():
    d, s = name.split('/', 1)
    t = token(NATIVE[d], s)
    mine_tokens.add((d, t))
    for b in set(facts['benchmarks']) & set(SCOPE):
        cap[b].add((d, s)); tok[b].add((d, t)); room[b].add(facts['group'])
for corpus, names in bench['other_corpora'].items():
    owners = [b for b, c in bench['by_benchmark'].items() if corpus in c]
    for b in set(owners) & set(SCOPE):
        room[b].update(corpus + '/' + n for n in names)
rung1 = {tuple(x) for x in bench['rung1_tokens']}


def row_room(d, s):
    if d == 'd1':
        m = re.match(r'(scene\d+)_\d+$', s)
        return 'scannet/' + m.group(1) if m else None
    if d == 'd2':
        return 'scannetpp/' + s
    if d == 'd3':
        v = visits.get(s)
        return 'arkitscenes/venue' + v if v and v != 'NA' else 'arkitscenes/capture' + s


stats = Counter(); hits = {b: set() for b in SCOPE}; rooms_seen = set()
for line in open(ROWS):
    if not line.strip():
        continue
    r = json.loads(line); stats['rows'] += 1
    canon = (r.get('canonical') or (r.get('provenance') or {}).get('canonical')
             or (r.get('ground_record') or {}).get('canonical') or (r.get('gt_authority') or {}).get('canonical'))
    ds, s = canon.split('/', 1)
    d = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}[ds]
    stats['token_consistent' if token(NATIVE[d], s) == r.get('scene') and d == r.get('dataset') else 'token_mismatch'] += 1
    rm = row_room(d, s); rooms_seen.add(rm)
    for b in SCOPE:
        if (d, s) in cap[b] or (r.get('dataset'), r.get('scene')) in tok[b] or rm in room[b]:
            hits[b].add(rm)
print(json.dumps(dict(bench_sha256=sha(BENCH), visits_sha256=sha(VISITS), rows_sha256=sha(ROWS),
    my_tokens_equal_bench_rung1=(mine_tokens == rung1), rung1=len(rung1),
    bank_sizes={b: dict(captures=len(cap[b]), rooms=len(room[b])) for b in SCOPE},
    stats=dict(stats), unique_rooms=len(rooms_seen), overlaps={b: sorted(v) for b, v in hits.items()})))
