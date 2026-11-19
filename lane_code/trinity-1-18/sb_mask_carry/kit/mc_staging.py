"""Every /scratch path the GPU pass reads, with sizes, for staging on another node (same absolute paths there).
Writes out/STAGING.json and out/STAGING_FRAMES.txt (one frame path per line, for `tar -T`).
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
    fs = C.frame_sets()
    frames = sorted({d['path'] for c in fs['captures'].values() for d in c['dense']})
    frame_bytes = sum(os.path.getsize(p) for p in frames)
    roots = sorted({str(Path(p).parents[1]) for p in frames})
    (C.OUT/'STAGING_FRAMES.txt').write_text('\n'.join(frames)+'\n')
    items = []
    for kind, path in [('sam3 checkpoint', C.CHECKPOINT), ('sam3 source', C.SAM3_ROOT), ('sam3 receipt', C.RECEIPT),
                       ('sam3 fp32 MLP shim (CPU only)', C.TOWER), ('interpreter env', ENV), ('kit code', C.KIT),
                       ('frame sets', C.OUT/'FRAME_SETS.json'), ('seeds', C.OUT/'seeds')]:
        path = Path(path)
        size, n = tree_bytes(path) if path.is_dir() else (path.stat().st_size, 1)
        items.append(dict(kind=kind, path=str(path), bytes=size, files=n))
    items.append(dict(kind='dense frames (list in out/STAGING_FRAMES.txt)', path=roots, bytes=frame_bytes, files=len(frames)))
    total = sum(i['bytes'] for i in items)
    C.write_json(C.OUT/'STAGING.json', dict(items=items, total_bytes=total, writes=str(C.OUT/'track'),
                                            note='paths are absolute; stage them at the same paths on the GPU node'))
    print(json.dumps(dict(total_gib=total/2**30, items=[(i['kind'], round(i['bytes']/2**30, 3), i['files']) for i in items])))


if __name__ == '__main__':
    main()
