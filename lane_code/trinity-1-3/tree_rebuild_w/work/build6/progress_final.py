"""Read the active package group and current lost-pass events once."""
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = L / 'work/build6'
paths = [B / 'proofs' / ('suite_' + name) / 'progress.json' for name in ('tree', 'base')]
path = max(paths, key=lambda p: p.stat().st_mtime)
state = json.loads(path.read_text())
progress = json.loads((path.parent / state['group'] / 'progress.json').read_text())
prior = set(json.loads((L / 'work/build5/proofs/suite_tree/results.json').read_text())['passed'])
losses = []
for group in ('generator', 'legacy', 'r2'):
    root = B / 'proofs/suite_tree' / group
    for name in ('live_errors.json', 'live_failures.json'):
        for test, error in json.loads((root / name).read_text()):
            if test.split(' (', 1)[0] in prior:
                losses.append(dict(test=test, error=error))
(B / 'LIVE_B5_LOSSES.json').write_text(json.dumps(losses, indent=2) + '\n')
print(json.dumps(dict(variant=state['variant'], group=state['group'], **progress,
                     lost_pass_events=len(losses), source=str(path.relative_to(L)),
                     steps=json.loads((B / 'FINAL_PASS.json').read_text()))))
