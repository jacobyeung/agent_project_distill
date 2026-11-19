"""Every /scratch path the GPU pass reads, with sizes, for staging on another node at the same absolute paths.
Writes out/v2/STAGING.json and out/v2/STAGING_FRAMES.txt (one frame path per line, for `tar -T`).
The pass reads only these; pricing and the summary run afterwards on this node (CPU) from out/v2/track.
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


def main():
    fs = C.read_json(C.OUT/'FRAME_SETS.json')
    frames = sorted({d['path'] for c in fs['captures'] for d in c['dense']})
    frame_bytes = sum(os.path.getsize(p) for p in frames)
    roots = [os.path.commonpath(frames)]
    (C.OUT/'STAGING_FRAMES.txt').write_text('\n'.join(frames)+'\n')
    items = []
    for kind, path in [('sam3 checkpoint', C.CHECKPOINT), ('sam3 source', C.SAM3_ROOT), ('sam3 receipt', C.RECEIPT),
                       ('sam3 vendor receipt', C.VENDOR_RECEIPT), ('interpreter env', ENV), ('kit code', C.KIT),
                       ('frame sets', C.OUT/'FRAME_SETS.json'), ('seeds', C.OUT/'seeds'), ('guard (withheld list)', C.OUT/'GUARD.json'),
                       ('kit manifest', C.OUT/'KIT_MANIFEST.sha256'), ('frozen bars', C.OUT/'BARS_FROZEN.json')]:
        path = Path(path)
        size, n = tree_bytes(path) if path.is_dir() else (path.stat().st_size, 1)
        items.append(dict(kind=kind, path=str(path), bytes=size, files=n))
    items.append(dict(kind='dense frames (list in out/v2/STAGING_FRAMES.txt)', path=roots, bytes=frame_bytes, files=len(frames)))
    total = sum(i['bytes'] for i in items)
    C.write_json(C.OUT/'STAGING.json', dict(items=items, total_bytes=total, writes=str(C.OUT/'track'),
                                            note='absolute paths; stage at the same paths on the GPU node; the tracker pass '
                                                 'reads nothing else (it refuses modules outside /scratch)'))
    print(json.dumps(dict(total_gib=total/2**30, items=[(i['kind'], round(i['bytes']/2**30, 3), i['files']) for i in items])))
    C.status(f'Staging (STAGING.json): {len(items)} items, {total/2**30:.2f} GiB, {len(frames)} frames.')


if __name__ == '__main__':
    main()
