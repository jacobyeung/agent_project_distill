"""Step 2 audit: draw a seeded, dataset-stratified sample of POS and MISS rows and render contact sheets.

Each tile shows one (capture, slot, name) row: the frame, the teacher mask in red (POS) and the GT instance raster in
green, the name and row id in the caption. A reader marks each tile right or wrong in the TSV this writes
(column `verdict` empty); the P7 numbers to reproduce are 4.6% wrong POS masks and 36.8% wrong MISS rows.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .common import read_json, rle_decode
from .teacher import capture_key


def rows_of(lab):
    for slot, fr in lab['frames'].items():
        for name, r in fr.items():
            for p in r['proposals']:
                if p['cls'] == 'POS':
                    yield 'POS', slot, name, p['k'], p['inst']
            for i in r['miss']:
                yield 'MISS', slot, name, None, i


def tile(frame, inst_raster, mask, inst, caption, size=256):
    im = np.asarray(frame.convert('RGB')).astype(float)
    h, w = im.shape[:2]
    g = np.kron(inst_raster == inst, np.ones((2, 2), bool))[:h, :w]
    out = im.copy()
    if mask is not None:
        out[mask] = out[mask] * 0.45 + np.array([255, 0, 0]) * 0.55
    edge = g & ~np.pad(g, 1, mode='edge')[2:, 1:-1] | g & ~np.pad(g, 1, mode='edge')[:-2, 1:-1] \
        | g & ~np.pad(g, 1, mode='edge')[1:-1, 2:] | g & ~np.pad(g, 1, mode='edge')[1:-1, :-2]
    out[g] = out[g] * 0.7 + np.array([0, 255, 0]) * 0.3
    out[edge] = [0, 255, 0]
    t = Image.fromarray(out.astype(np.uint8))
    t.thumbnail((size, size))
    canvas = Image.new('RGB', (size, size + 14), 'white')
    canvas.paste(t, (0, 14))
    ImageDraw.Draw(canvas).text((2, 1), caption[:42], fill='black')
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--labels', required=True)
    ap.add_argument('--teacher-root', required=True)
    ap.add_argument('--frame-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--per-class', type=int, default=48)
    ap.add_argument('--seed', type=int, default=17)
    a = ap.parse_args(argv)
    man = {c['canonical']: c for c in json.loads(Path(a.manifest).read_text())['captures']}
    pool = collections.defaultdict(list)
    for p in sorted(Path(a.labels).glob('*.labels.json.gz')):
        lab = read_json(p)
        if lab['k1_split'] != 'train':
            continue
        for cls, slot, name, k, inst in rows_of(lab):
            pool[(cls, lab['canonical'].split('/')[0])].append((lab['canonical'], slot, name, k, inst))
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    picked = []
    for cls in ('POS', 'MISS'):
        keys = sorted(k for k in pool if k[0] == cls)
        per = max(1, a.per_class // max(1, len(keys)))
        for key in keys:
            rows = sorted(pool[key])
            picked += [(cls,) + r for r in rng.sample(rows, min(per, len(rows)))]
    cache = {}
    tiles, tsv = [], ['id\tclass\tcanonical\tslot\tname\tk\tinst\tverdict']
    for n, (cls, can, slot, name, k, inst) in enumerate(picked):
        if can not in cache:
            cache = {can: (read_json(Path(a.teacher_root) / capture_key(can) / 'teacher.json.gz'),
                           np.load(man[can]['gt']['path'], allow_pickle=False))}
        t, z = cache[can]
        f = man[can]['frames'][int(slot)]
        frame = Image.open(Path(a.frame_root) / f['sha256'][:2] / f"{f['sha256']}.png")
        mask = rle_decode(t['frames'][slot]['phrases'][name]['instances'][k]['mask']) if k is not None else None
        tiles.append(tile(frame, z['inst'][int(slot)], mask, inst, f'{n} {cls} {name}'))
        tsv.append(f'{n}\t{cls}\t{can}\t{slot}\t{name}\t{k}\t{inst}\t')
    for s in range(0, len(tiles), 16):
        sheet = Image.new('RGB', (4 * 256, 4 * 270), 'white')
        for j, tl in enumerate(tiles[s:s + 16]):
            sheet.paste(tl, ((j % 4) * 256, (j // 4) * 270))
        sheet.save(out / f'sheet_{s // 16:02d}.png')
    (out / 'AUDIT_SAMPLE.tsv').write_text('\n'.join(tsv) + '\n')
    print(json.dumps({'picked': len(picked), 'by': collections.Counter((p[0], p[1].split('/')[0]) for p in picked).most_common(),
                      'pool': {f'{k[0]}:{k[1]}': len(v) for k, v in sorted(pool.items())}}, default=str))


if __name__ == '__main__':
    main()
