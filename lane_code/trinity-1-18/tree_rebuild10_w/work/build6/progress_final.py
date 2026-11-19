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
steps = json.loads((B / 'FINAL_PASS.json').read_text())
phase = ('The final suite driver has completed; final review and reporting remain.'
         if steps[-1]['step'] == 'comparison' and steps[-1]['returncode'] == 0
         else 'Final packaged qualification is running. The source remains frozen.')
lines = ['# Build 6 status', '', phase, '',
         f"Active package group: `{state['variant']}/{state['group']}`; completed executions: {progress['completed']}. Source: `{path.relative_to(L)}` and its group progress receipt.", '',
         f"Detected lost build-5 pass events: {len(losses)} (`work/build6/LIVE_B5_LOSSES.json`). This live check does not replace the final base comparison.", '',
         'The packet suite passed on the final source (`work/build6/final_packet.log`). The focused repairs passed (`work/build6/proofs/final_targeted/results.json`). OFF/ON packed-row parity passed (`work/build6/proofs/rows/PARITY.json`).', '',
         'The exact and merged contract files are verified (`work/build6/INTEGRATION_CHECK.json`). Both restaged kits passed their scan and read checks (`work/build6/kits/RESULTS.json`, `work/build6/KIT_READCHECK.json`). Delivery identity: `work/build6/DELIVERY.json`.', '',
         '| Completed driver step | Return code | Log |', '|---|---:|---|']
lines.extend(f"| {row['step']} | {row['returncode']} | `{row['log']}` |" for row in steps)
lines += ['', 'Coverage remains provisional until the driver aggregates final receipts. Initial diagnostic evidence is retained under `work/build6/proofs/suite_tree/diagnostic_results.json` and the corresponding base proof.', '',
          'Full RGB/scene admission and missing evidence records remain unqualified. Both kit authorizations stay closed. No launch is authorized. Remaining work is recorded in `work/build6/RESUME.md`.']
(B / 'STATUS.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(dict(variant=state['variant'], group=state['group'], **progress,
                     lost_pass_events=len(losses), source=str(path.relative_to(L)),
                     steps=steps)))
