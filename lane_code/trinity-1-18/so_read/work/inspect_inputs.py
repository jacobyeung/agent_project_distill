import json
from pathlib import Path
base = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3')
for name in ('A4', 'B5'):
    root = base/name
    print('\nPACKAGE', name)
    for path in sorted((root/'ret/metadata/reads/0/metadata/journals').glob('*/*/items.jsonl')):
        rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
        first = rows[0]
        print('JOURNAL', path.relative_to(root), 'N', len(rows), 'type', first.get('type'))
        print('ROW KEYS', list(first), 'OUTPUT KEYS', list(first.get('output', {})))
        print('FIRST', json.dumps(first)[:3500])
        print('TIMINGS', (path.parent/'timings.jsonl').read_text()[:2500])
        env = json.loads((path.parent/'environment.json').read_text())
        print('ENV', {k:v for k,v in env.items() if k != 'binding'})
        print('BINDING', {k:v for k,v in env['binding'].items() if k not in ('ids',)})
    for name2 in ('STEPS.jsonl', 'SUMMARY.json', 'metadata/projection.json'):
        p = root/'ret/metadata/reads/0'/name2
        if p.exists():print(name2,p.read_text()[:2000])
