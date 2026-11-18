"""Read-only row census: for every SQLite file under DIR (argv[1]) with a table holding a JSON 'row' column, count rows by
(category, origin): origin 'n' for pools of new rows, 's' for re-rendered sealed pools (w1g, r1g, absent), 'r' for the direct
route pool. Prints one JSON document. Stdlib only; opens databases read-only."""
import json, sqlite3, sys, collections, os
from pathlib import Path
SEALED = {'w1g', 'r1g', None}
def origin(p):
    if p in SEALED: return 's'
    return 'r' if 'route' in str(p) else 'n'
out = {}
for f in sorted(Path(sys.argv[1]).rglob('*')):
    if not f.is_file() or f.suffix not in ('.sqlite', '.db', '.sqlite3'): continue
    try:
        c = sqlite3.connect('file:' + str(f) + '?mode=ro', uri=True)
        tables = [t for (t,) in c.execute("select name from sqlite_master where type='table'")]
    except sqlite3.Error as e:
        out[str(f)] = dict(error=str(e)); continue
    for t in tables:
        cols = [r[1] for r in c.execute('pragma table_info("%s")' % t)]
        if 'row' not in cols: continue
        cnt, bad = collections.Counter(), 0
        for (s,) in c.execute('select row from "%s"' % t):
            try: d = json.loads(s)
            except (TypeError, ValueError): bad += 1; continue
            cnt[str(d.get('category')) + '|' + origin(d.get('pool'))] += 1
        out[str(f) + ':' + t] = dict(total=sum(cnt.values()), unparsed=bad, by_family=dict(sorted(cnt.items())))
print(json.dumps(out, indent=1, sort_keys=True))
