"""Check every STAGING_PART2.json row against the sb_ph2fix2 extract (bytes + sha256); list unlisted members and symlinks."""
import hashlib, json, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_ph2chk/work')
EX = W/'extract'
SRC = Path('/scratch/jjyeung/orch_n30/sb_ph2fix')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def check(row):
    p = EX/row['staged_path']
    if p.is_symlink():
        return row['staged_path'], 'SYMLINK', os.readlink(p)
    if not p.is_file():
        return row['staged_path'], 'MISSING', None
    if p.stat().st_size != row['bytes']:
        return row['staged_path'], 'SIZE', p.stat().st_size
    d = sha(p)
    return row['staged_path'], ('OK' if d == row['sha256'] else 'SHA'), d


def main():
    inv = json.loads((EX/'out/STAGING_PART2.json').read_text())
    rows = inv['inventory']
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(check, rows, chunksize=64))
    bad = [r for r in res if r[1] != 'OK']
    listed = {r['staged_path'] for r in rows}
    files, links = [], []
    for base, dirs, names in os.walk(EX):
        for n in names + [d for d in dirs if (Path(base)/d).is_symlink()]:
            p = Path(base)/n
            rel = str(p.relative_to(EX))
            (links if p.is_symlink() else files).append(rel)
    unlisted = sorted(set(files) - listed)
    top = {}
    for u in unlisted:
        k = '/'.join(u.split('/')[:3])
        top[k] = top.get(k, 0) + 1
    out = dict(status=inv.get('status'), manifest_rows=len(rows), manifest_bytes=sum(r['bytes'] for r in rows),
               manifest_files_field=inv.get('files'), manifest_bytes_field=inv.get('bytes'),
               manifest_same_as_source=sha(EX/'out/STAGING_PART2.json') == sha(SRC/'out/STAGING_PART2.json'),
               n_ok=sum(r[1] == 'OK' for r in res), n_bad=len(bad), bad=bad[:50],
               files_in_extract=len(files), symlinks_in_extract=links[:40], n_symlinks=len(links),
               unlisted_count=len(unlisted), unlisted_by_dir=top,
               sources_outside_scratch=sorted({r['path'] for r in rows if not r['path'].startswith('/scratch/')})[:20])
    (W/'MANIFEST_CHECK.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items()}, indent=1)[:5000])


if __name__ == '__main__':
    main()
