"""Parity and FoV-variant check of a k1fwd2 return against job 170235's return (stdlib only).
usage: fov_check.py OLD_result.tar.gz NEW_result.tar.gz G3T.json OUT.json OVERLAY.tar MANIFEST_MEMBER"""
import ast, hashlib, io, json, math, statistics, struct, sys, tarfile, zipfile
from array import array


def npy(raw):
    assert raw[:6] == b'\x93NUMPY'
    major = raw[6]
    hlen = struct.unpack('<H', raw[8:10])[0] if major == 1 else struct.unpack('<I', raw[8:12])[0]
    start = 10 if major == 1 else 12
    head = ast.literal_eval(raw[start:start + hlen].decode('latin1'))
    assert head['descr'] in ('<f8', '<f4') and not head['fortran_order'], head
    data = array('d' if head['descr'] == '<f8' else 'f')
    data.frombytes(raw[start + hlen:])
    return tuple(head['shape']), head['descr'], data


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load(path):
    out = {}
    with tarfile.open(path, 'r:gz') as archive:
        for item in archive:
            parts = item.name.split('/')
            if item.isfile() and len(parts) >= 4 and parts[-3] == 'probe':
                name = parts[-1]
                if name in ('own.npz', 'fov.npz', 'PHASE_COMPLETE.json', 'FOV_RECEIPT.json'):
                    out.setdefault(parts[-2], {})[name] = archive.extractfile(item).read()
    return out


def arrays(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return {n[:-4]: npy(z.read(n)) for n in z.namelist()}


def main():
    old, new = load(sys.argv[1]), load(sys.argv[2])
    g3t = json.load(open(sys.argv[3]))['captures']
    with tarfile.open(sys.argv[5]) as overlay:
        manifest = json.loads(overlay.extractfile(sys.argv[6]).read())
    by_key = {digest(c['canonical'])[:16]: c for c in manifest['captures']}
    grid = dict(source='tree 168872 student_pilot/tower_read.py 2cd338e1: GRID_UV = np.linspace(0, 1000, 51, dtype=np.float32)',
                values_float32_sha256=hashlib.sha256(array('f', [1000 * i / 50 for i in range(51)]).tobytes()).hexdigest())
    keys = {digest(name)[:16]: name for name in g3t}
    rows, problems = [], []
    stats = {k: [] for k in ('fovdeg_B_V1', 'fovdeg_B_V2', 'fovdeg_V1_V2', 'ratio_V1_B', 'ratio_V2_B')}
    for key in sorted(k for k in new if 'own.npz' in new[k]):
        row = dict(key=key, scored=key in keys)
        a, b = arrays(old[key]['own.npz']), arrays(new[key]['own.npz'])
        assert set(a) == set(b) == {'depth', 'gravity'}, key
        same = all(a[n][0] == b[n][0] and a[n][2].tobytes() == b[n][2].tobytes() for n in ('depth', 'gravity'))
        row['served_equal'] = same
        if not same:
            problems.append(key + ': served own.npz differs from 170235')
        phase = json.loads(new[key]['PHASE_COMPLETE.json'])
        cap = by_key[key]
        row.update(canonical=cap['canonical'], anchor_indices=cap['anchor_indices'],
                   capture_sha256_equal=digest(cap) == phase['capture_sha256'], grid_uv=grid['values_float32_sha256'])
        if not row['capture_sha256_equal']:
            problems.append(key + ': PHASE_COMPLETE capture_sha256 differs from the batch manifest capture')
        row['checkpoint'] = phase['checkpoint']['sha256'] if isinstance(phase['checkpoint'], dict) else phase['checkpoint']
        if 'fov.npz' not in new[key] or 'FOV_RECEIPT.json' not in new[key]:
            problems.append(key + ': fov.npz or FOV_RECEIPT.json missing')
            rows.append(row)
            continue
        rec = json.loads(new[key]['FOV_RECEIPT.json'])
        f = arrays(new[key]['fov.npz'])
        ok = (rec['files']['fov.npz'] == hashlib.sha256(new[key]['fov.npz']).hexdigest()
              and rec['served_depth_sha256'] == hashlib.sha256(b['depth'][2].tobytes()).hexdigest()
              and rec['capture_sha256'] == phase['capture_sha256'] and rec['checks']['second_pass_pose_fov_bit_identical']
              and sorted(f) == rec['keys'])
        want = ['depth_V1', 'depth_V2', 'fov_B', 'fov_V1', 'fov_V2'] if key in keys else ['depth_V1', 'fov_B', 'fov_V1']
        ok &= sorted(f) == want
        if key in keys:
            ref = array('f', [x for pair in g3t[keys[key]]['fov_hw_rad'] for x in pair])
            ok &= f['fov_V2'][2].tobytes() == ref.tobytes() and rec['canonical'] == keys[key]
        for name in want:
            ok &= f[name][0] == ((32, 51, 51) if name.startswith('depth') else (32, 2))
            ok &= f[name][1] == ('<f8' if name.startswith('depth') else '<f4')
        row.update(receipt_ok=bool(ok), second_pass_max_abs=rec['checks']['second_pass_pose_fov_max_abs'],
                   missing=rec['missing'], seconds=rec['seconds'])
        if not ok:
            problems.append(key + ': FoV receipt/array check failed')
        if key in keys:
            B, V1, V2 = f['fov_B'][2], f['fov_V1'][2], f['fov_V2'][2]
            deg = 180 / math.pi
            stats['fovdeg_B_V1'].append(statistics.median(abs(x - y) * deg for x, y in zip(B, V1)))
            stats['fovdeg_B_V2'].append(statistics.median(abs(x - y) * deg for x, y in zip(B, V2)))
            stats['fovdeg_V1_V2'].append(statistics.median(abs(x - y) * deg for x, y in zip(V1, V2)))
            served = b['depth'][2]
            stats['ratio_V1_B'].append(statistics.median(x / y for x, y in zip(f['depth_V1'][2], served)))
            stats['ratio_V2_B'].append(statistics.median(x / y for x, y in zip(f['depth_V2'][2], served)))
        rows.append(row)
    scored = [r for r in rows if r['scored']]
    summary = dict(grid_uv=grid, anchor_indices_source='batch manifest capture (prompt frames asserted equal in boundaries.own); bound by capture_sha256', captures=len(rows), scored=len(scored), scored_expected=len(keys),
                   served_bit_identical=sum(r['served_equal'] for r in rows),
                   receipts_ok=sum(bool(r.get('receipt_ok')) for r in rows),
                   second_pass_bit_identical=sum(r.get('second_pass_max_abs') == 0.0 for r in rows),
                   medians_over_scored={k: (statistics.median(v) if v else None) for k, v in stats.items()},
                   problems=problems, passed=not problems and len(scored) == len(keys))
    json.dump(dict(summary=summary, rows=rows), open(sys.argv[4], 'w'), indent=1)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
