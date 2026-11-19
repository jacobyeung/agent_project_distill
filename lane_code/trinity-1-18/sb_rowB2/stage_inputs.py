"""Resolve exact, source-pinned GT bytes from the local mirror only."""
import collections
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
MIRROR = Path('/scratch/jjyeung/n30_mirror')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()

def main():
    rows = [json.loads(s) for s in (ROOT/'inputs/sources.jsonl').read_text().splitlines()]
    expected = {}
    for r in rows:
        p = r['provenance']
        assert expected.setdefault(p['raster'], p['raster_sha256']) == p['raster_sha256']
    candidates = json.loads((ROOT/'inputs/all_gt_candidates.json').read_text())
    groups = collections.defaultdict(list)
    for original, entries in candidates.items():
        for archive, member, size in entries:
            groups[archive].append((original, member))
    dest = ROOT/'inputs/gt'
    dest.mkdir(exist_ok=True)
    resolved, mismatches, pins = {}, [], {}
    for archive, entries in sorted(groups.items()):
        print('Resolving', archive, len(entries), flush=True)
        pins[archive] = sha(archive)
        with tarfile.open(archive) as tar:
            for original, member in entries:
                if original in resolved:
                    continue
                data = tar.extractfile(member).read()
                digest = hashlib.sha256(data).hexdigest()
                if digest != expected[original]:
                    mismatches.append(dict(original=original, archive=archive, member=member, actual_sha256=digest, expected_sha256=expected[original]))
                    continue
                p = dest/(digest+'.npz')
                p.write_bytes(data)
                resolved[original] = dict(path=str(p), sha256=digest, archive=archive, member=member)
    # A renamed loose raster is admitted only by its complete byte hash.
    wanted_hashes = {v:k for k,v in expected.items() if k not in resolved}
    for p in MIRROR.rglob('*.npz'):
        digest = sha(p)
        if digest in wanted_hashes:
            original = wanted_hashes[digest]
            resolved[original] = dict(path=str(p), sha256=digest)
    # Recover the exact dev-S1 authority, without loading unrelated archive data.
    inventory = json.loads((ROOT/'inputs/archive_inventory.json').read_text())
    dev_expected = '969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'
    for a in inventory:
        names = [n for n,s in a['members'] if n.endswith('dev_scene_exclusions.json')]
        if not names:
            continue
        with tarfile.open(a['path']) as tar:
            data = tar.extractfile(names[0]).read()
        if hashlib.sha256(data).hexdigest() == dev_expected:
            (ROOT/'inputs/dev_scene_exclusions.json').write_bytes(data)
            pins[a['path']+'::'+names[0]] = dev_expected
            break
    result = dict(input_sha256=pins, resolved=resolved, mismatches=mismatches,
                  missing=[dict(original=p, expected_mirror=str(MIRROR/p.split('/orch_n30/',1)[1]), sha256=h, status='MISSING')
                           for p,h in sorted(expected.items()) if p not in resolved])
    (ROOT/'inputs/GT_RESOLUTION.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Resolved',len(resolved),'missing',len(result['missing']),'hash mismatches',len(mismatches),flush=True)
    (ROOT/'STATUS.md').write_text(f'GT discovery resolved {len(resolved)} of {len(expected)} exact source-pinned rasters from local archives and files. The remaining {len(result["missing"])} rasters are MISSING and affected rows will be refused. Audit, geometry recomputation, room filtering, balancing, and validation are pending.\n')

if __name__ == '__main__':
    main()
