"""Reviewer re-probe of sb_ktfix3: every sb_ktchk plant plus new planted-file attacks.
Runs inside a private mount namespace where work/plant3 (a copy of the extracted tar) is bound over the kit path."""
import sys, os, json, subprocess, uuid, hashlib
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktfix2/code')
from common import *
from process_guard import freeze, require_score, directory
OUTFILE = Path(os.environ.get('PLANT_OUT', '/scratch/jjyeung/orch_n30/sb_ktchk2/work/plant2_results.json'))
RES = []
CALL = {'A': 'E.run_a()', 'B': 'E.run_b()', 'C': 'E.run_c()',
        'H': "import process_guard as G;G.require_score(E.OUT,'H');print('H_GUARD_PASSED');E.heldout_once()"}
HEAD = ("import sys;sys.path.insert(0,'code');from pathlib import Path;import evaluate_v2 as E,evaluate as V,camera_pricing as C;"
        "E.OUT=V.OUT=C.OUT=Path(sys.argv[1]);")

def tree(root):
    out = {}
    for d, dirs, files in os.walk(root):
        for n in dirs + files:
            p = Path(d)/n; k = str(p.relative_to(root))
            if p.is_symlink(): out[k] = 'LINK:'+os.readlink(p)
            elif p.is_file(): out[k] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def fresh(name):
    return ROOT/'runtime'/('plant2_'+name+'_'+uuid.uuid4().hex[:8])

def run(root, call):
    return subprocess.run([sys.executable, '-B', '-c', HEAD+call, str(root)], cwd=ROOT, capture_output=True, text=True, timeout=3000)

def record(name, part, planted, root, before, r, expect='refuse', **extra):
    after = tree(root)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    ok = (r.returncode != 0 and not changed) if expect == 'refuse' else None
    RES.append(dict(attempt=name, part=part, planted=planted, expect=expect, returncode=r.returncode, refused='REFUSE:' in r.stderr,
                    guard_passed='H_GUARD_PASSED' in r.stdout, last_error=(r.stderr.strip().splitlines() or [''])[-1][:300],
                    written=changed, ok=ok, **extra))
    print(json.dumps(RES[-1]), flush=True)

def attempt(name, part, rel, content, call=None, expect='refuse', setup=None):
    root = fresh(name); freeze(root, part)
    if setup: setup(root)
    p = root/rel; p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, tuple) and content[0] == 'symlink': os.symlink(content[1](root), p)
    else: p.write_text(content)
    before = tree(root)
    record(name, part, rel, root, before, run(root, call or CALL[part]), expect)

rows = json.dumps(dict(status='OK', rows=[dict(row_id='planted', room='r', split='train', arm='C32_V32_today', score=99.0)]))
one = '{"row_id":"planted","score":99}\n'
# 1. Every sb_ktchk plant.
attempt('A_report', 'A', 'A_DISTANCE.txt', rows)
attempt('A_subdir_bars', 'A', 'parts/A/old/BARS.json', one)
attempt('A_control_per_item', 'A', 'parts/A/PER_ITEM_A_train.jsonl', one)
attempt('B_report', 'B', 'B_LADDER_TRAIN.txt', rows)
attempt('C_report', 'C', 'C_CAMERA.txt', json.dumps(dict(status='OK', rows=[dict(id='planted', arm='G32', score=99.0)])))
attempt('H_report', 'H', 'HELDOUT_once.txt', json.dumps(dict(status='OK', results=dict(A=dict(rows=[dict(row_id='planted', score=99.0)])))))
attempt('H_control_legacy', 'H', 'PER_ITEM_A_heldout.jsonl', one)

# B reads A's per-item rows; a planted A_DISTANCE.txt that disagrees must refuse (both former verdict directions), a matching one proceeds.
import evaluate as V, evaluate_v2 as E
from unittest.mock import patch
from exclusions import population
pop = population()
a_rows = [dict(row_id=i, room=r, split='train', arm=E.arm(32, 32, 'today'), score=50.) for i, r in pop['row_rooms'].items()]
for tag, a_score in (('40', 40.), ('60', 60.), ('match', None)):
    root = fresh('B_A_DISTANCE_'+tag); freeze(root, 'A'); freeze(root, 'B')
    with patch.object(V, 'OUT', root): V.items_file(a_rows, 'A', 'train')
    (root/'A_DISTANCE.txt').write_text(json.dumps(dict(status='OK', rows=[dict(r, score=a_score) if a_score is not None else r for r in a_rows])))
    before = tree(root)
    record('B_reads_planted_A_DISTANCE_'+tag, 'B', 'A_DISTANCE.txt', root, before, run(root, CALL['B']), 'refuse' if a_score is not None else 'proceed')

