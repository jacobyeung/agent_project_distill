"""Stage 2, one process per rank: the sealed CPU first batch for one rank, with stage 1's prepared state.
Usage: s2.py KIT RANK|final MEMORY_GIB. RANK: admit(prepare_only=True) (reuses stage 1's phases and returns its data receipt),
then the sealed run.first_batch_check(cfg, [RANK], ..., device cpu, progress_dir <admission dir>/first_batch_progress, rank_limit=1)
exactly as admit(prepare_only=False) calls it, so the rank journal is the one admit reads. final: admit(prepare_only=False)
once every rank is journalled (no model load; writes the admission receipt)."""
import hashlib, json, os, sys
from pathlib import Path
root, which, mem = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]); sys.path.insert(0, str(root / 'b'))
from v import tree, pin
from i import authorize
from d import contract
auth, cfg0 = authorize(root, 'p', '0')
cur = json.loads((root / 'k/0.json').read_text())
tree({'path': cur['record']['file'], 'sha256': cur['record']['sha256']}, os.environ['TRAINER'], cur['commit'])
sys.path.insert(0, os.environ['TRAINER'])
launch = json.loads((root / 'k/launch.json').read_text())
value = contract(launch, cfg0); dest = Path(value['directory']); config_pin = pin(root / launch['config']['file'])
from student_pilot.s1_admission import admit
if which == 'final':
    admit(config_pin, dest, value['frame_roots'], threads=16, memory_gib=mem)
    raise SystemExit(0)
rank = int(which); assert 0 <= rank < 4
receipt = admit(config_pin, dest, value['frame_roots'], threads=16, memory_gib=mem, prepare_only=True)
p = Path(receipt['config']['path']); b = p.read_bytes()
if hashlib.sha256(b).hexdigest() != receipt['config']['sha256']: raise ValueError('Prepared configuration differs from its pin')
cfg = json.loads(b)
from student_pilot import carrier_c1_run as run
out = dest / ('attempt_r%d_%s' % (rank, os.environ.get('SLURM_JOB_ID', 'local'))); out.mkdir()
run.first_batch_check(cfg, [rank], out / 'first_batch_report.json', steps=1, device='cpu',
                      progress_dir=dest / 'first_batch_progress', rank_limit=1)
