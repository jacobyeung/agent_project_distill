"""Reviewer probe: try to defeat the bars-first guard with one planted file per part.
Copied unchanged from sb_ktchk except this output path; sb_ktchk3 binds work/plant4 over the kit path."""
import sys, json, subprocess, uuid, hashlib
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_ktfix2/code')
from common import *
from process_guard import freeze, require_score, directory
RES = []
CALL = {'A': 'E.run_a()', 'B': 'E.run_b()', 'C': 'E.run_c()',
        'H': "import process_guard as G;G.require_score(E.OUT,'H');print('H_GUARD_PASSED');E.heldout_once()"}

def tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

def attempt(name, part, rel, content, call=None):
    root = ROOT/'runtime'/('plant_'+name+'_'+uuid.uuid4().hex[:8])
    freeze(root, part)
    p = root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    before = tree(root)
    script = ("import sys;sys.path.insert(0,'code');from pathlib import Path;import evaluate_v2 as E,evaluate as V,camera_pricing as C;"
              "E.OUT=V.OUT=C.OUT=Path(sys.argv[1]);" + (call or CALL[part]))
    r = subprocess.run([sys.executable, '-B', '-c', script, str(root)], cwd=ROOT, capture_output=True, text=True, timeout=3000)
    after = tree(root)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    RES.append(dict(attempt=name, part=part, planted=rel, returncode=r.returncode, refused='REFUSE:' in r.stderr,
                    guard_passed='H_GUARD_PASSED' in r.stdout, last_error=(r.stderr.strip().splitlines() or [''])[-1][:300],
                    planted_overwritten=before.get(rel) != after.get(rel), written=changed))
    print(json.dumps(RES[-1]), flush=True)

rows = json.dumps(dict(status='OK', rows=[dict(row_id='planted', room='r', split='train', arm='C32_V32_today', score=99.0)]))
attempt('A_report', 'A', 'A_DISTANCE.txt', rows)
attempt('A_subdir_bars', 'A', 'parts/A/old/BARS.json', '{"row_id":"planted","score":99}\n')
attempt('A_control_per_item', 'A', 'parts/A/PER_ITEM_A_train.jsonl', '{"row_id":"planted","score":99}\n')
attempt('B_report', 'B', 'B_LADDER_TRAIN.txt', rows)
attempt('C_report', 'C', 'C_CAMERA.txt', json.dumps(dict(status='OK', rows=[dict(id='planted', arm='G32', score=99.0)])))
attempt('H_report', 'H', 'HELDOUT_once.txt', json.dumps(dict(status='OK', results=dict(A=dict(rows=[dict(row_id='planted', score=99.0)])))))
attempt('H_control_legacy', 'H', 'PER_ITEM_A_heldout.jsonl', '{"row_id":"planted","score":99}\n')

# B trusts A_DISTANCE.txt: the same B rows give opposite added_frame_gain verdicts under two planted A files.
from exclusions import population
from evaluate_v2 import gains_once, arm
pop = population(); b_rows = [dict(row_id=i, room=r, split='train', arm=arm(64, 64, 'today'), score=50.) for i, r in pop['row_rooms'].items()]
flip = {}
for a_score in (40., 60.):
    a_rows = [dict(row_id=i, room=r, split='train', arm=arm(32, 32, 'today'), score=a_score) for i, r in pop['row_rooms'].items()]
    g = gains_once(a_rows + b_rows)['gains']['added_frame_gain']; flip[str(a_score)] = dict(point=g['point'], low=g['low'], verdict='PASS' if g['low'] > 0 else 'FAIL')
RES.append(dict(attempt='B_reads_planted_A_DISTANCE', note='evaluate_v2.run_b reads OUT/A_DISTANCE.txt rows with no hash check', verdicts=flip))
print(json.dumps(RES[-1]), flush=True)

# One planted FREEZE.json hides a scoring-code change made after the freeze.
root = ROOT/'runtime'/('plant_A_freeze_'+uuid.uuid4().hex[:8]); freeze(root, 'A')
m = ROOT/'code/metrics.py'; original = m.read_bytes()
try:
    m.write_bytes(original + b'\n# reviewer probe: bar logic edited after freeze\n')
    script = "import sys;sys.path.insert(0,'code');import process_guard as G;from pathlib import Path;print(G.require_score(Path(sys.argv[1]),'A')['code_sha256'])"
    r1 = subprocess.run([sys.executable, '-B', '-c', script, str(root)], cwd=ROOT, capture_output=True, text=True)
    new = subprocess.run([sys.executable, '-B', '-c', "import sys;sys.path.insert(0,'code');from common import *;print(digest(code_pins()))"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    f = directory(root, 'A')/'FREEZE.json'; d = json.loads(f.read_text()); d['code_sha256'] = new; f.write_text(json.dumps(d))
    r2 = subprocess.run([sys.executable, '-B', '-c', script, str(root)], cwd=ROOT, capture_output=True, text=True)
    RES.append(dict(attempt='A_planted_FREEZE_after_code_edit', before_plant=dict(returncode=r1.returncode, refused='REFUSE:' in r1.stderr, last_error=(r1.stderr.strip().splitlines() or [''])[-1][:200]),
                    after_plant=dict(returncode=r2.returncode, refused='REFUSE:' in r2.stderr, stdout=r2.stdout.strip()[:80])))
finally:
    m.write_bytes(original)
print(json.dumps(RES[-1]), flush=True)
Path('/scratch/jjyeung/orch_n30/sb_ktchk3/work/plant_results.json').write_text(json.dumps(RES, indent=1))
