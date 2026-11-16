"""Verify the salted inventory against the approved node-local reserve archive."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    build = json.loads((ROOT/'evidence/ASSET_BUILD.json').read_text())
    source = Path('/scratch/jjyeung/n30_mirror/b10_reserve/R0_RESERVE_20261116.tar')
    digest = sha(source)
    expected = '2bbae12a984fde1228bdb571f5aee390c1e6a82dc554310aa04c6fd0fe80a116'
    if digest != expected or digest != build['source_sha256']:
        raise ValueError('Reserve archive digest differs')
    registration = json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
    mapping = json.loads((ROOT/'evidence/ID_MAP.json').read_text())
    wanted = {}
    for row in map(json.loads, (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()):
        old = mapping[row['id']]
        for index, ref in zip(row['source_frame_indices'], row['frame_refs']):
            name = f"frames/{old['dataset']}/{old['scene']}/{index:06d}.png"
            pin = registration['frames'][ref]
            if name in wanted and wanted[name] != pin:
                raise ValueError('Conflicting source-frame pin')
            wanted[name] = pin
    seen = set()
    with tarfile.open(source, 'r:') as archive:
        for member in archive:
            if member.name not in wanted:
                continue
            if not member.isfile() or member.name in seen:
                raise ValueError('Invalid reserve member')
            body = archive.extractfile(member).read()
            if dict(bytes=len(body), sha256=hashlib.sha256(body).hexdigest()) != wanted[member.name]:
                raise ValueError('Reserve frame differs')
            seen.add(member.name)
    if seen != set(wanted) or len(seen) != 3136:
        raise ValueError('Reserve frame membership differs')
    result = dict(status='PASS', source=str(source), source_bytes=source.stat().st_size,
                  source_sha256=digest, verified_frames=len(seen), files=registration['files'])
    (ROOT/'evidence/FIX1_RESERVE.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
