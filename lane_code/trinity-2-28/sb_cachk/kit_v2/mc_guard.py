"""Guards: the training-data exclusion lists against every capture the kit touches, the ladder's room folds, k1_split,
and the K1_TRACK.json reuse check. Writes out/v2/GUARD.json.

Exclusion pins (orchestrator 1010Z): R0 rooms (R0_ROOMS.txt bdb5d402 and the K1 split authority's r0_scenes), dev-S1
(969cdb56), BENCH v2 (3119aa4a), the 80 withheld rooms (634820b4), K1 held-out (teacher_k1 4d4736cf). Each list is
matched in every name form it uses: canonical capture, d-token capture, room, d-token room, rung-1 alias.
Usage: python mc_guard.py   (p1cpu interpreter)
"""
import json, sys, time
import mc_common as C
import mc_ladder as L

LISTS = dict(
    R0=('/scratch/jjyeung/orch_n30/b10_reserve/out/R0_ROOMS.txt', 'bdb5d402'),
    dev_S1=('/scratch/jjyeung/orch_n30/sb_rowOI/inputs/dev_s1.json', '969cdb56'),
    BENCH_v2=('/scratch/jjyeung/orch_n30/sb_cntrev/k1/auth/BENCH_SCENE_EXCLUSIONS_v2.json', '3119aa4a'),
    withheld_80=('/scratch/jjyeung/orch_n30/sb_cntrev/k1/auth/WITHHELD_ROOMS_80.json', '634820b4'),
    K1_heldout=('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/build17/inputs/'
                '27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390.json', '4d4736cf'),
)
HELDOUT_57 = '/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_CAPTURES_HELDOUT_57.txt'
TOKEN = {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}


def forms(canonical, room):
    ds, cap = canonical.split('/', 1)
    rds, rname = room.split('/', 1)
    return {canonical, f'{TOKEN[ds]}/{cap}', room, f'{TOKEN[rds]}/{rname}'}


def names(kind, raw, text=None):
    """Every name a list excludes, flattened to strings."""
    if kind == 'R0':
        return set(text.split())
    if kind == 'dev_S1':
        out = set(raw['rooms']) | set(raw['physical_groups']) | set(raw['natives'])
        for k, v in raw['aliases'].items():
            out |= {k, *v}
        for k, v in raw['canonical'].items():
            out |= {k, *v}
        return out
    if kind == 'BENCH_v2':
        out = set(raw['scenes']) | set(raw['physical_groups']) | {'/'.join(t) for t in raw['rung1_tokens']}
        return out | {m['group'] for m in raw['members'].values()}
    if kind == 'withheld_80':
        out = set(raw['rooms'])
        for k, v in raw['aliases'].items():
            out |= {k, *v}
        return out
    if kind == 'K1_heldout':
        held = [c for c in raw['teacher_k1']['captures'] if c['k1_split'] != 'train']
        return {c['canonical'] for c in held} | {c['room'] for c in held} | {a for c in held for a in c.get('aliases', [])}
    raise KeyError(kind)


