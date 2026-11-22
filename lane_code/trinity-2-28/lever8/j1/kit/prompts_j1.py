"""J1 step 2 (CPU, p1cpu): text prompts per operand name and GT box prompts per bound instance, for detect.py.

Text: for each eligible capture, every distinct operand name of its eligible items, written as the served call writes it
(stage1.name_key: lowercase and strip; the step-544 rows write the question's own name, so 'heater' stays 'heater'). The
operand list records each (item, name, bound instance) and whether the T1 row holds the model's ground call for it.
Box (arm k): for each bound GT instance of the capture, on every anchor where the instance raster is non-empty, the tight box
(select_j1.box_from_mask, normalised cx, cy, w, h). The GT raster's sha256 per instance is kept, so relift_j1 can check that
the boxes came from the same GT. Also the operand-frame counts per capture (text prompt-frames = names x 32 anchors; box
prompt-frames = non-empty GT anchors) and the capture with the fewest of them (the CPU rehearsal capture).
Writes out/PROMPTS_J1.json. Usage: CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B prompts_j1.py
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import j1_common as G
import select_j1 as S


def name_key(name):
    """stage1.py:24-25, copied: the served phrase rule (strip, lower)."""
    return str(name).strip().lower()


def build(R, refs, rows, items, objects):
    by_cap = {}
    for o in objects:
        by_cap.setdefault(o['capture'], []).append(o)
    gt_of = {i['capture']: i['gt_path'] for i in items}
    out = []
    for cap in sorted(by_cap):
        with np.load(gt_of[cap], allow_pickle=False) as z:
            inst = z['inst'].copy()
        names, operands, units = [], [], {}
        for o in by_cap[cap]:
            p = name_key(o['name'])
            if p not in names:
                names.append(p)
            served = {x['name'].strip().lower() for x in rows[o['item_id']]['objects']}
            operands.append(dict(item_id=o['item_id'], name=o['name'], prompt=p, instance_id=o['instance_id'],
                                 served_call=o['name'].strip().lower() in served))
            iid = o['instance_id']
            if iid not in units:
                target = inst == iid
                boxes = [S.box_from_mask(target[f]) for f in range(32)]
                units[iid] = dict(instance_id=iid, gt_sha256=G.mask_sha(target),
                                  boxes=[dict(slot=f+1, box=b, gt_pixels=int(target[f].sum())) for f, b in enumerate(boxes) if b is not None])
        out.append(dict(capture=cap, dataset=G.fine(cap), prompts=names, operands=operands, k_units=list(units.values()),
                        text_prompt_frames=32*len(names), box_prompt_frames=sum(len(u['boxes']) for u in units.values())))
    return out


def main():
    R = G.load_relift(); R.dependencies()
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    caps = build(R, refs, rows, items, objects)
    frames = G.read_json(G.FRAMES_J1)
    if sorted(c['capture'] for c in frames['captures']) != [c['capture'] for c in caps] or frames['failed']:
        raise ValueError('FRAMES_J1 does not cover the 46 captures')
    fewest = min(caps, key=lambda c: (c['text_prompt_frames']+c['box_prompt_frames'], c['capture']))
    body = dict(schema='j1-prompts-v1', captures=caps, frames_j1_sha256=G.sha256_file(G.FRAMES_J1),
                rule=dict(prompt='stage1.name_key(name): strip + lower (b/e2e_reader/stage1.py:24-25, 82); no alias, no singular map',
                          box='tight box of the bound GT instance on the 240x320 grid, [cx, cy, w, h] in [0, 1]'),
                totals=dict(captures=len(caps), prompts=sum(len(c['prompts']) for c in caps), operands=sum(len(c['operands']) for c in caps),
                            k_units=sum(len(c['k_units']) for c in caps), text_prompt_frames=sum(c['text_prompt_frames'] for c in caps),
                            box_prompt_frames=sum(c['box_prompt_frames'] for c in caps),
                            operands_without_served_call=sum(not o['served_call'] for c in caps for o in c['operands'])),
                rehearsal_capture=fewest['capture'], inputs=dict(items=str(G.ITEMS), items_sha256=G.sha256_file(G.ITEMS)))
    G.write_json(G.PROMPTS_J1, body)
    print(json.dumps(dict(status='PASS', **body['totals'], rehearsal_capture=fewest['capture'],
                          rehearsal_prompt_frames=fewest['text_prompt_frames']+fewest['box_prompt_frames'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
