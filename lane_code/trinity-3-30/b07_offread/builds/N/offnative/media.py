"""Registered ReVSI clip identities, correspondence checks, and tar staging."""
from pathlib import Path
import argparse
import hashlib
import json
import tarfile
import numpy as np
from .io import dump, load, owned, sha
from .paths import ROOT
from .source import validate_mapping

POOL = '/project/community/jjyeung/okh7/313db5a47f11ff0c/'
ARCHIVE = '/project/community/jjyeung/okh7/d46dd56e669a050f/7b5d2192.tar'


def build(indices, needed, *, clips=None):
    rows = {}; files = []
    for entry in needed:
        name = entry['relative_path']; source = indices[Path(name).stem]
        i32, i64 = source['32-frame'], source['64-frame']
        slots = [i64.index(i) for i in i32]
        pair = []
        for prefix in ('a', 'b'):
            member = prefix+'/'+name
            p = Path(clips)/member if clips else None
            h = sha(p) if p and p.is_file() else None
            size = p.stat().st_size if h else None
            pair.append(h)
            files.append(dict(member=member, relative_path=name, sha256=h, bytes=size,
                              source=POOL+name if prefix=='a' and not entry['upload_required'] else ARCHIVE,
                              transport='pool' if prefix=='a' and not entry['upload_required'] else 'tar',
                              status='pinned' if h else 'hash_pending'))
        rows[name] = dict(path='b/'+name, clip_sha256=pair[0], original_sha256=pair[1],
                          anchor_indices=i32, dense_indices=i64, anchor_slots=slots,
                          dense_decode_indices=list(range(64)))
    mapping = dict(schema='revsi-dense64-v1', registration='sampled_video_frame_idx.json',
                   hashes_pending=any(f['sha256'] is None for f in files), clips=rows)
    validate_mapping(mapping)
    return mapping, dict(schema='revsi-media-v1', archive_source=ARCHIVE, accepted_pool=POOL, files=files,
                         hashes_pending=mapping['hashes_pending'])


def decode(path):
    import av
    with av.open(str(path)) as video:
        return [f.to_ndarray(format='rgb24') for f in video.decode(video=0)]


def correspondence(mapping, clips):
    validate_mapping(mapping, production=True)
    records = []
    for name, row in sorted(mapping['clips'].items()):
        a, b = Path(clips)/'a'/name, Path(clips)/row['path']
        if sha(a) != row['clip_sha256'] or sha(b) != row['original_sha256']:
            raise ValueError('pixel-check clip hash differs: '+name)
        x, y = decode(a), decode(b)
        if len(x) != 32 or len(y) != 64:
            raise ValueError('pixel-check clip frame count differs: '+name)
        matched, neighbour = [], []
        for frame, slot in zip(x, row['anchor_slots'], strict=True):
            other = slot+1 if slot < 63 else slot-1
            if frame.shape != y[slot].shape or frame.shape != y[other].shape:
                raise ValueError('pixel-check dimensions differ: '+name)
            matched.append(float(np.abs(frame.astype(np.float32)-y[slot]).mean()))
            neighbour.append(float(np.abs(frame.astype(np.float32)-y[other]).mean()))
        records.append(dict(video=name, matched_rgb_mae=matched, neighbour_rgb_mae=neighbour,
                            matched_mean=float(np.mean(matched)), neighbour_mean=float(np.mean(neighbour))))
    return dict(schema='pixel-correspondence-v1', videos=len(records), records=records,
                scope='Pixel correspondence diagnostic; no benchmark answers or scores.')


