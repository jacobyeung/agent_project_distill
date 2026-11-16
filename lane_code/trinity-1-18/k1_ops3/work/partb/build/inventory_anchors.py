"""Inventory and verify the local production anchor archive with native staging."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

import job_support as H

ROOT = Path(__file__).resolve().parent
ARCHIVE = Path('/scratch/jjyeung/k1/partB/k1_partB_anchors.tar')

def main():
    free = shutil.disk_usage(ROOT).free
    assert free > 205 * 1024**3
    assert ARCHIVE.stat().st_size == 2646947840
    digest = H.sha(ARCHIVE)
    assert digest == '1405c09c2f30ed7110f7550a6a4c7e41be8709fdbff3a17c2375a9b214a8158a'
    S, _, NS, _ = H.native()
    members = {}
    with tarfile.open(ARCHIVE, 'r|') as archive:
        for item in archive:
            name = str(S.relative(item.name))
            if item.isdir():
                continue
            assert item.isfile() and name not in members
            hashed = hashlib.sha256()
            with archive.extractfile(item) as stream:
                for chunk in iter(lambda: stream.read(1024**2), b''):
                    hashed.update(chunk)
            members[name] = dict(bytes=item.size, sha256=hashed.hexdigest())
    H.dump(ROOT/'inputs/anchors.members.json', members)
    target = ROOT/'evidence/report6_anchors'
    assert not target.exists()
    actual = H.unpack(S, ARCHIVE, target, strip=0)
    NS.verify_inventory(actual, members)
    H.dump(ROOT/'evidence/REPORT6_ANCHOR_UNPACK.json', dict(inventory_equal=True, members=len(actual)))
    manifest = json.loads((ROOT/'manifest_v2/a40fbc19.json').read_text())
    checked = set()
    for capture in manifest['captures']:
        for frame in (capture['dense_frames'][i] for i in capture['anchor_slots']):
            name = str(Path(frame['path']).relative_to('/scratch/jjyeung/k1_frames'))
            assert members[name]['sha256'] == frame['sha256']
            checked.add(name)
    result = dict(archive=str(ARCHIVE), bytes=ARCHIVE.stat().st_size, sha256=digest,
                  members=len(members), manifest_frames=len(checked), strip=0,
                  inventory_equal=True, free_before=free, extraction=str(target))
    H.dump(ROOT/'evidence/REPORT6_ANCHORS.json', result)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