def main():
    t0 = time.monotonic()
    caps, labels, rowids, tableids, folds, truth, head = L.setup()
    caps = sorted(caps, key=lambda c: c['canonical'])
    rows = {c['canonical']: [r['id'] for r in c['rows'] if r['id'] in rowids] for c in caps}
    out = dict(captures=len(caps), rows=sum(map(len, rows.values())), lists={})
    for kind, (path, prefix) in LISTS.items():
        data = C.read(path)
        sha = C.PINS[str(C.local(path))]
        raw = None if kind == 'R0' else json.loads(data)
        if kind == 'K1_heldout' and raw['teacher_k1']['sha256'][:8] != prefix:
            raise SystemExit(f'teacher_k1 sha256 {raw["teacher_k1"]["sha256"][:12]} is not {prefix}')
        if kind != 'K1_heldout' and sha[:8] != prefix:
            raise SystemExit(f'{kind} sha256 {sha[:12]} is not the pinned {prefix}')
        excluded = names(kind, raw, data.decode() if kind == 'R0' else None)
        if kind == 'R0':
            r0 = json.loads(C.read(LISTS['K1_heldout'][0]))['r0_scenes']
            excluded |= set(r0['rooms']) | set(r0['captures'])
        hits = [c['canonical'] for c in caps if forms(c['canonical'], c['room']) & excluded]
        out['lists'][kind] = dict(path=path, sha256=sha, pin=prefix, names=len(excluded), hit_captures=hits,
                                  hit_rooms=sorted({c['room'] for c in caps if c['canonical'] in hits}),
                                  hit_rows=sum(len(rows[k]) for k in hits), passed=not hits)
    held57 = set(C.read(HELDOUT_57).decode().split())
    out['lists']['K1_heldout']['heldout_57_hits'] = sorted(held57 & {c['canonical'] for c in caps})
    out['exclusions_passed'] = all(v['passed'] for v in out['lists'].values()) and not out['lists']['K1_heldout']['heldout_57_hits']
    withheld = out['lists']['withheld_80']
    out['withheld_default'] = ('keep: the kit fits nothing and the ladder it reproduces priced these rows; bars stay on '
                               f"1,037 rows and a sensitivity row on the other {out['rows']-withheld['hit_rows']} rows "
                               'decides nothing; mc_track_pass.py --exclude-withheld skips them if the orchestrator rules so'
                               ) if withheld['hit_captures'] else None
    split = {c['canonical']: c.get('k1_split') for c in caps}
    teacher = json.loads(C.read(LISTS['K1_heldout'][0]))['teacher_k1']
    k1 = {c['canonical']: c['k1_split'] for c in teacher['captures']}
    k1.update({k: 'refused' for k in teacher['refused'] if k not in k1})
    out['k1_split'] = dict(pinned_train=sorted({str(v) for v in split.values()}),
                           teacher_k1={v: sum(k1.get(k) == v for k in split) for v in sorted({str(k1.get(k)) for k in split})},
                           teacher_k1_refused=sorted(k for k in split if k1.get(k) == 'refused'),
                           passed=set(split.values()) == {'train'} and {k1.get(k) for k in split} <= {'train', 'refused'})
    room_fold = {c['room']: folds[c['room']] for c in caps}
    by_fold = {}
    for room, k in room_fold.items():
        by_fold.setdefault(int(k), set()).add(room)
    pub = L.published(('A0_deployed',))
    fold_rows = {}
    for (arm, rid), r in pub.items():
        fold_rows.setdefault(r['room'], set()).add(r['fold'])
    disjoint = all(not (by_fold[a] & by_fold[b]) for a in by_fold for b in by_fold if a < b)
    out['folds'] = dict(rooms=len(room_fold), per_fold={k: len(v) for k, v in sorted(by_fold.items())},
                        captures_per_fold={k: sum(room_fold[c['room']] == k for c in caps) for k in sorted(by_fold)},
                        disjoint=disjoint, equal_published=all(fold_rows.get(r) == {k} for r, k in room_fold.items()),
                        passed=disjoint and sorted(by_fold) == list(range(5)) and all(fold_rows.get(r) == {k} for r, k in room_fold.items()))
    if C.REUSE.exists():
        out['reuse_K1_TRACK'] = dict(path=str(C.REUSE), status='PRESENT: checked by mc_track_pass.py --reuse against the checkpoint and frames')
    else:
        out['reuse_K1_TRACK'] = dict(path=str(C.REUSE), status='MISSING: file and its directory are absent on this node; '
                                     'the kit runs the tracker itself')
    out['seconds'] = time.monotonic()-t0
    C.code_pins()
    C.write_json(C.OUT/'GUARD.json', out)
    w = out['lists']['withheld_80']
    print(json.dumps({k: (v if k != 'lists' else {kk: (vv['passed'], len(vv['hit_captures']), vv['hit_rows']) for kk, vv in v.items()})
                      for k, v in out.items()}), flush=True)
    C.status(f"Guard (GUARD.json): R0/dev-S1/BENCH v2/K1 held-out hits "
             f"{[len(out['lists'][k]['hit_captures']) for k in ('R0', 'dev_S1', 'BENCH_v2', 'K1_heldout')]}; withheld-80 hits "
             f"{len(w['hit_captures'])} captures, {w['hit_rows']} rows (default keep, question raised); k1_split train "
             f"{out['k1_split']['passed']}; folds disjoint and equal to the ladder {out['folds']['passed']}; K1_TRACK reuse "
             f"{out['reuse_K1_TRACK']['status'].split(':')[0]}.")


if __name__ == '__main__':
    main()
