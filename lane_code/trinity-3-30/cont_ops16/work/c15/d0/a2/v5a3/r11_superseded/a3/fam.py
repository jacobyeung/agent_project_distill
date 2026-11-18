"""Read-only family census. Usage: fam.py INPUT_DB DIR
Counts rows by family in INPUT_DB (the staged row store) and in every SQLite file under DIR (the run's admission directory)
with a 'rows' table holding JSON rows. A family is printed as an 8-hex code of its category plus an origin letter (n new pool,
s re-rendered sealed pool, r direct route pool); the code-to-name table stays off this machine. For the rebuilt question
stream (a database under a 'vqa' directory) it prints admitted = rows present there and refused = input rows of the family
whose row key is absent there. No row text, pool, rule or source value is printed."""
import hashlib, json, sqlite3, sys, collections
from pathlib import Path
SEALED = {'w1g', 'r1g', None}
def code(d):
    p = d.get('pool')
    return hashlib.sha256(str(d.get('category')).encode()).hexdigest()[:8] + '|' + ('s' if p in SEALED else 'r' if 'route' in str(p) else 'n')
def scan(f):
    c = sqlite3.connect('file:' + str(f) + '?mode=ro', uri=True)
    if 'row' not in [r[1] for r in c.execute('pragma table_info("rows")')]: return None
    fam, keys, bad = collections.Counter(), {}, 0
    for (s,) in c.execute('select row from rows'):
        try: d = json.loads(s)
        except (TypeError, ValueError): bad += 1; continue
        if not isinstance(d, dict): bad += 1; continue
        k = code(d); fam[k] += 1; keys[str(d.get('qid'))] = k
    return fam, keys, bad
src = scan(Path(sys.argv[1])); assert src is not None
out = dict(input=dict(total=sum(src[0].values()), unparsed=src[2], by_family=dict(sorted(src[0].items()))), databases={})
for f in sorted(Path(sys.argv[2]).rglob('*')):
    if not f.is_file() or f.suffix not in ('.sqlite', '.db', '.sqlite3'): continue
    try: r = scan(f)
    except sqlite3.Error as e: out['databases'][str(f.relative_to(sys.argv[2]))] = dict(error=type(e).__name__); continue
    if r is None: continue
    rec = dict(total=sum(r[0].values()), unparsed=r[2], by_family=dict(sorted(r[0].items())))
    if 'vqa' in f.relative_to(sys.argv[2]).parts:
        refused = collections.Counter(k for q, k in src[1].items() if q not in r[1])
        rec.update(admitted=dict(sorted(r[0].items())), refused=dict(sorted(refused.items())), refused_total=sum(refused.values()),
                   not_in_input=sum(1 for q in r[1] if q not in src[1]))
    out['databases'][str(f.relative_to(sys.argv[2]))] = rec
print(json.dumps(out, indent=1, sort_keys=True))
