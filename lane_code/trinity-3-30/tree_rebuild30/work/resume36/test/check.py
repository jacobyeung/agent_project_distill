"""Checks of the resume test; prints one line per check and writes <T>/result.json.
usage: check.py <T> <world>"""
import json, math, sys
from pathlib import Path
T, world = Path(sys.argv[1]), int(sys.argv[2])
rd = lambda p: json.loads(Path(p).read_text())
A = [rd(T / f'log/A_rank{r}.json') for r in range(world)]
B = [rd(T / f'log/B_rank{r}.json') for r in range(world)]
last = lambda p: (Path(p).read_text().strip().splitlines() or [''])[-1]
rs = {v: json.loads(last(T / f'log/rs_{v}.log') or '{}') for v in ('B', 'Bx', 'Bc')}
checks = []
def c(name, ok, detail=''):
    checks.append(dict(check=name, ok=bool(ok), detail=detail)); print(('PASS ' if ok else 'FAIL ') + name + (' | ' + str(detail) if detail else ''))
c('A all ranks PASS', all(a['status'] == 'PASS' for a in A), [a.get('error') for a in A if a['status'] != 'PASS'])
c('A stopped at step 2, newest state step 2', A[0]['report']['last_step'] == 2 and '_000002_' not in '' and 'checkpoint_000002_' in A[0]['newest']['path'], A[0]['newest']['path'])
c('A control reached step 3', A[0]['control']['last_step'] == 3)
c('rs B PASS (binding equal, parts/archive/marker digests, latest_resume == staged state)', rs['B'].get('status') == 'PASS', rs['B'])
c('rs Bx REFUSE RS_BINDING_DIFFERS on preparation only', rs['Bx'].get('code') == 'RS_BINDING_DIFFERS' and rs['Bx'].get('fields') == ['preparation'], rs['Bx'].get('fields'))
c('rs Bc REFUSE RS_PART_DIGEST', rs['Bc'].get('code') == 'RS_PART_DIGEST', rs['Bc'].get('code'))
c('B all ranks PASS', all(b['status'] == 'PASS' for b in B), [b.get('error') for b in B if b['status'] != 'PASS'])
b0 = B[0]
c('B bound == A bound (new run folder, same namespace)', all(b['bound'] == a['bound'] for a, b in zip(A, B)))
c('tree refuses latest_resume for a foreign preparation pin', b0.get('refuse_latest_foreign') == 'No complete C1 resume state', b0.get('refuse_latest_foreign'))
c('tree refuses restore for a foreign preparation pin (every rank)', all(b.get('refuse_restore_foreign') == 'C1 resume binding differs' for b in B), b0.get('refuse_restore_foreign'))
c('loaded step 2 on every rank', all(b.get('loaded_step') == 2 for b in B))
c('loaded weights == A step-2 weights, bitwise, every rank', all(b['digest_loaded'] == a['digest_step2'] for a, b in zip(A, B)))
c('a fresh start over the restored state is refused', b0.get('refuse_fresh_start') == 'Complete C1 resume state exists; resume instead of starting fresh', b0.get('refuse_fresh_start'))
c('B trained exactly step 3', b0['report']['first_step'] == 3 and b0['report']['last_step'] == 3, b0['report'])
m = [r for r in b0.get('metrics', []) if r['step'] == 3]
finite = bool(m) and all(isinstance(v, (int, float)) and math.isfinite(v) for v in list((m[0]['stream_means'] or {}).values()) + list((m[0]['components'] or {}).values()))
c('step-3 losses finite', finite and bool(m[0]['stream_means']), m[0] if m else None)
c('save written: complete state step 3 is newest', b0.get('saved_step') == 3 and 'checkpoint_000003_' in b0['saved']['path'], b0.get('saved'))
c('export m3 written', bool(b0.get('export')), b0.get('export'))
c('persistence archived the new state and m3 (local receipts)', sum(n.endswith('.local.json') for n in b0.get('persist', [])) == 2, b0.get('persist'))
c('resumed step-3 weights == uninterrupted control step-3 weights, bitwise, every rank', all(b['digest_step3'] == a['control']['digest_step3'] for a, b in zip(A, B)))
pub = T / 'B/live_spool/state'
c('publisher receipt for the restored state copied (no re-archive, no re-send)', any(pub.glob('gcs_checkpoint_000002_*.done')), [p.name for p in pub.glob('*')])
out = dict(passed=sum(x['ok'] for x in checks), total=len(checks), checks=checks)
(T / 'result.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
print(f"{out['passed']}/{out['total']} checks pass")
