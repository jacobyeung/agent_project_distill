"""Verify every STAGING_PART2.json member in the extracted tar (bytes + sha256) and list unlisted tar members."""
import hashlib, json, os, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

EX = Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/extract')
SRC = Path('/scratch/jjyeung/orch_n30/sb_ph2fix')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def check(row):
    p = EX/row['staged_path']
    if not p.is_file():
        return row['staged_path'], 'MISSING', None
    if p.stat().st_size != row['bytes']:
        return row['staged_path'], 'SIZE', p.stat().st_size
    d = sha(p)
    return row['staged_path'], ('OK' if d == row['sha256'] else 'SHA'), d


def main():
    inv_ex = json.loads((EX/'out/STAGING_PART2.json').read_text())
    same_manifest = sha(EX/'out/STAGING_PART2.json') == sha(SRC/'out/STAGING_PART2.json')
    rows = inv_ex['inventory']
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(check, rows, chunksize=64))
    bad = [r for r in res if r[1] != 'OK']
    listed = {r['staged_path'] for r in rows}
    all_files = []
    for base, dirs, names in os.walk(EX):
        for n in names:
            all_files.append(str((Path(base)/n).relative_to(EX)))
    unlisted = sorted(set(all_files) - listed)
    roles = {}
    for r in rows:
        for x in r['roles']:
            roles.setdefault(x, [0, 0]); roles[x][0] += 1; roles[x][1] += r['bytes']
    ext_src = sorted({r['path'] for r in rows if not r['path'].startswith('/scratch/')})
    out = dict(status=inv_ex.get('status'), manifest_rows=len(rows), manifest_bytes=sum(r['bytes'] for r in rows),
               manifest_same_as_source=same_manifest, bad=bad[:50], n_bad=len(bad), files_in_extract=len(all_files),
               unlisted_count=len(unlisted), unlisted_top=sorted({u.split('/')[0] + '/' + (u.split('/')[1] if '/' in u else '') for u in unlisted}),
               unlisted_sample=unlisted[:40], roles=roles, sources_outside_scratch=ext_src[:20],
               manifest_keys=[k for k in inv_ex if k != 'inventory'])
    Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/MANIFEST_CHECK.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ('unlisted_sample',)}, indent=1)[:4000])


if __name__ == '__main__':
    main()
