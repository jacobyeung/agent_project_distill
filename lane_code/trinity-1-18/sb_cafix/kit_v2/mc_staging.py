"""Every /scratch path the GPU pass, its launcher and its preflight read, with sizes, for staging on another node at the
same absolute paths. Writes out/v2/STAGING_FRAMES.txt (one frame path per line, for `tar -T`) and out/v2/STAGING.json,
which lists itself and STAGING_FRAMES.txt among its items (its own bytes are a fixed point). The list is self-contained:
the kit's pinned vnice.sh and terminator.sh replace /data3/shared/scripts/vnice, the phrase-fold file and the two files
its provenance pins are staged for the preflight, and nothing on /home or /data* is read. vnice's terminator writes only
/tmp/terminator/$USER-<pid>; the pass writes only out/v2/track (caches included).
Pricing and the summary run afterwards on this node (CPU) from out/v2/track.
Usage: python mc_staging.py   (p1cpu interpreter)
"""
import json, os
from pathlib import Path
import mc_common as C

ENV = Path('/scratch/jjyeung/envs/sam3_capretry_native_v1')


def tree_bytes(root):
    total = files = 0
    for d, _, names in os.walk(root):
        for n in names:
            p = os.path.join(d, n)
            if not os.path.islink(p):
                total += os.path.getsize(p); files += 1
    return total, files


def sources():
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    prov = seeds['summary']['S_PHR'].get('phrase_folds') or {}
    phrase = [('phrase folds (seed provenance)', prov['path']), ('phrase decision (seed provenance)', prov['decision']),
              ('phrase bars (seed provenance)', prov['bars_file'])] if prov else []
    return ([('sam3 checkpoint', C.CHECKPOINT), ('sam3 source', C.SAM3_ROOT), ('sam3 receipt', C.RECEIPT),
             ('sam3 vendor receipt', C.VENDOR_RECEIPT), ('interpreter env', ENV), ('kit code (vendor/vnice.sh, vendor/terminator.sh included)', C.KIT),
             ('frame sets', C.OUT/'FRAME_SETS.json'), ('seeds', C.OUT/'seeds'), ('guard (withheld list)', C.OUT/'GUARD.json'),
             ('population (RULING 1056Z)', C.POPULATION), ('ruling transcript', C.RULING),
             ('kit manifest', C.OUT/'KIT_MANIFEST.sha256'), ('frozen bars', C.OUT/'BARS_FROZEN.json'),
             ('bars amendment', C.BARS_AMENDMENT)] + phrase +
            [('control: frame list', C.OUT/'STAGING_FRAMES.txt'), ('control: this staging list', C.OUT/'STAGING.json')])


def main():
    fs = C.read_json(C.OUT/'FRAME_SETS.json')
    frames = sorted({d['path'] for c in fs['captures'] for d in c['dense']})
    frame_bytes = sum(os.path.getsize(p) for p in frames)
    (C.OUT/'STAGING_FRAMES.txt').write_text('\n'.join(frames)+'\n')
    staging = C.OUT/'STAGING.json'
    items = []
    for kind, path in sources():
        path = Path(path)
        if path == staging:
            items.append(dict(kind=kind, path=str(path), bytes=0, files=1, check_bytes=False))
            continue
        size, n = tree_bytes(path) if path.is_dir() else (path.stat().st_size, 1)
        items.append(dict(kind=kind, path=str(path), bytes=size, files=n, check_bytes=not path.is_dir()))
    items.append(dict(kind='dense frames (list in out/v2/STAGING_FRAMES.txt)', path=[os.path.commonpath(frames)], bytes=frame_bytes,
                      files=len(frames), check_bytes=False))
    outside = [i['path'] for i in items for p in (i['path'] if isinstance(i['path'], list) else [i['path']]) if not p.startswith('/scratch/')]
    if outside:
        raise SystemExit(f'staged paths outside /scratch: {outside}')
    me = next(i for i in items if i['path'] == str(staging))
    for _ in range(8):
        total = sum(i['bytes'] for i in items)
        C.write_json(staging, dict(items=items, total_bytes=total, writes=str(C.OUT/'track'), extra_writes=['/tmp/terminator/$USER-<pid> (vnice)'],
                                   note='absolute paths; stage at the same paths on the GPU node; the pass, launcher and preflight '
                                        'read nothing else (the pass refuses modules outside /scratch)'))
        size = staging.stat().st_size
        if size == me['bytes']:
            break
        me['bytes'] = size
    else:
        raise SystemExit('STAGING.json size did not reach a fixed point')
    print(json.dumps(dict(total_bytes=total, total_gib=total/2**30, items=[(i['kind'], i['bytes'], i['files']) for i in items])))
    C.status(f'Staging (STAGING.json): {len(items)} items incl. control files and pinned vnice, {total:,} bytes '
             f'({total/2**30:.2f} GiB), {len(frames)} frames.')


if __name__ == '__main__':
    main()
