#!/usr/bin/env python3
"""Report which name of the job folder the frame-audit records carry (ORCH ANSWER 1928Z item 4). Informational, never a verdict.
Usage: python3 -I spell.py DIR. Searches DIR recursively; for frames.json and request.json prints their roots / frame_roots;
for every .json file prints how often each spelling occurs. Spellings: first = /tmp/q_22c714e1, second = /tmp/jjyeung/q_22c714e1."""
import gzip, json, sys
from pathlib import Path
FIRST, SECOND = '/tmp/q_22c714e1', '/tmp/jjyeung/q_22c714e1'
def text(p):
    raw = p.read_bytes()
    return (gzip.decompress(raw) if p.suffix == '.gz' else raw).decode('utf-8', 'replace')
def name(root):
    r = str(root)
    for label, pre in (('second', SECOND), ('first', FIRST)):
        if r == pre or r.startswith(pre + '/'): return label
    return 'job-folder' if r.startswith(FIRST + '_') else 'other'
seen = {'frames.json': 0, 'request.json': 0}
for p in sorted(Path(sys.argv[1]).rglob('*')):
    if not p.is_file() or not (p.name.endswith('.json') or p.name.endswith('.json.gz')): continue
    t = text(p); base = p.name[:-3] if p.name.endswith('.gz') else p.name
    n2 = t.count(SECOND); n1 = t.count(FIRST + '/') + t.count(FIRST + '"'); nj = t.count(FIRST + '_')
    if n1 or n2 or nj: print('SPELL count %s first=%d second=%d job-folder=%d' % (p, n1, n2, nj))
    if base in seen:
        try: d = json.loads(t)
        except ValueError: print('SPELL %s unreadable' % p); continue
        roots = d.get('roots') if base == 'frames.json' else d.get('frame_roots')
        if roots is None: continue
        seen[base] += 1
        print('SPELL %s %s: %s %s' % (base, p, sorted({name(r) for r in roots}), roots))
for k, v in seen.items():
    if not v: print('SPELL %s: none among the fetched files (read it on the node with srun --overlap)' % k)
