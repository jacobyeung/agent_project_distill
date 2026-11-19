"""Frame sets D64 (64 dense frames) and A32 (the 32 anchors) for the 209 priced K1 training captures.

Checks frame order: dense frames strictly increase in source index, dense_frames[anchor_slots[i]] is anchor i's
file (path and sha256 equal to the model row's anchor list), its index is anchor_indices[i], the raster's
frame_indices equal anchor_indices, and every PNG's bytes hash to its pinned sha256.
Usage: python mc_frames.py   (p1cpu interpreter; writes out/FRAME_SETS.json)
"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import mc_common as C

sys.path.insert(0, str(C.BOX))
ROWSET = '/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt'
ROWSET_SHA = 'e7646798c8a1e12ca6291723c5f686473b9954a78d068dcfa65c314be35a98ac'


def priced_captures():
    manifest = C.read_json(C.BOX/'pinned_train.json')
    rowids = set(C.read(ROWSET).decode().splitlines())
    if C.PINS[ROWSET] != ROWSET_SHA or len(rowids) != 1037:
        raise ValueError('K1_TRAIN_1037 rowset pin mismatch')
    caps = [c for c in manifest['captures'] if any(r['id'] in rowids for r in c['rows'])]
    return manifest, caps, rowids


def frame_record(item):
    path, sha = item
    got = C.sha256_file(path)
    return path, sha, got, os.path.getsize(path)


def capture_checks(c):
    dense, slots = c['dense_frames'], c['anchor_slots']
    anchors = c['model_row']['student_input']['frames']
    idx = [d['index'] for d in dense]
    gt = np.load(C.local(c['gt']['path']))
    return dict(
        dense_64=len(dense) == 64, anchors_32=len(slots) == 32 and len(anchors) == 32,
        dense_time_order=all(a < b for a, b in zip(idx, idx[1:])),
        slots_increase=all(a < b for a, b in zip(slots, slots[1:])),
        anchor_file_equal=all(dense[s]['sha256'] == a['sha256'] and dense[s]['path'] == a['path'] for s, a in zip(slots, anchors)),
        anchor_index_equal=[dense[s]['index'] for s in slots] == list(c['anchor_indices']),
        model_row_indices=list(c['model_row']['student_input'].get('frame_indices', c['anchor_indices'])) == list(c['anchor_indices']),
        raster_indices=[int(x) for x in gt['frame_indices']] == list(c['anchor_indices']),
        paths_local=all(d['path'].startswith('/scratch/') for d in dense))


def main():
    import math_v2 as M
    C.read(C.BOX/'math_v2.py')
    manifest, caps, rowids = priced_captures()
    folds = M.folds(c['room'] for c in caps)
    items = sorted({(d['path'], d['sha256']) for c in caps for d in c['dense_frames']})
    with ProcessPoolExecutor(4) as pool:
        hashed = {p: (s, g, n) for p, s, g, n in pool.map(frame_record, items, chunksize=64)}
    bad = [p for p, (s, g, n) in hashed.items() if s != g]
    for p, (s, g, n) in hashed.items():
        C.PINS[p] = g
    records, failures = [], []
    for c in sorted(caps, key=lambda c: c['canonical']):
        C.read(c['gt']['path'])
        if C.PINS[c['gt']['path']] != c['gt']['sha256']:
            failures.append(dict(capture=c['canonical'], check='raster_sha256'))
        checks = capture_checks(c)
        failures += [dict(capture=c['canonical'], check=k) for k, v in checks.items() if not v]
        dense = [dict(slot=k, index=d['index'], path=d['path'], sha256=d['sha256'], bytes=hashed[d['path']][2]) for k, d in enumerate(c['dense_frames'])]
        records.append(dict(capture=c['canonical'], room=c['room'], fold=folds[c['room']], k1_split=c['k1_split'],
                            anchor_slots=list(c['anchor_slots']), anchor_indices=list(c['anchor_indices']),
                            D64=list(range(len(dense))), A32=list(c['anchor_slots']), dense=dense, checks=checks))
    passed = not bad and not failures and len(records) == 209
    total = sum(n for _, _, n in hashed.values())
    C.code_pins()
    C.write_json(C.OUT/'FRAME_SETS.json', dict(
        status='PASS' if passed else 'FAIL', captures=records, unique_frames=len(hashed), frame_bytes=total,
        sha_mismatches=bad, failures=failures, canvas=list(C.CANVAS),
        frame_sets=dict(D64='the 64 dense frames in source-index order; masks read at the 32 anchors',
                        A32='the 32 anchors only, in order')))
    print(json.dumps(dict(status='PASS' if passed else 'FAIL', captures=len(records), frames=len(hashed), gib=total/2**30,
                          mismatches=len(bad), failures=failures[:10])), flush=True)
    C.status(f'Stage 1 (frame sets): {"PASS" if passed else "FAIL"}; {len(records)} captures, {len(hashed)} unique PNG frames '
             f'({total/2**30:.2f} GiB) hashed; frame-order failures {len(failures)}. out/FRAME_SETS.json.')


if __name__ == '__main__':
    main()
