"""Dump requested rows of P's rebuilt database after its full-hash gate (p_sample_request_v1)."""
import gzip, hashlib, json, os, random, sqlite3, sys
from pathlib import Path

GATE = os.environ.get('PS_GATE', '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84')
LIMIT = 5_000_000


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()


def main(db, request, rd0, out):
    db, request, out = Path(db), Path(request), Path(out)
    if out.exists(): raise SystemExit('PS_OUTPUT_EXISTS')
    actual = sha(db)
    if actual != GATE: raise SystemExit('PS_GATE_FAILED:' + actual)
    req = json.loads(request.read_bytes())
    if req.get('schema') != 'p_sample_request_v1': raise SystemExit('PS_REQUEST_SCHEMA')
    order, uf = [], []
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as c:
        for i, row in c.execute('SELECT i,row FROM rows ORDER BY i'):
            order.append(i)
            src = (json.loads(row).get('s1_source') or {})
            if isinstance(src, dict) and src.get('name') == 'U_Faithful': uf.append(i)
        picks = []
        for pos in req['uniform_positions']:
            picks.append(('uniform', pos, order[pos]))
        for pos in sorted(random.Random(20261121).sample(range(len(uf)), min(20, len(uf)))):
            picks.append(('U_Faithful', pos, uf[pos]))
        absent = None
        g = Path(rd0) / 'rdiff.json.gz' if rd0 and rd0 != '-' else None
        if g is not None and g.is_file():
            absent = json.loads(gzip.decompress(g.read_bytes()))['P_absent']
            for pos in sorted(random.Random(20261122).sample(range(len(absent)), min(20, len(absent)))):
                picks.append(('P_absent', pos, absent[pos]['i']))
        rows = []
        for cls, pos, i in picks:
            r = c.execute('SELECT i,row,target FROM rows WHERE i=?', (i,)).fetchone()
            if r is None: raise SystemExit('PS_ROW_MISSING:%s' % i)
            rows.append(dict(**{'class': cls}, position=pos, i=r[0], row=r[1], target=r[2]))
    value = dict(database_sha256=actual, count=len(order), U_Faithful_count=len(uf),
                 P_absent_count=None if absent is None else len(absent),
                 P_absent_source=None if absent is None else dict(path=str(g), sha256=sha(g)),
                 request_sha256=sha(request), rows=rows)
    data = json.dumps(value, ensure_ascii=False, indent=1).encode()
    if len(data) > LIMIT: raise SystemExit('PS_TOO_LARGE:%d' % len(data))
    tmp = out.with_name('.' + out.name + '.tmp'); tmp.write_bytes(data); os.replace(tmp, out)
    print('p_sample rows', len(rows), 'bytes', len(data), 'P_absent', value['P_absent_count'], flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:5])
