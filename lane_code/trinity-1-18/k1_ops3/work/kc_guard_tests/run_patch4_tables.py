"""Run the authorized full tables-only validations sequentially with timings."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'kc_guard/k1_build/work/kit_k1a/work'
for name, count, gt, extra in (
    ('primary296', 296, 'GT_SET_PRIMARY_296.json', []),
    ('sensitivity300', 300, 'GT_SET_SENSITIVITY_300.json', ['--sensitivity']),
):
    out = ROOT / ('patch4_' + name) / 'tables'
    command = [sys.executable, '-I', '-s', '-B', str(WORK / 'k1_pipeline.py'), 'tables',
               '--manifest', str(ROOT.parent / 'manifest_v2/a40fbc19.json'),
               '--cache', '/scratch/jjyeung/k1/run_convert_2',
               '--gt-set', str(ROOT.parent / 'gt_sets' / gt), '--out', str(out), *extra]
    print('Starting ' + name, flush=True)
    start = time.monotonic()
    with (ROOT / ('patch4_' + name + '.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.monotonic() - start
    record = dict(command=command, exit_code=result.returncode, runtime_seconds=elapsed)
    if result.returncode == 0:
        receipt = json.loads((out / 'TABLE_RECEIPT.json').read_text())
        assert len(receipt['gt_canvas_map']) == count
        assert receipt['json_bound_bytes'] == 64 * 1024 * 1024
        record.update(rows={n: sum(1 for _ in (out / n).open()) for n in ('candidates.jsonl', 'pairs.jsonl')},
                      gt_canvas_map_counts=receipt['gt_canvas_map_counts'],
                      geometry_refused=receipt['geometry_refused'],
                      json_bound_bytes=receipt['json_bound_bytes'],
                      captures=len(receipt['gt_canvas_map']), receipt=str(out / 'TABLE_RECEIPT.json'))
    (ROOT / ('patch4_' + name + '_summary.json')).write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
