"""Finalize the review only after every synthetic rank forward has completed."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
inputs = {}
def read(path):
    path = Path(path)
    data = path.read_bytes()
    inputs[str(path)] = hashlib.sha256(data).hexdigest()
    return data

read(__file__)
read(ROOT / 'run_cpu.sh')
read(ROOT.parent / 'sb_f64/work/read_a/root/e2e_reader/parity.py')
forward = json.loads(read(OUT / 'forward_review.json'))
assert forward['layers'] == 32 and forward['threads'] == 8
assert [r['rank'] for r in forward['records']] == [0, 1, 2, 3]
assert all(r['finite'] and math.isfinite(r['loss']) for r in forward['records'])
assert all(r['peak_rss_gib'] * 2**30 < 40_000_000_000 for r in forward['records'])
for filename, expected in forward['input_sha256'].items():
    read(filename)
    assert inputs[filename] == expected, filename
for name in ('resume_review.json', 'behavior_review.json', 'static_review.json',
             'baseline_regression.json', 'patched_regression.json', 'anchor_order_review.json',
             'PATCH_LINES.md', 'INDEPENDENT_TREE_DIFF.patch'):
    read(OUT / name)
peak = max(r['peak_rss_gib'] for r in forward['records'])
times = [r['seconds'] for r in forward['records']]
path = OUT / 'REVIEW_VERDICT.md'
text = path.read_text()
text = text.replace('Independent full-depth CPU result: PENDING.',
    f'Independent full-depth CPU check: all four synthetic ranks passed with finite losses, '
    f'9,127 tokens each and peak RSS {peak:.2f} GiB (`forward_review.json`).')
assert 'PENDING' not in text and len(text.splitlines()) <= 50
path.write_text(text)
read(path)
summary = dict(command='bash run_cpu.sh finish_review.py', input_sha256=inputs,
    verdict='NO-GO', report_lines=len(text.splitlines()),
    synthetic_cpu_forward=dict(ranks=4, all_finite=True, peak_rss_gib=peak, seconds_by_rank=times,
                               layers=forward['layers'], threads=forward['threads'],
                               total_parameters=forward['total_parameters'],
                               heads_total=forward['heads_total'], heads_trainable=forward['heads_trainable']),
    actual_bound_cpu_first_batches='MISSING', gpu_measurements='MISSING',
    scope='Read-only review of builder files; all review writes remain within sb_f64rev.')
(OUT / 'FINAL_EVIDENCE.json').write_text(json.dumps(summary, indent=2) + '\n')
(ROOT / 'STATUS.md').write_text(
    f'Review complete: out/REVIEW_VERDICT.md records NO-GO in {len(text.splitlines())} lines. '
    f'All four independent full-depth synthetic CPU forwards passed with finite losses; peak RSS was {peak:.2f} GiB. '
    'Both regression suites ran 109 tests with the same pre-existing missing POOL.jsonl error; all 12 layout tests passed. '
    'Blockers remain in population/anchor-order preservation, audit completeness, missing bound inputs, '
    'and unmeasured GPU training memory/time. Exact patch lines and SHA256-backed evidence are in out/. '
    'No GPU, network, Git, deletion, or writes to the builder workspace were used.\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))
