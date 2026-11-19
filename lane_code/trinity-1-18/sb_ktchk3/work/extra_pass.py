"""sb_ktchk3: a legitimate A-then-B run in runner.py's freeze order, then one pass of planted DECISION, FREEZE and H files.
Runs inside a private mount namespace where work/plant4 (a copy of the extracted sb_ktfix4 tar) is bound over the kit path."""
import sys, os, json, subprocess, uuid, hashlib, shutil
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktfix2/code')
from common import *
from process_guard import freeze, directory
import numpy as np
OUTFILE = Path('/scratch/jjyeung/orch_n30/sb_ktchk3/work/extra_results.json')
RES = []
CALL = {'A': 'E.run_a()', 'B': 'E.run_b()'}
HEAD = ("import sys;sys.path.insert(0,'code');from pathlib import Path;import evaluate_v2 as E,evaluate as V,camera_pricing as C;"
        "E.OUT=V.OUT=C.OUT=Path(sys.argv[1]);")
FREEZE_CALL = "import process_guard as G;G.freeze(E.OUT,'%s');print('FROZE')"

def tree(root):
    out = {}
    for d, dirs, files in os.walk(root):
        for n in dirs + files:
            p = Path(d)/n; k = str(p.relative_to(root))
            if p.is_symlink(): out[k] = 'LINK:'+os.readlink(p)
            elif p.is_file(): out[k] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def fresh(name): return ROOT/'runtime'/('extra_'+name+'_'+uuid.uuid4().hex[:8])
def run(root, call): return subprocess.run([sys.executable, '-B', '-c', HEAD+call, str(root)], cwd=ROOT, capture_output=True, text=True, timeout=3000)
def last(r): return (r.stderr.strip().splitlines() or [''])[-1][:240]
def dec(root):
    p = root/'DECISION.json'
    return json.loads(p.read_text()) if p.is_file() else None

def record(name, root, before, r, expect='refuse', **extra):
    after = tree(root)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    ok = (r.returncode != 0 and not changed) if expect == 'refuse' else (r.returncode == 0) if expect == 'proceed' else None
    RES.append(dict(attempt=name, expect=expect, returncode=r.returncode, refused='REFUSE:' in r.stderr, last_error=last(r), written=changed, ok=ok, **extra))
    print(json.dumps(RES[-1]), flush=True)

def tower_rows(root, n=4):
    """Write A's 32-frame towers for n train captures the way runner.capture_pass does (savez_compressed)."""
    from policy import captures
    from evaluate import stored_tower
    done = []
    for c in captures('train')[:n]:
        dest = capdir(c, root/'captures/A'); dest.mkdir(parents=True)
        np.savez_compressed(dest/'tower.npz', **stored_tower(c)); done.append(c['canonical'])
    return done

def lines(p): return sum(1 for l in p.read_text().splitlines() if l.strip()) if p.is_file() else None

# 1. Legitimate A then B, freezing as runner.py:81-82 (A, then H) before A's model output, and B before B's.
root = fresh('legit_AB')
r = run(root, FREEZE_CALL % 'A' + ";G.freeze(E.OUT,'H')"); assert r.returncode == 0, r.stderr
caps = tower_rows(root)
before = tree(root); rA = run(root, CALL['A'])
record('legit_A_scores', root, before, rA, 'proceed', towers=caps, a_items=lines(directory(root, 'A')/'PER_ITEM_A_train.jsonl'),
       a_distance_rows=len(json.loads((root/'A_DISTANCE.txt').read_text())['rows']) if (root/'A_DISTANCE.txt').is_file() else None,
       decision_bars=sorted((dec(root) or {}).get('bars', {})), decision_complete=(dec(root) or {}).get('complete'))
r = run(root, FREEZE_CALL % 'B'); assert r.returncode == 0, r.stderr
before = tree(root); rB = run(root, CALL['B'])
d = dec(root) or {}
record('legit_B_scores_after_A', root, before, rB, 'proceed', b_items=lines(directory(root, 'B')/'PER_ITEM_B_train.jsonl'),
       decision_bars=sorted(d.get('bars', {})), decision_complete=d.get('complete'), train_complete=d.get('train_complete'),
       added_frame_gain=d.get('bars', {}).get('B', {}).get('added_frame_gain', {}).get('verdict'))
for part in 'AB':
    before = tree(root); record('legit_repeat_'+part+'_refuses', root, before, run(root, CALL[part]))
before = tree(root); record('legit_run_H_sh_refreeze_passes', root, before, run(root, FREEZE_CALL % 'H'), 'proceed')
legit = root

# 2. Planted DECISION.json files.
fake = dict(views_pay=dict(status='OK', point=9., low=5.), added_frame_gain=dict(status='OK', point=9., low=5., verdict='PASS'))
def plant_decision(name, part, content, expect='refuse', setup=None, link=False):
    root = fresh(name); freeze(root, 'A')
    if part == 'B': freeze(root, 'B')
    if setup: setup(root)
    p = root/'DECISION.json'
    if link:
        t = root/'elsewhere_decision.json'; t.write_text(json.dumps(content)); os.symlink(t, p)
    else: p.write_text(json.dumps(content))
    before = tree(root); r = run(root, CALL[part])
    record(name, root, before, r, expect, decision_after=dec(root))