def extract_local(archive, destination, names):
    """Admit a complete deterministic local tar before writing any clip."""
    destination = owned(destination)
    if destination.exists():
        raise ValueError('clip destination exists; use a fresh directory')
    with tarfile.open(archive) as source:
        members = source.getmembers()
        expected = {p+'/'+n for p in ('a','b') for n in names}
        if (len(members) != len(expected) or {m.name for m in members} != expected
                or any(not m.isfile() or m.size <= 0 for m in members)):
            raise ValueError('local tar is incomplete or contains unsafe members')
        required = sum(m.size for m in members)
        used = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
        if used+required > 4_000_000_000:
            raise ValueError('clip extraction exceeds the 4 GB build cap')
        import shutil
        if shutil.disk_usage('/scratch').free-required < 100_000_000_000:
            raise ValueError('clip extraction violates scratch free-space reserve')
        for member in members:
            target = destination/member.name; target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as inp, target.open('xb') as out:
                while chunk := inp.read(1024*1024): out.write(chunk)
    return destination


def stage(manifest, destination, *, archive=None, pool=None, archive_pin=None):
    """Stage 41 new anchors and 302 dense clips from the tar, plus the accepted pool."""
    destination = owned(destination)
    if destination.exists(): raise ValueError('media destination exists')
    files = manifest['files']
    if manifest.get('hashes_pending') or any(not f.get('sha256') or not f.get('bytes') for f in files):
        raise ValueError('media hashes pending; production refused')
    names = [f['member'] for f in files]
    if len(names) != len(set(names)) or any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):
        raise ValueError('unsafe media manifest')
    by_member = {f['member']: f for f in files}
    receipt = {}
    archive=Path(archive or manifest['archive_source'])
    if archive_pin is not None and (archive.stat().st_size!=archive_pin['bytes'] or sha(archive)!=archive_pin['sha256']):
        raise ValueError('media archive identity differs')
    def copy(inp, row):
        target=destination/row['member']; target.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256(); count=0
        with target.open('xb') as out:
            while chunk := inp.read(1024*1024):
                count += len(chunk)
                if count > row['bytes']: raise ValueError('media size exceeds manifest')
                h.update(chunk); out.write(chunk)
        if count != row['bytes'] or h.hexdigest() != row['sha256']:
            raise ValueError('media identity differs: '+row['member'])
        receipt[row['member']] = dict(sha256=h.hexdigest(), bytes=count)
    with tarfile.open(archive) as source:
        members=source.getmembers(); seen=set()
        for m in members:
            if m.name in seen or m.name not in by_member or not m.isfile():
                raise ValueError('unsafe or unknown media tar member')
            seen.add(m.name)
        required={f['member'] for f in files if f['transport']=='tar'}
        if not required <= seen: raise ValueError('media tar is incomplete')
        for m in members:
            row=by_member[m.name]
            if row['transport']=='tar':
                with source.extractfile(m) as inp: copy(inp,row)
    for row in files:
        if row['transport']=='pool':
            with (Path(pool or manifest['accepted_pool'])/row['relative_path']).open('rb') as inp: copy(inp,row)
    dump(destination/'STAGED.json', receipt)
    return receipt


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive');p.add_argument('--clips')
    p.add_argument('--destination',default='work/revsi_clips_n3')
    args=p.parse_args()
    needed=load(ROOT/'out/NEED_302.json')
    clips=args.clips
    if args.archive:
        clips=extract_local(args.archive,args.destination,[r['relative_path'] for r in needed])
    mapping,manifest=build(load(ROOT/'out/REGISTERED_FRAME_INDICES.json'),needed,clips=clips)
    mapping['registration_sha256']=sha(ROOT/'out/REGISTERED_FRAME_INDICES.json')
    dump(ROOT/'out/REVSI_DENSE_MAPPING.json',mapping)
    dump(ROOT/'out/REVSI_MEDIA_MANIFEST.json',manifest)
    if clips:dump(ROOT/'out/REVSI_PIXEL_CORRESPONDENCE.json',correspondence(mapping,clips))
    print(json.dumps({'videos':len(mapping['clips']), 'hashes_pending':mapping['hashes_pending'],
                      'mapping_sha256':sha(ROOT/'out/REVSI_DENSE_MAPPING.json')}))


if __name__=='__main__':main()
