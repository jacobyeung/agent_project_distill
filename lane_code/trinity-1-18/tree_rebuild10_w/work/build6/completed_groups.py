"""Record completed diagnostic groups without treating live tests as passes."""
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = L / 'work/build6'
rows = []
for variant in ('tree', 'base'):
    for group in ('generator', 'legacy', 'r2'):
        path = B / 'proofs' / ('suite_' + variant) / group / 'results.json'
        if not path.exists():
            continue
        value = json.loads(path.read_text())
        sizes = json.loads((path.parent/'temporary_sizes.json').read_text())
        peak = max((max(row['before_bytes'], row['after_bytes']) for row in sizes), default=0)
        rows.append(dict(variant=variant, group=group, run=value['tests'],
                         passed=len(value['passed']), errors=len(value['errors']),
                         failures=len(value['failures']), skips=len(value['skips']),
                         complete=value['complete'], temporary_peak_bytes=peak,
                         temporary_source=str((path.parent/'temporary_sizes.json').relative_to(L)),
                         source=str(path.relative_to(L))))
(B / 'GROUP_COUNTS.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows))
lines = ['# Build 6 status', '',
         'The first packaged diagnostic is running. The working tree contains additional repairs '
         'that still require focused and final packaged verification. The current delivery record '
         'describes the diagnostic snapshot, not the final source.', '',
         '| Completed group | Run | Passed | Error / failure events | Source |',
         '|---|---:|---:|---:|---|']
lines.extend(f"| {r['variant']} / {r['group']} | {r['run']} | {r['passed']} | "
             f"{r['errors']} / {r['failures']} | `{r['source']}` |" for r in rows if r['complete'])
lines.extend(['', 'The exact contract hashes and unchanged level-basis functions pass '
              '(`work/build6/INTEGRATION_CHECK.json`). Packet and packed-row receipts are in '
              '`work/build6/proofs/packet/results.json` and `work/build6/proofs/rows/PARITY.json`.', '',
              'Final coverage remains provisional. Legacy failures require matching causes in '
              'the untouched base; the entire R2/shared-grammar group must pass. Pending repairs '
              'and the remaining workflow are recorded in `work/build6/RESUME.md`. No launch is authorized.'])
(B / 'STATUS.md').write_text('\n'.join(lines) + '\n')
