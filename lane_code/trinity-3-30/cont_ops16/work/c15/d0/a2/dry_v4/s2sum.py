"""Stage 2 summary (read-only): per rank, rows in the batch by family, loss terms and finiteness, wall time and peak memory.
Usage: s2sum.py INPUTS_DIR (the run's admission directory). Families come from the prepared SQLite rows (qid -> category, pool)."""
import json, sqlite3, sys, collections
from pathlib import Path
d = Path(sys.argv[1]); fam = {}
SEALED = {'w1g', 'r1g', None}
for f in sorted(d.rglob('*.sqlite')):
    try:
        c = sqlite3.connect('file:' + str(f) + '?mode=ro', uri=True)
        if 'row' not in [r[1] for r in c.execute('pragma table_info("rows")')]: continue
        for (s,) in c.execute('select row from rows'):
            try: r = json.loads(s)
            except ValueError: continue
            if isinstance(r, dict) and r.get('qid') is not None:
                p = r.get('pool'); fam.setdefault(str(r['qid']), str(r.get('category')) + '|' + ('s' if p in SEALED else 'r' if 'route' in str(p) else 'n'))
    except sqlite3.Error: continue
reports = sorted(d.glob('attempt_*/first_batch_report.json'), key=lambda p: p.stat().st_mtime)
records = {}
for p in reports:
    for r in json.loads(p.read_text()).get('records', []): records[(r['rank'], r['step'], r['microstep'])] = r
done = {}
for p in sorted((d / 'first_batch_progress').glob('rank_*.complete.json')):
    m = json.loads(p.read_text()); v = json.loads((p.parent / Path(m['payload']['path']).name).read_text())  # payload pin is a namespace path
    done[int(p.name[5:8])] = v['resources']
    for r in v['records']: records[(r['rank'], r['step'], r['microstep'])] = r
out = {}
for rank in range(4):
    rows = [r for k, r in sorted(records.items()) if k[0] == rank]
    by = collections.Counter(); comp = collections.defaultdict(list); nonfinite = []
    for r in rows:
        key = r['stream'] + ':' + fam.get(str(r.get('qid')), '-')
        by[key] += 1
        for k, v in (r.get('components') or {}).items(): comp[k].append(v)
        if r.get('finite') is not True: nonfinite.append(dict(step=r['step'], microstep=r['microstep'], stream=r['stream'], qid=r.get('qid'), error=r.get('error')))
    out[str(rank)] = dict(status='PASS' if rank in done else ('FAILED' if nonfinite else 'not measured'), rows_done=len(rows),
        rows_by_family=dict(sorted(by.items())), nonfinite=nonfinite,
        loss=dict(min=min((r['loss'] for r in rows if 'loss' in r), default=None), max=max((r['loss'] for r in rows if 'loss' in r), default=None)),
        components={k: dict(n=len(v), min=min(v), max=max(v), mean=sum(v) / len(v)) for k, v in sorted(comp.items())},
        row_seconds=round(sum(r.get('seconds', 0) for r in rows), 1), rank_resources=done.get(rank))
out['receipt_present'] = (d / 'receipt.json').exists()
print(json.dumps(out, indent=1, sort_keys=True))
