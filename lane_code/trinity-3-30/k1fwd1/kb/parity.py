"""Compare own.npz grids of a new return against job 170235's return (stdlib only).
usage: parity.py OLD_result.tar.gz NEW_result.tar.gz OUT.json"""
import ast, io, json, struct, sys, tarfile, zipfile
from array import array


def npy(raw):
    assert raw[:6] == b'\x93NUMPY'
    major = raw[6]
    hlen = struct.unpack('<H', raw[8:10])[0] if major == 1 else struct.unpack('<I', raw[8:12])[0]
    start = 10 if major == 1 else 12
    head = ast.literal_eval(raw[start:start + hlen].decode('latin1'))
    assert head['descr'] == '<f8' and not head['fortran_order'], head
    data = array('d')
    data.frombytes(raw[start + hlen:])
    return tuple(head['shape']), data


def grids(path):
    out = {}
    with tarfile.open(path, 'r:gz') as archive:
        for item in archive:
            parts = item.name.split('/')
            if item.isfile() and parts[-1] in ('own.npz', 'PHASE_COMPLETE.json') and 'probe' in parts:
                key = parts[-2]
                raw = archive.extractfile(item).read()
                if parts[-1] == 'own.npz':
                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        out.setdefault(key, {})['arrays'] = {n[:-4]: npy(z.read(n)) for n in z.namelist()}
                else:
                    out.setdefault(key, {})['phase'] = json.loads(raw)
    return out


def main():
    old, new = grids(sys.argv[1]), grids(sys.argv[2])
    rows, worst_abs, worst_rel, identical = [], 0.0, 0.0, True
    for key in sorted(k for k in new if 'arrays' in new[k]):
        a, b = old[key]['arrays'], new[key]['arrays']
        assert set(a) == set(b) == {'depth', 'gravity'}, key
        row = dict(capture=key, checkpoint=new[key].get('phase', {}).get('checkpoint'))
        for name in ('depth', 'gravity'):
            (sa, da), (sb, db) = a[name], b[name]
            assert sa == sb, (key, name, sa, sb)
            same = da.tobytes() == db.tobytes()
            mabs = max(abs(x - y) for x, y in zip(da, db))
            mrel = max(abs(x - y) / abs(x) if x else (0.0 if x == y else float('inf')) for x, y in zip(da, db))
            row[name] = dict(shape=sa, bit_identical=same, max_abs=mabs, max_rel=mrel)
            identical &= same
            worst_abs, worst_rel = max(worst_abs, mabs), max(worst_rel, mrel)
        rows.append(row)
    result = dict(captures=len(rows), bit_identical=identical, max_abs=worst_abs, max_rel=worst_rel,
                  passed=bool(rows) and worst_rel <= 1e-4, rows=rows)
    json.dump(result, open(sys.argv[3], 'w'), indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
