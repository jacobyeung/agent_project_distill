"""Run a disjoint future capture range through the unchanged K1-X CLI."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = '/scratch/jjyeung/envs/p1cpu/bin/python'
start, end, workers = map(int, sys.argv[1:])
assert 1 <= workers <= 8
assert json.loads((ROOT / 'out/PARITY.json').read_text())['passed']
manifest = json.loads(Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json').read_text())
rowsets = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS')
ids = set((rowsets / 'K1_HELDOUT_216.txt').read_text().splitlines())
ids.update((rowsets / 'K1_TRAIN_1037.txt').read_text().splitlines())
captures = [c['canonical'] for c in manifest['captures'] if any(r['id'] in ids for r in c['rows'])]
chosen = captures[start:end]
assert chosen
processes = []
for worker in range(workers):
    chunk = chosen[worker::workers]
    if not chunk:
        continue
    log = ROOT / f'out/BATCH_{start}_{end}_{worker}.log'
    args = ['nice', '-n', '10', PYTHON, '-I', '-s', '-B', str(ROOT / 'k1x.py'),
            'run', '--heavy-io-approved', '--phase', 'factorial']
    for capture in chunk:
        args.extend(['--capture', capture])
    with log.open('w') as stream:
        process = subprocess.Popen(args, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    processes.append((worker, process, log, chunk))
receipt = []
for worker, process, log, chunk in processes:
    code = process.wait()
    receipt.append(dict(worker=worker, exit_code=code, log=str(log), captures=chunk))
    print(f'worker {worker}: exit {code}, {len(chunk)} captures', flush=True)
(ROOT / f'out/BATCH_{start}_{end}.json').write_text(json.dumps(receipt, indent=2) + '\n')
sys.exit(int(any(r['exit_code'] != 0 for r in receipt)))
