"""Stage 2 summary (read-only): per rank, rows in the batch by family, loss terms and finiteness, wall time and peak memory.
Usage: s2sum.py DIR (the run's admission directory). Families are printed as fam.py codes (8-hex category code plus origin
letter), row keys and error messages only as 16-hex digests with the exception class name; no row text or metadata is printed."""
import hashlib, json, re, sqlite3, sys, collections
from pathlib import Path
SEALED = {'w1g', 'r1g', None}
h = lambda s: hashlib.sha256(str(s).encode()).hexdigest()[:16]
def code(d):
    p = d.get('pool')
    return hashlib.sha256(str(d.get('category')).encode()).hexdigest()[:8] + '|' + ('s' if p in SEALED else 'r' if 'route' in str(p) else 'n')
EXC = {'ValueError', 'RuntimeError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError', 'AssertionError', 'MemoryError',
       'OSError', 'FileNotFoundError', 'ZeroDivisionError', 'OverflowError', 'NotImplementedError', 'OutOfMemoryError', 'SystemExit'}
STREAMS = {'pose', 'vqa', 'pointing', 'routing', 'mdg'}
NAMES = STREAMS | {'depth', 'lm', 'text', 'heads', 'total', 'loss', 'aux', 'geometry', 'mask', 'box', 'point'}
RES = {'seconds', 'cpu_threads', 'peak_rss_kib', 'rows', 'tokens'}
def err(m):  # approved exception class name, else 'error', plus a digest of the whole message
    if m is None: return None
    t = str(m).partition(':')[0].rpartition('.')[2]
    return (t if t in EXC else 'error') + ' ' + h(m)
lab = lambda s, ok: s if s in ok else 'x' + h(s)  # approved label, else a digest
def hook(t, v, tb):  # a top-level failure prints only its approved class name and a digest, never its text
    print(json.dumps(dict(summary_failed=(t.__name__ if t.__name__ in EXC else 'error') + ' ' + h(v))))
    sys.exit(1)
sys.excepthook = hook
num = lambda v: v if isinstance(v, (int, float)) and not isinstance(v, bool) else None
d = Path(sys.argv[1]); fam = {}
for f in sorted(d.rglob('*.sqlite')):
    try:
        c = sqlite3.connect('file:' + str(f) + '?mode=ro', uri=True)
        if 'row' not in [r[1] for r in c.execute('pragma table_info("rows")')]: continue
        for (s,) in c.execute('select row from rows'):
            try: r = json.loads(s)
            except ValueError: continue
            if isinstance(r, dict) and r.get('qid') is not None: fam.setdefault(str(r['qid']), code(r))
    except sqlite3.Error: continue
records = {}
for p in sorted(d.glob('attempt_*/first_batch_report.json'), key=lambda p: p.stat().st_mtime):
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
        by[lab(r['stream'], STREAMS) + ':' + fam.get(str(r.get('qid')), '-')] += 1
        for k, v in (r.get('components') or {}).items():
            if num(v) is not None: comp[lab(k, NAMES)].append(v)
        if r.get('finite') is not True:
            nonfinite.append(dict(step=num(r.get('step')), microstep=num(r.get('microstep')), stream=lab(r.get('stream'), STREAMS), row=h(r.get('qid')), error=err(r.get('error'))))
    losses = [r['loss'] for r in rows if isinstance(r.get('loss'), (int, float))]
    out[str(rank)] = dict(status='PASS' if rank in done else ('FAILED' if nonfinite else 'not measured'), rows_done=len(rows),
        rows_by_family=dict(sorted(by.items())), nonfinite=nonfinite, loss=dict(min=min(losses, default=None), max=max(losses, default=None)),
        components={k: dict(n=len(v), min=min(v), max=max(v), mean=sum(v) / len(v)) for k, v in sorted(comp.items())},
        row_seconds=round(sum(num(r.get('seconds')) or 0 for r in rows), 1),
        rank_resources=None if done.get(rank) is None else {k: num(v) for k, v in done[rank].items() if k in RES})
out['receipt_present'] = (d / 'receipt.json').exists()
print(json.dumps(out, indent=1, sort_keys=True))
