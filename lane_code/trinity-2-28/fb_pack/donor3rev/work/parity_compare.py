"""Compare field-absent parity outputs: base vs new, live_base vs live, and each against donor2rev's runs."""
import json
from pathlib import Path

W = Path(__file__).resolve().parent
D2 = Path('/scratch/jjyeung/orch_n30/fb_pack/donor2rev/work')
P = {n: json.loads((W / f'PARITY_{n}.json').read_text()) for n in ('base', 'new', 'live_base', 'live')}
lines, ok = [], True
for a, b in (('base', 'new'), ('live_base', 'live')):
    same = [k for k in P[a] if P[a][k] == P[b].get(k)]
    diff = sorted(set(P[a]) ^ set(P[b]) | {k for k in P[a] if P[a][k] != P[b].get(k)})
    ok &= not diff
    lines.append(f'{a} vs {b}: {len(same)}/{len(P[a])} fields equal; differ={diff}')
for n in P:
    prev = json.loads((D2 / f'PARITY_{n}.json').read_text())
    eq = prev == P[n]
    lines.append(f'{n} equals donor2rev {n}: {eq}')
lines.append('PASS' if ok else 'FAIL')
(W / 'PARITY_COMPARE.txt').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