def after_legit_A(root):
    shutil.copytree(legit/'parts/A', root/'parts/A', dirs_exist_ok=True)
    for n in ('A_DISTANCE.txt', 'A_POSE.json', 'A_DEPTH.json', 'A_SCALE.json'): shutil.copy2(legit/n, root/n)
    shutil.copytree(legit/'captures/A', root/'captures/A')
plant_decision('A_DECISION_complete_B_false_only', 'A', dict(complete=dict(B=False)))
plant_decision('A_DECISION_own_A_bars_preplanted', 'A', dict(bars=dict(A=fake), complete=dict(A=True)))
plant_decision('A_DECISION_train_complete_only', 'A', dict(train_complete=True))
plant_decision('A_DECISION_symlink_to_B_bars', 'A', dict(bars=dict(B=fake), complete=dict(B=True)), link=True)
plant_decision('A_DECISION_MISSING_status_with_B_bars', 'A', dict(status='MISSING', bars=dict(B=fake), complete=dict(B=True)), 'proceed')
RES[-1]['B_bars_survive'] = 'B' in (RES[-1]['decision_after'] or {}).get('bars', {})
plant_decision('B_DECISION_A_entry_without_A_run', 'B', dict(bars=dict(A={}), complete=dict(A=True)))
plant_decision('B_DECISION_after_A_adds_complete_B', 'B', dict(bars=dict(A={}), complete=dict(A=True, B=True)), setup=after_legit_A)
plant_decision('B_DECISION_after_A_forges_A_bars', 'B', dict(bars=dict(A=fake), complete=dict(A=True)), 'info', setup=after_legit_A)

# 3. Planted FREEZE.json files.
def plant_freeze(name, part, files, expect='refuse', setup=None):
    root = fresh(name)
    if setup: setup(root)
    for rel, src in files.items():
        p = root/rel; p.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, p)
    before = tree(root); record(name, root, before, run(root, FREEZE_CALL % part), expect)
plant_freeze('A_FREEZE_only_no_BARS', 'A', {'parts/A/FREEZE.json': legit/'parts/A/FREEZE.json'})
plant_freeze('B_pair_copied_from_A', 'B', {'parts/B/BARS.json': legit/'parts/A/BARS.json', 'parts/B/FREEZE.json': legit/'parts/A/FREEZE.json'})
plant_freeze('H_FREEZE_only_no_BARS', 'H', {'parts/H/FREEZE.json': legit/'parts/H/FREEZE.json'})

# 4. Planted H files: late freeze after B output, hidden and nested A output, symlinked output; replayed H pair.
def late_H(name, setup, expect='refuse'):
    root = fresh(name); setup(root); before = tree(root); record(name, root, before, run(root, FREEZE_CALL % 'H'), expect)
def put(rel, data=b'model output'):
    def f(root):
        p = root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    return f
late_H('H_late_after_B_output', put('captures/B/0123456789abcdef/candidates.json', b'{}'))
late_H('H_late_after_hidden_A_file', put('captures/A/.partial'))
late_H('H_late_after_nested_A_file', put('captures/A/x/y/tower.npz'))
def link_file(root):
    root.mkdir(parents=True); t = root/'elsewhere.npz'; t.write_bytes(b'model output'); d = root/'captures/A/0123456789abcdef'; d.mkdir(parents=True); os.symlink(t, d/'tower.npz')
late_H('H_late_after_symlinked_A_file', link_file)
def link_units(root):
    t = root/'elsewhere_caps'; (t/'0123456789abcdef').mkdir(parents=True); (t/'0123456789abcdef/tower.npz').write_bytes(b'model output')
    (root/'captures').mkdir(); os.symlink(t, root/'captures/A')
late_H('H_late_captures_A_is_dir_symlink', link_units)
def link_subdir(root):
    t = root/'elsewhere_cap'; t.mkdir(parents=True); (t/'tower.npz').write_bytes(b'model output')
    (root/'captures/A').mkdir(parents=True); os.symlink(t, root/'captures/A/0123456789abcdef')
late_H('H_late_capture_subdir_symlink', link_subdir, 'info')
def replay_H(root):
    put('captures/A/0123456789abcdef/tower.npz')(root); shutil.copytree(legit/'parts/H', root/'parts/H')
late_H('H_pair_replayed_after_A_output', replay_H, 'info')
RES[-1]['note'] = 'BARS.json for H is protocol(H) plus input hashes, a function of the pinned code only'
OUTFILE.write_text(json.dumps(RES, indent=1))
print('SUMMARY', json.dumps({x['attempt']: x['ok'] for x in RES}))
