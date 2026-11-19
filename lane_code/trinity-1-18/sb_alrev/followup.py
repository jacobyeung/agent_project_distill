"""Follow-up checks for the sb_alrev review: tier-B pin, baseline split, ScanNet++ coverage, near misses."""
import collections, hashlib, json, sqlite3, sys, tarfile
from pathlib import Path
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1'); sys.path.insert(0, str(TREE))
from student_pilot.r1_rooms import Rooms

OUT = Path(__file__).resolve().parent
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
KIT = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k')
mint = lambda n, s: 'v' + hashlib.sha256(f'rung1 scene {n}/{s}'.encode()).hexdigest()[:12]
NAT = {'scannet': 'scannet', 'scannetpp': 'scannetppv2', 'scannetppv2': 'scannetppv2', 'arkitscenes': 'arkitscenes'}
PFX = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}
alias = lambda c: PFX[c.split('/')[0]] + '/' + mint(NAT[c.split('/')[0]], c.split('/', 1)[1])
rev = json.load(open(OUT/'review_out.json'))
R = Rooms(json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/build17/proofs/rooms/RESULT.json'))['audit']['authority'])
res = {}

# Tier B pin
tar = Path('/scratch/jjyeung/n30_mirror/b08_headrows/b08_partB_kit.tar')
with tarfile.open(tar) as t: raw = t.extractfile('work/auth/alias_map.json').read()
B = json.loads(raw); hashed = {k: v for k, v in B.items() if '/v' in k and len(k.split('/')[1]) == 13}
res['B_member_sha256'] = hashlib.sha256(raw).hexdigest()
res['B_entries'] = len(B); res['B_hashed'] = len(hashed)
res['B_hashed_mint_agree'] = sum(alias(v) == k for k, v in hashed.items())
lit = {k: v for k, v in B.items() if k not in hashed}
res['B_literal_examples'] = list(lit.items())[:3]
res['B_literal_consistent'] = sum(k.split('/', 1)[1] == v.split('/', 1)[1] for k, v in lit.items())

# Baseline (N's Rooms.status with its pinned c47c5fcd aliases) and the new K1 rows
tm = json.load(open('/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'))['aliases']
k1 = set(R.k1); base = collections.Counter(); new_k1 = collections.Counter(); base_k1_not_full = 0; tokens = set()
con = sqlite3.connect(STORE.as_uri() + '?mode=ro&immutable=1', uri=True)
for (raw,) in con.execute('select row from rows order by i'):
    r = json.loads(raw); st, can, how = R.status(r); base[st] += 1; base['how:' + how] += 1
    t = r['dataset'] + '/' + r['scene']; tokens.add(t)
    full = R.room(tm[t]['canonical']) in k1
    if st == 'k1_heldout' and not full: base_k1_not_full += 1
    if full and st != 'k1_heldout': new_k1[st] += 1
res['baseline_N_status'] = dict(base); res['new_k1_rows_by_baseline_status'] = dict(new_k1)
res['baseline_k1_rows_not_k1_in_full'] = base_k1_not_full

# ScanNet++ tokens resolvable without the builder's candidate list
own = set()
for p in (KIT/'benchmark_scene_exclusions.json', KIT/'dev_scene_exclusions.json'):
    own |= {x.split('/')[-1] for x in json.dumps(json.load(open(p))).replace('"', ' ').split() if x.startswith(('scannetpp', 'd2/'))}
w80 = json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json'))
own |= {x.split('/')[1] for x in w80['rooms'] if x.startswith('scannetpp')}
own |= {x.split('/')[1] for x in open('/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt').read().split() if x.startswith('scannetpp')}
for (raw,) in con.execute('select row from rows'):
    c = (json.loads(raw).get('provenance') or {}).get('canonical') or ''
    if c.startswith('scannetpp'): own.add(c.split('/')[1])
d2 = {t for t in tokens if t.startswith('d2/')}
res['d2_tokens'] = len(d2); res['d2_resolved_without_builder_candidates'] = len(d2 & {'d2/' + mint('scannetppv2', s) for s in own})
res['d2_tier_of_rest'] = dict(collections.Counter(tm[t]['tier'] for t in d2 - {'d2/' + mint('scannetppv2', s) for s in own}))

# Near misses: longest shared hex prefix and min Hamming distance, v7 tokens vs every list-room token
bench = json.load(open(KIT/'benchmark_scene_exclusions.json'))
listed = {a + '/' + b for a, b in bench['rung1_tokens']} | {x for v in w80['aliases'].values() for x in v if '/v' in x}
listed |= {x for v in json.load(open(KIT/'dev_scene_exclusions.json'))['aliases'].values() for x in v if '/v' in x}
for room in R.r0 | set(w80['rooms']):
    ds, c = room.split('/', 1)
    if ds == 'scannet': listed |= {'d1/' + mint('scannet', f'{c}_{b:02d}') for b in range(100)}
    else: listed |= {'d2/' + mint('scannetppv2', c)}
lh = [x.split('/')[1][1:] for x in listed]; vh = [t.split('/')[1][1:] for t in tokens if t not in {x for x in tokens if R.room(tm[x]['canonical']) in k1}]
best_pref = 0; best_ham = 12
for a in vh:
    for b in lh:
        p = 0
        while p < 12 and a[p] == b[p]: p += 1
        if p > best_pref: best_pref = p
        h = sum(x != y for x, y in zip(a, b))
        if h < best_ham: best_ham = h
res['near_miss'] = dict(v7_non_k1_tokens=len(vh), list_tokens=len(lh), longest_shared_hex_prefix=best_pref, min_hamming_of_12=best_ham)
res['visits_max_video_id'] = max(int(v) for v in R.visits); res['visits_NA'] = sum(v == 'NA' for v in R.visits.values())
res['k1_rooms_by_dataset'] = dict(collections.Counter(x.split('/')[0] for x in k1))
(OUT/'followup_out.json').write_text(json.dumps(res, indent=1, default=str) + '\n'); print(json.dumps(res, indent=1, default=str))
