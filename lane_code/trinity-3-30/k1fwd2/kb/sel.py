"""Stream a deterministic tar.gz of the scored captures of a k1fwd2 return to stdout (stdlib only).
usage: sel.py NEW_result.tar.gz G3T.json INCLUDE_OWN(0|1) EXTRA_FILE...   (extras go under k1fwd2/)"""
import gzip, hashlib, io, json, sys, tarfile
from pathlib import Path


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, allow_nan=False).encode()).hexdigest()


def main():
    src, g3t, include_own, extras = sys.argv[1], sys.argv[2], sys.argv[3] == '1', sys.argv[4:]
    keys = {digest(name)[:16] for name in json.load(open(g3t))['captures']}
    names = {'PHASE_COMPLETE.json', 'fov.npz', 'FOV_RECEIPT.json'} | ({'own.npz'} if include_own else set())
    members = []
    with tarfile.open(src, 'r:gz') as archive:
        for item in archive:
            if not item.isfile():
                continue
            parts = item.name.split('/')
            if item.name.startswith('/') or '..' in parts:
                raise ValueError('unsafe member ' + item.name)
            probe = len(parts) >= 3 and parts[0] == 'native' and parts[1] == 'probe'
            if probe and len(parts) == 4:
                if parts[2] not in keys or parts[3] not in names:
                    continue
            elif probe and len(parts) != 3:
                continue
            members.append((item.name, archive.extractfile(item).read()))
    for path in extras:
        members.append(('k1fwd2/' + Path(path).name, Path(path).read_bytes()))
    with gzip.GzipFile(fileobj=sys.stdout.buffer, mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as out:
            for name, raw in sorted(members):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(raw), 0o644, 0
                out.addfile(info, io.BytesIO(raw))
    seen = {m[0].split('/')[2] for m in members if m[0].count('/') == 3}
    print(json.dumps(dict(members=len(members), capture_dirs=len(seen), missing=sorted(keys - seen)[:5],
                          bytes_raw=sum(len(r) for _, r in members))), file=sys.stderr)


if __name__ == '__main__':
    main()