# Code edit after freeze plus a forged FREEZE.json, for every part; then the two-file forge (BARS.json and FREEZE.json).
m = ROOT/'code/metrics.py'; original = m.read_bytes()
pins = "import sys;sys.path.insert(0,'code');from common import *;print(digest(code_pins()))"
try:
    roots = {}
    for part in 'ABCH':
        roots[part] = fresh('freeze_forge_'+part); freeze(roots[part], part)
    m.write_bytes(original + b'\n# reviewer probe: bar logic edited after freeze\n')
    new = subprocess.run([sys.executable, '-B', '-c', pins], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    for part, root in roots.items():
        f = directory(root, part)/'FREEZE.json'; d = json.loads(f.read_text()); d['code_sha256'] = new; f.write_text(json.dumps(d))
        before = tree(root)
        record('planted_FREEZE_after_code_edit_'+part, part, 'parts/'+part+'/FREEZE.json', root, before,
               run(root, "import process_guard as G;G.require_score(E.OUT,'%s');print('H_GUARD_PASSED');%s" % (part, CALL[part] if part != 'H' else 'E.heldout_once()')))
    root = roots['A']; b = directory(root, 'A')/'BARS.json'; f = directory(root, 'A')/'FREEZE.json'
    bd = json.loads(b.read_text()); bd['code_sha256'] = new; b.write_text(json.dumps(bd))
    d = json.loads(f.read_text()); d['bars_sha256'] = hashlib.sha256(b.read_bytes()).hexdigest(); f.write_text(json.dumps(d))
    before = tree(root)
    record('two_file_forge_BARS_and_FREEZE_A', 'A', 'parts/A/BARS.json+FREEZE.json', root, before,
           run(root, "import process_guard as G;G.require_score(E.OUT,'A');print('H_GUARD_PASSED')"), 'info')
finally:
    m.write_bytes(original)
assert m.read_bytes() == original

# Duplicate (row_id, arm) rows.
from evaluate_v2 import gains_once
dup = a_rows + [dict(row_id=i, room=r, split='train', arm=E.arm(64, 64, 'today'), score=50.) for i, r in pop['row_rooms'].items()]
try: gains_once(dup + [dict(dup[-1], score=100.)]); RES.append(dict(attempt='duplicate_rows_appended', ok=False))
except RuntimeError as e: RES.append(dict(attempt='duplicate_rows_appended', ok='REFUSE: duplicate' in str(e), last_error=str(e)))
print(json.dumps(RES[-1]), flush=True)

# 2. New planted-file attacks: nested, hidden, renamed, malformed, symlinks.
attempt('A_nested_deep', 'A', 'parts/A/x/y/z.json', one)
attempt('A_hidden_file', 'A', 'parts/A/.keep', '')
attempt('A_renamed_per_item_in_part_dir', 'A', 'parts/A/PER_ITEM_A_train.jsonl.bak', one)
attempt('A_legacy_top_per_item', 'A', 'PER_ITEM_A_train.jsonl', one)
attempt('A_pose_report', 'A', 'A_POSE.json', rows)
attempt('A_DISTANCE_not_json', 'A', 'A_DISTANCE.txt', 'not json')
attempt('A_DISTANCE_json_list', 'A', 'A_DISTANCE.txt', '[1,2]')
attempt('B_nested_per_item', 'B', 'parts/B/old/PER_ITEM_B_train.jsonl', one)
attempt('C_nested_per_item', 'C', 'parts/C/x/PER_ITEM_C_devs1.jsonl', one)
attempt('H_part_dir_file', 'H', 'parts/H/PER_ITEM_H_heldout.jsonl', one)
attempt('H_nested_freeze', 'H', 'parts/H/old/FREEZE.json', one)
attempt('A_symlink_per_item_dangling', 'A', 'parts/A/PER_ITEM_A_train.jsonl', ('symlink', lambda r: str(r/'nowhere.jsonl')))
def target_file(r):
    t = r/'elsewhere.jsonl'; t.write_text(one); return str(t)
attempt('A_symlink_per_item_to_file', 'A', 'parts/A/PER_ITEM_A_train.jsonl', ('symlink', target_file))
def report_file(r):
    t = r/'elsewhere_report.json'; t.write_text(rows); return str(t)
attempt('A_symlink_report_to_scored_file', 'A', 'A_DISTANCE.txt', ('symlink', report_file))
def target_dir(r):
    t = r/'elsewhere_dir'; t.mkdir(); (t/'PER_ITEM_A_train.jsonl').write_text(one); return str(t)
attempt('A_symlink_dir_with_per_item', 'A', 'parts/A/old', ('symlink', target_dir), expect='info')
attempt('A_renamed_top_report_bak', 'A', 'A_DISTANCE.txt.bak', rows, expect='info')
attempt('A_depth_report_with_rows', 'A', 'A_DEPTH.json', rows, expect='info')
attempt('B_gains_once_planted', 'B', 'B_GAINS_ONCE.txt', json.dumps(dict(status='OK', gains=dict(added_frame_gain=dict(point=10., low=10.)))), expect='info')

# 3. DECISION.json: planted bars for another part before A, and a frozen train decision before B.
fake_b = dict(views_pay=dict(status='OK', point=9., low=5.), added_frame_gain=dict(status='OK', point=9., low=5., verdict='PASS'))
root = fresh('A_DECISION_planted_B'); freeze(root, 'A')
(root/'DECISION.json').write_text(json.dumps(dict(bars=dict(B=fake_b), complete=dict(B=True))))
before = tree(root)
record('A_DECISION_planted_B_bars', 'A', 'DECISION.json', root, before, run(root, CALL['A']),
       decision_after=json.loads((root/'DECISION.json').read_text()).get('bars', {}).get('B'))
r = run(root, "E.update('A',{},True);import json;print(json.dumps(json.loads((E.OUT/'DECISION.json').read_text())['train_complete']))")
RES[-1]['update_A_complete_sets_train_complete'] = r.stdout.strip()
print(json.dumps(RES[-1]), flush=True)
root = fresh('B_DECISION_frozen'); freeze(root, 'A'); freeze(root, 'B')
with patch.object(V, 'OUT', root): V.items_file(a_rows, 'A', 'train')
(root/'A_DISTANCE.txt').write_text(json.dumps(dict(status='OK', rows=a_rows)))
(root/'DECISION.json').write_text(json.dumps(dict(bars=dict(A={}, B=fake_b), complete=dict(A=True, B=True), train_complete=True)))
before = tree(root)
record('B_DECISION_train_complete_planted', 'B', 'DECISION.json', root, before, run(root, CALL['B']))
r = run(root, CALL['B'])
RES[-1]['second_B_attempt'] = dict(returncode=r.returncode, last_error=(r.stderr.strip().splitlines() or [''])[-1][:200])
print(json.dumps(RES[-1]), flush=True)

# 4. H frozen only after A's model output exists (parts/H absent at run_H time): freeze(H) should refuse.
root = fresh('H_late_freeze'); freeze(root, 'A')
cap = root/'captures/A/0123456789abcdef'; cap.mkdir(parents=True); (cap/'tower.npz').write_bytes(b'model output')
before = tree(root)
record('H_freeze_after_A_model_output', 'H', 'captures/A/<cap>/tower.npz (parts/H absent)', root, before,
       run(root, "import process_guard as G;G.freeze(E.OUT,'H');print('H_FROZE')"))

# 5. Realistic A rows round-trip through items_file and emit, then a_train_rows (no false refusal on real data).
from replay import price, load_selector
from evaluate import geometry, stored_tower, scored
from policy import captures
root = fresh('A_rows_roundtrip'); freeze(root, 'A')
head = load_selector(); lab = E.labels('train'); real = []
for c in captures('train')[:4]:
    own = npz(capdir(c, '/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz')
    g, _ = geometry(stored_tower(c), own)
    cache = read_json(capdir(c, '/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
    real += scored(price(c, g, cache, 32, head=head), E.arm(32, 32, 'today'), lab)
    real += scored(price(c, g, gt=npz(c['gt']['path'])), E.arm(32, 32, 'GTmask'), lab)
with patch.object(V, 'OUT', root), patch.object(E, 'OUT', root):
    V.items_file(real, 'A', 'train'); E.emit('A_DISTANCE.txt', real, status='OK', bars={})
    try: got = E.a_train_rows(); rt = dict(ok=got == json.loads(json.dumps(clean(real))), returned_rows=len(got))
    except Exception as e: rt = dict(ok=False, error=repr(e)[:300])
RES.append(dict(attempt='A_rows_roundtrip_real_price_rows', priced_rows=len(real), keys=sorted({k for r in real for k in r}),
                row_has_input_sha256=any('input_sha256' in r for r in real), **rt))
print(json.dumps(RES[-1]), flush=True)
OUTFILE.write_text(json.dumps(RES, indent=1))
