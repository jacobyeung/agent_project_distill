"""Pose rows: can each have a nested 64-frame dense sample inside its posed ordinals, and how many new decodes?

usage: pose_count.py CLIPS.jsonl.gz ROWS.jsonl.gz DIVISION.json SOURCE OUT.json [CLIPS_NP_OUT.jsonl.gz]
Pose rows are windows (32 ordinals, first ordinal is not 0), so the tree rule nested_indices (which needs
ordinal 0 and the clip's total) does not apply. The window rule used here is its direct analogue: bisect the
largest gap inside [first, last] of the row's own 32 ordinals until 64 (midpoint, ties to the earlier gap).
  posed ordinals of a scene = union of the ordinals of every pose row of that scene in this source (the frames
  that exist in the pose frame store with pins).
  A: exact window rule; a row needs no new decode when every midpoint is a posed ordinal.
  B: a nested 64 exists inside the posed ordinals of the window (|posed in [first,last]| >= 64), using the
     posed ordinal nearest each midpoint (store-snapped variant of A).
Counts are given for all selected rows and for rows whose scene is a division train scene.
Optionally writes the non-pose clips to CLIPS_NP_OUT (so the large pose clip list never leaves the host).
"""
import collections
import gzip
import json
import sys


def window_nested(sparse, count=64, available=None):
    chosen = set(sparse)
    lo, hi = sparse[0], sparse[-1]
    avail = None if available is None else sorted(a for a in available if lo <= a <= hi)
    import bisect
    while len(chosen) < count:
        ordered = sorted(chosen)
        gaps = sorted(((b - a, a, b) for a, b in zip(ordered, ordered[1:])), key=lambda g: (-g[0], g[1]))
        pick = None
        for length, a, b in gaps:
            if length < 2:
                break
            mid = (a + b) // 2
            if avail is None:
                pick = mid
                break
            j = bisect.bisect_left(avail, mid)
            cands = [avail[k] for k in (j - 1, j) if 0 <= k < len(avail) and a < avail[k] < b]
            if cands:
                pick = min(cands, key=lambda c: (abs(c - mid), c))
                break
        if pick is None:
            return None
        chosen.add(pick)
    return sorted(chosen)


def main():
    clips_p, rows_p, div_p, source, out_p = sys.argv[1:6]
    np_out = sys.argv[6] if len(sys.argv) > 6 else None
    division = json.load(open(div_p))
    train = set(division.get('train_scenes', []))
    pose_sigs = set()
    rows_by_sig = collections.Counter()
    for line in gzip.open(rows_p, 'rt'):
        r = json.loads(line)
        if r['source'] == source and r.get('selected') and r.get('sig'):
            pose_sigs.add(r['sig'])
            rows_by_sig[r['sig']] += 1
    clips = {}
    npw = gzip.open(np_out, 'wt') if np_out else None
    for line in gzip.open(clips_p, 'rt'):
        c = json.loads(line)
        if c['sig'] in pose_sigs:
            clips[c['sig']] = c
        elif npw is not None and 'pose' not in c.get('streams', {}):
            npw.write(line)
    if npw is not None:
        npw.close()
    posed = collections.defaultdict(dict)
    for c in clips.values():
        for i, sha in zip(c['frame_indices'], c['sha256']):
            posed[(c['dataset'], c['scene'])][i] = sha
    res = collections.Counter()
    new_decodes = collections.defaultdict(set)
    by_ds = collections.Counter()
    gaps = collections.Counter()
    for sig, c in clips.items():
        n = rows_by_sig[sig]
        key = (c['dataset'], c['scene'])
        scene_key = f"{c['dataset']}/{c['scene']}"
        tags = ['all'] + (['train'] if scene_key in train else [])
        idx = c['frame_indices']
        ok_idx = idx == sorted(set(idx)) and len(idx) == 32
        a = window_nested(idx, 64) if ok_idx else None
        b = window_nested(idx, 64, posed[key]) if ok_idx else None
        for t in tags:
            res[(t, 'rows')] += n
            by_ds[(t, c['dataset'])] += n
            if not ok_idx:
                res[(t, 'invalid_ordinals')] += n
                continue
            if a is None:
                res[(t, 'window_too_short')] += n
                continue
            missing = [i for i in a if i not in posed[key]]
            if not missing:
                res[(t, 'A_no_new_decode')] += n
            if b is not None:
                res[(t, 'B_nested64_inside_posed')] += n
            if t == 'all':
                for i in missing:
                    new_decodes[key].add(i)
        span = idx[-1] - idx[0]
        gaps[min(span // 64, 20)] += n
    out = dict(source=source, division_train_scenes=len(train), clips=len(clips),
               counts={f'{k[0]}|{k[1]}': v for k, v in sorted(res.items())},
               rows_by_dataset={f'{k[0]}|{k[1]}': v for k, v in sorted(by_ds.items())},
               posed_ordinals_per_scene=dict(collections.Counter(min(len(v) // 32, 20) * 32 for v in posed.values())),
               window_span_over_64_hist=dict(sorted(gaps.items())),
               A_new_decodes_distinct=sum(len(v) for v in new_decodes.values()),
               A_new_decode_scenes=len(new_decodes), scenes=len(posed))
    json.dump(out, open(out_p, 'w'), indent=1)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
