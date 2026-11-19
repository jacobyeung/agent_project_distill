"""Independent reviewer checks: schema, meaning invariants, assignment, reproducibility."""
import hashlib, json, re, sys, math
from collections import Counter
from pathlib import Path

ROW = Path('/scratch/jjyeung/orch_n30/sb_rowA')
SRC = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src')
sys.path.insert(0, str(ROW))
from wordings import HELDOUT  # templates only; no builder code

T = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
src = json.loads((SRC/'items/devs1_routed.json').read_text())
orig = {x['id']: x for x in src['items'] if x['question_type'] in T}
m = json.loads((ROW/'out/HELDOUT_CAMERA_ITEMS.json').read_text())
tw = json.loads((ROW/'out/HELDOUT_CAMERA_TWINS.json').read_text())
W = json.loads((ROW/'out/WORDINGS.json').read_text())
tasks = [json.loads(l) for l in (ROW/'out/HELDOUT_NATIVE_TASKS.jsonl').read_text().splitlines() if l.strip()]
ntask = {json.loads(l)['id']: json.loads(l) for l in (SRC/'b/work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl').read_text().splitlines() if l.strip()}
items = {x['id']: x for x in m['items']}
res = {}

def enc(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
def tree_types(x):
    if isinstance(x, dict): return ('dict', tuple(sorted((k, tree_types(v)) for k, v in x.items())))
    if isinstance(x, list): return ('list', tuple(tree_types(v) for v in x))
    return type(x).__name__

# WORDINGS.json heldout == wordings.py HELDOUT
res['wordings_json_matches_py'] = W['heldout'] == HELDOUT

# Original templates: one per type?
pat = {
 T[0]: r'Approximately how far \(in meters\) did the camera move between frame (\d+) and frame (\d+) of 32\?',
 T[1]: r'What is the signed camera rotation in degrees between frame (\d+) and frame (\d+) of 32\? Positive means left; use \(-180, 180\]\.',
 T[2]: r"During the sequence between frame (\d+) and frame (\d+) of 32, what was the primary consistent direction of the camera's movement relative to its orientation at the start\? The options are (\w+), (\w+), (\w+) and (\w+)\.",
}
otmpl = Counter()
for x in orig.values():
    mm = re.fullmatch(pat[x['question_type']], x['question'])
    ok = bool(mm) and [int(mm[1]), int(mm[2])] == x['display_frame_pair']
    if ok and x['question_type'] == T[2]:
        words = [w.lower() for w in mm.groups()[2:]]
        ok = words == [re.sub(r'^[A-D]\.\s*', '', o).lower() for o in x['options']] and [o[0] for o in x['options']] == list('ABCD')
    otmpl[(x['question_type'], ok)] += 1
res['original_single_template_and_consistent'] = dict((f'{k[0]}|{k[1]}', v) for k, v in otmpl.items())

# Pairs
schema_bad = diff_bad = meaning_bad = 0; bad_examples = []
counts = Counter(); twin_ids = set()
for p in tw['twins']:
    o = orig[p['original_id']]; a = items[p['original_id']]; b = items[p['reworded_id']]
    t = o['question_type']; i, j = o['display_frame_pair']; n = len(o['source_frame_indices'])
    if a != o: diff_bad += 1
    if set(b) != set(o) or tree_types({k: v for k, v in b.items()}) != tree_types(o): schema_bad += 1
    if {k for k in o if o[k] != b[k]} != {'id', 'question'}: diff_bad += 1
    q = b['question']
    # frame numbers: i appears before j, n present, no other numbers except range constants
    nums = [int(s) for s in re.findall(r'(?<![\d.-])\d+(?![\d.])', q)]
    extra = [v for v in nums if v not in (i, j, n, 180)]
    pos_i = [mm.start() for mm in re.finditer(rf'(?<!\d){i}(?!\d)', q)]
    pos_j = [mm.start() for mm in re.finditer(rf'(?<!\d){j}(?!\d)', q)]
    ok = n == 32 and bool(pos_i) and bool(pos_j) and min(pos_i) < min(pos_j) and str(n) in q and not extra
    if t == T[0]: ok &= ('meters' in q) and not re.search(r'centimet|feet|inch|\bcm\b|path|total distance|travel(l)?ed', q)
    if t == T[1]: ok &= ('(-180, 180]' in q) and 'degree' in q and re.search(r'left', q) is not None and re.search(r'right', q) is None
    if t == T[2]:
        ok &= '; '.join(o['options']) in q and re.search(r'net |overall|endpoint|end point|final position', q) is None
    if not ok: meaning_bad += 1; bad_examples.append(p['reworded_id'])
    k = int(hashlib.sha256(f'sb_rowA|heldout|{tw["seed"]}|{t}|{o["id"]}'.encode()).hexdigest(), 16) % 8
    if p['wording_id'] != f'h{k:02d}' or q != HELDOUT[t][k].format(i=i, j=j, n=n, unit='meters', options='; '.join(o['options'])):
        meaning_bad += 1; bad_examples.append(('assign', p['reworded_id']))
    counts[(t, k)] += 1; twin_ids.add(p['reworded_id'])
res.update(pairs=len(tw['twins']), schema_bad=schema_bad, diff_bad=diff_bad, meaning_bad=meaning_bad, bad_examples=bad_examples[:10])
res['orig_covered'] = set(p['original_id'] for p in tw['twins']) == set(orig)
res['ids_unique_items'] = len(items) == len(m['items']) == 900
res['reworded_ids_collide_with_any_source_id'] = len(twin_ids & {x['id'] for x in src['items']})
res['manifest_digest_ok'] = hashlib.sha256(enc(m['items'])).hexdigest() == m['item_set_sha256']

# Balance per type
bal = {}
for t in T:
    c = [counts[(t, k)] for k in range(8)]
    e = 150 / 8; chi = sum((x - e) ** 2 / e for x in c)
    bal[t] = dict(counts=c, min=min(c), max=max(c), chi2_df7=round(chi, 2))
res['balance'] = bal

# Native tasks
by = Counter(x['id'] for x in tasks)
res['native_unique'] = len(by) == len(tasks) == 900 and set(by) == set(items)
nbad = 0
for x in tasks:
    it = items[x['id']]
    base = ntask[x['id']] if x['id'] in ntask else ntask[x['id'].split('-sbca-')[0]]
    if x['id'] in ntask:
        nbad += x != base
    else:
        nbad += (set(x) != set(base) or tree_types(x) != tree_types(base)
                 or {k for k in base if base[k] != x[k]} != {'id', 'question'} or x['question'] != it['question'])
    for f in ('question', 'question_type', 'options', 'dataset', 'scene', 'native', 'source_frame_indices'):
        nbad += it[f] != x[f]
    nbad += str(it['answer']) != str(x['answer'])
res['native_bad'] = nbad
res['native_sha_matches_twins_pin'] = hashlib.sha256((ROW/'out/HELDOUT_NATIVE_TASKS.jsonl').read_bytes()).hexdigest() == tw['native_tasks']['sha256']
res['native_source_sha'] = hashlib.sha256((SRC/'b/work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl').read_bytes()).hexdigest()

# Reproducibility: rebuild reworded items in memory from wordings + source only
rebuilt = []
for o in orig.values():
    t = o['question_type']; i, j = o['display_frame_pair']
    k = int(hashlib.sha256(f'sb_rowA|heldout|20261118|{t}|{o["id"]}'.encode()).hexdigest(), 16) % 8
    x = dict(o); x['id'] = o['id'] + f'-sbca-h{k:02d}'
    x['question'] = HELDOUT[t][k].format(i=i, j=j, n=32, unit='meters', options='; '.join(o['options']))
    rebuilt += [o, x]
rebuilt.sort(key=lambda x: x['id'])
res['rebuild_identical'] = hashlib.sha256(enc(rebuilt)).hexdigest() == m['item_set_sha256']

# SHA256SUMS integrity
sums_bad = []
for line in (ROW/'out/SHA256SUMS').read_text().splitlines():
    h, name = line.split(None, 1); name = name.lstrip('*')
    p = (ROW/name) if (ROW/name).exists() else (ROW/'out'/Path(name).name)
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h: sums_bad.append(name)
res['sha256sums_mismatch'] = sums_bad
print(json.dumps(res, indent=1, default=str))
