"""Dense 64-frame manifest for GF-1: plan (metadata only, no RGB read) and seal (after new frames exist).

One rule: the dense ordinals of a clip are `student_pilot.dense_eval.nested_indices(total, student32, 64)`
(midpoint bisection of the largest gap, the tree's single dense rule). Frames at those ordinals come from
  - the row's own pin at a student ordinal (content identity, whatever store the row names),
  - the k6 map (frame_map.jsonl.gz, sha 17aa3e9e...) when it holds that (scene, ordinal),
  - a new decode: ScanNet/ScanNet++ from the k6 source mp4 (same decoder rule as k6 `wd.py`: mode same,
    640x480 INTER_AREA, PNG level 3); ARKitScenes from Apple `lowres_wide.zip` by range read (k6 `wa.py`
    rule: member nearest the trajectory timestamp of row k of `lowres_wide.traj`, tol 2 ms, orient, x2.5
    INTER_CUBIC, PNG level 3).
A clip is keyed by content: clip_key = p3_provenance.digest([[ordinal, sha256] x 64]). Rows are looked up by
their clip signature (dataset, scene, fps, total, frame_indices, student sha256s), never by a path or a
canonical name, so aliases with identical content share one clip and two clocks of one scene stay apart.

Commands
  plan  CLIPS.jsonl.gz FRAME_MAP FRAME_PLAN FPS_AUTHORITY OUT_DIR  -> plan.json.gz, tasks_v.json.gz,
        tasks_a.json, refusals.json, summary.json   (metadata only)
  seal  OUT_DIR WD_OUT.jsonl WA_OUT.jsonl SEALED.json [PIXEL_PARITY.jsonl] -> r2-dense-manifest-v1 + index
"""
import collections
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.environ.get('B06_TREE', '/scratch/jjyeung/orch_n30/b06_a2dense/cache/work/tree_r1')
if TREE not in sys.path:
    sys.path.insert(0, TREE)
from student_pilot.dense_eval import nested_indices  # noqa: E402  (the tree's one dense rule)
from student_pilot.p3_provenance import digest  # noqa: E402

COUNT = 64
NEW_ROOT = '/data2/k6dx'          # logical root of new dense frames (content-addressed, <sha[:2]>/<sha>.png)
K6_ROOT = '/data2/k6tk'
DATASET_OF = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}


def logical(root, sha):
    return f'{root}/{sha[:2]}/{sha}.png'


def load_map(path):
    fm = collections.defaultdict(dict)
    with gzip.open(path, 'rt') as fh:
        for line in fh:
            r = json.loads(line)
            fm[(r['d'], r['s'])][r['i']] = dict(sha256=r['sha256'], path=r['path'], w=r['w'], h=r['h'])
    return fm


def signature_key(dataset, scene, fps, total, indices, shas):
    import hashlib
    key = [dataset, scene, fps, total, indices, shas]
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()


class Refusal(Exception):
    def __init__(self, code, detail=''):
        super().__init__(code + (': ' + detail if detail else ''))
        self.code, self.detail = code, detail


def plan_names(plan, fm):
    """canonical name -> k6 alias (unique in the k6 plan), alias -> dataset."""
    names = plan.get('_names')
    if names is None:
        canon = {v['n'][:-4]: s for s, v in plan['v'].items()}
        canon.update({'arkitscenes/' + a['u'].split('/')[-2]: s for s, a in plan['a'].items()})
        names = plan['_names'] = dict(canon=canon, dataset={s: d for d, s in fm})
    return names


def resolve_clip(clip, fm, plan, fps_authority):
    """Complete a clip record (map-joined clips get total, fps and shas). Raises Refusal."""
    d, s = clip['dataset'], clip['scene']
    idx = clip['frame_indices']
    names = plan_names(plan, fm)
    if clip.get('map_joined') and '/' in s:
        alias = names['canon'].get(s)
        if alias is None:
            raise Refusal('off_map', 'canonical scene name has no k6 alias')
        d = d or DATASET_OF.get(s.split('/')[0])
        s = alias
        clip = dict(clip, scene=s, dataset=d, canonical=clip['scene'])
    if d is None and clip.get('map_joined'):
        d = names['dataset'].get(s)
        clip = dict(clip, dataset=d)
    if d not in ('d1', 'd2', 'd3'):
        raise Refusal('not_video', str(d))
    m = fm.get((d, s))
    if clip.get('map_joined'):
        if not m:
            raise Refusal('off_map', 'scene absent from the k6 map; its student frames have no pins')
        total = plan['total'].get(s)
        if total is None:
            raise Refusal('off_map', 'scene absent from the k6 frame plan totals')
        fps = fps_authority.get(f'{d}/{s}') or {'d1': 24.0, 'd2': 60.0, 'd3': 10.0}[d]
        if idx[-1] != total - 1:
            raise Refusal('clock_differs', f'last student ordinal {idx[-1]} != k6 total-1 {total - 1}')
        missing = [i for i in idx if i not in m]
        if missing:
            raise Refusal('off_map', f'{len(missing)} student ordinals absent from the k6 map')
        shas = [m[i]['sha256'] for i in idx]
        paths = [m[i]['path'] for i in idx]
        return dict(clip, total=total, fps=fps, sha256=shas, paths=paths)
    return dict(clip, paths=clip.get('paths'))


def plan_clip(clip, fm, plan):
    """Dense plan of one resolved clip. Returns (entry, tasks). Raises Refusal."""
    d, s, total, idx, shas = clip['dataset'], clip['scene'], clip['total'], clip['frame_indices'], clip['sha256']
    if type(total) is not int or total < COUNT:
        raise Refusal('short_clip', f'total {total} < {COUNT}')
    try:
        wanted = nested_indices(total, list(idx), COUNT)
    except ValueError as error:
        raise Refusal('student_set_invalid', str(error))
    m = fm.get((d, s), {})
    plan_total = plan['total'].get(s)
    if m and plan_total is not None and plan_total != total:
        raise Refusal('clock_differs', f'row total {total} != k6 map total {plan_total}: ordinals are on another clock')
    frames, tasks, origin = {}, [], collections.Counter()
    row_pin_differs = 0
    for i, sha in zip(idx, shas):
        if i in m and m[i]['sha256'] != sha:
            row_pin_differs += 1
        frames[i] = dict(source_index=i, sha256=sha, origin='row')
    for i in wanted:
        if i in frames:
            origin['row'] += 1
            continue
        if i in m:
            frames[i] = dict(source_index=i, sha256=m[i]['sha256'], path=m[i]['path'], origin='k6')
            origin['k6'] += 1
            continue
        if d in ('d1', 'd2'):
            v = plan['v'].get(s)
            if v is None:
                raise Refusal('no_decode_source', 'scene has no k6 mp4 decode entry')
            if i >= v['raw_n']:
                raise Refusal('ordinal_past_source', f'ordinal {i} >= mp4 frames {v["raw_n"]}')
            frames[i] = dict(source_index=i, sha256=None, origin='decode')
            tasks.append(('v', s, i))
        else:
            a = plan['a'].get(s)
            if a is None:
                raise Refusal('no_range_source', 'scene has no k6 Apple range-read entry')
            frames[i] = dict(source_index=i, sha256=None, origin='range')
            tasks.append(('a', s, i))
        origin[frames[i]['origin']] += 1
    sig = signature_key(d, s, clip['fps'], total, list(idx), list(shas))
    entry = dict(sig=sig, extract_sig=clip['sig'], dataset=d, scene=s, fps=clip['fps'], total=total, frame_indices=list(idx),
                 student_sha256=list(shas), wanted=wanted, frames=[frames[i] for i in wanted],
                 origin=dict(origin), row_pin_differs_from_k6=row_pin_differs,
                 student_roots=sorted((clip.get('roots') or {}).keys()))
    return entry, tasks


def plan_all(clips, fm, plan, fps_authority):
    entries, refusals, tasks_v, tasks_a = [], [], collections.defaultdict(set), collections.defaultdict(set)
    by_sig = {}
    for clip in clips:
        try:
            resolved = resolve_clip(clip, fm, plan, fps_authority)
            entry, tasks = plan_clip(resolved, fm, plan)
        except Refusal as r:
            refusals.append(dict(sig=clip['sig'], dataset=clip.get('dataset'), scene=clip.get('scene'),
                                 rows=clip.get('rows'), streams=clip.get('streams'), code=r.code, detail=r.detail))
            continue
        seen = by_sig.get(entry['sig'])
        if seen is not None:
            seen['extract_sigs'].append(entry['extract_sig'])
            continue
        entry['extract_sigs'] = [entry['extract_sig']]
        by_sig[entry['sig']] = entry
        entries.append(entry)
        for kind, s, i in tasks:
            (tasks_v if kind == 'v' else tasks_a)[s].add(i)
    return entries, refusals, tasks_v, tasks_a


def decode_manifest(tasks_v, plan, entries=(), every=20):
    """wd.py manifest for the new ScanNet/ScanNet++ frames (k6 conf: mode same, 640x480). Parity ordinals:
    2 student ordinals per scene (all 32 for every `every`-th scene) whose k6 pins the seal compares."""
    student = {}
    for e in entries:
        if e['dataset'] in ('d1', 'd2') and not e['row_pin_differs_from_k6']:
            student.setdefault(e['scene'], e['frame_indices'])
    out, parity = {}, {}
    for n, (s, need) in enumerate(sorted(tasks_v.items())):
        v = plan['v'][s]
        idx = student.get(s, [])
        par = list(idx) if n % every == 0 else ([idx[0], idx[len(idx) // 2]] if idx else [])
        parity[s] = par
        out[s] = dict(g=v['g'], n=v['n'], raw_n=v['raw_n'], need=sorted(set(need) | set(par)))
    return {'v': out, 'parity': parity}


def fetch_plan(tasks_a, plan):
    """wa.py-compatible plan for the new ARKitScenes frames; timestamps are resolved on the host from the
    capture's lowres_wide.traj (row k) because the k6 plan only lists the student ordinals."""
    out = {}
    for s, need in sorted(tasks_a.items()):
        a = plan['a'][s]
        known = {k: (t, f) for k, t, f in a['need']}
        out[s] = dict(u=a['u'], rot=a['rot'], need_ordinals=sorted(need),
                      known=[[k, t, f] for k, (t, f) in sorted(known.items())])
    return out


def cmd_plan(clips_path, map_path, plan_path, fps_path, out):
    os.makedirs(out, exist_ok=True)
    fm = load_map(map_path)
    plan = json.load(gzip.open(plan_path, 'rt'))
    plan.pop('_names', None)
    fps_authority = json.load(open(fps_path)).get('by_scene', {})
    with gzip.open(clips_path, 'rt') as fh:
        clips = [json.loads(line) for line in fh]
    entries, refusals, tasks_v, tasks_a = plan_all(clips, fm, plan, fps_authority)
    with gzip.open(os.path.join(out, 'plan.json.gz'), 'wt') as fh:
        json.dump(entries, fh)
    with gzip.open(os.path.join(out, 'tasks_v.json.gz'), 'wt') as fh:
        json.dump(decode_manifest(tasks_v, plan, entries), fh)
    json.dump(fetch_plan(tasks_a, plan), open(os.path.join(out, 'tasks_a.json'), 'w'))
    json.dump(refusals, open(os.path.join(out, 'refusals.json'), 'w'), indent=0)
    summary = summarize(clips, entries, refusals, tasks_v, tasks_a)
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    return summary


def summarize(clips, entries, refusals, tasks_v, tasks_a):
    by = lambda items, f: dict(collections.Counter(f(x) for x in items))  # noqa: E731
    rows_by = collections.Counter()
    for c in clips:
        for st, n in (c.get('streams') or {}).items():
            rows_by[st] += n
    refused_rows = collections.Counter()
    for r in refusals:
        for st, n in (r.get('streams') or {}).items():
            refused_rows[(r['code'], st)] += n
    origin = collections.Counter()
    for e in entries:
        origin.update(e['origin'])
    return dict(clips=len(clips), planned=len(entries), refused=len(refusals),
                planned_by_dataset=by(entries, lambda e: e['dataset']),
                refused_by_code=by(refusals, lambda r: r['code']),
                refused_rows_by_code_stream={f'{k[0]}|{k[1]}': v for k, v in sorted(refused_rows.items())},
                rows_by_stream=dict(rows_by), frame_origin=dict(origin),
                new_decode_frames=sum(len(v) for v in tasks_v.values()), new_decode_scenes=len(tasks_v),
                new_range_frames=sum(len(v) for v in tasks_a.values()), new_range_captures=len(tasks_a),
                row_pin_differs_from_k6=sum(e['row_pin_differs_from_k6'] for e in entries),
                clips_with_row_pin_differs=sum(1 for e in entries if e['row_pin_differs_from_k6']))


def read_outputs(wd_out, wa_out):
    """{(scene, ordinal): sha256} from wd.py / wa.py result lines; errors and misses are returned."""
    got, problems = {}, []
    for path in (wd_out, wa_out):
        if not path or not os.path.exists(path):
            continue
        for line in open(path):
            r = json.loads(line)
            if 'error' in r:
                problems.append(dict(scene=r['s'], error=r['error']))
                continue
            for f in r['frames']:
                got[(r['s'], f[0])] = f[1]
            for miss in r.get('misses', []):
                problems.append(dict(scene=r['s'], miss=miss))
    return got, problems


def seal(entries, got):
    """Fill new shas, refuse duplicates, key by content. Returns (clips, index, refusals)."""
    clips, index, refusals = {}, {}, []
    for e in entries:
        frames, bad = [], None
        if signature_key(e['dataset'], e['scene'], e['fps'], e['total'], e['frame_indices'], e['student_sha256']) != e['sig']:
            refusals.append(dict(sig=e['sig'], dataset=e['dataset'], scene=e['scene'], code='stale_signature',
                                 detail='the entry no longer matches its row signature'))
            continue
        pins = dict(zip(e['frame_indices'], e['student_sha256']))
        if any(f['source_index'] in pins and f['sha256'] != pins[f['source_index']] for f in e['frames']):
            refusals.append(dict(sig=e['sig'], dataset=e['dataset'], scene=e['scene'], code='student_pin_differs',
                                 detail='a dense frame at a student ordinal is not the row pin'))
            continue
        for f in e['frames']:
            sha = f['sha256'] if f['sha256'] is not None else got.get((e['scene'], f['source_index']))
            if sha is None:
                bad = ('frame_not_produced', f'ordinal {f["source_index"]}')
                break
            path = f.get('path') or logical(NEW_ROOT if f['origin'] in ('decode', 'range') else K6_ROOT, sha)
            frames.append(dict(source_index=f['source_index'], sha256=sha, path=path))
        if bad is None and len({f['sha256'] for f in frames}) != COUNT:
            bad = ('duplicate_content', 'two dense ordinals carry the same bytes')
        if bad is not None:
            refusals.append(dict(sig=e['sig'], dataset=e['dataset'], scene=e['scene'], code=bad[0], detail=bad[1]))
            continue
        key = digest([[f['source_index'], f['sha256']] for f in frames])
        dense = dict(frames=frames, frame_indices=[f['source_index'] for f in frames],
                     timestamps=[f['source_index'] / e['fps'] for f in frames], fps=e['fps'],
                     total_num_frames=e['total'])
        if key in clips and clips[key]['frame_indices'] != dense['frame_indices']:
            raise ValueError('content key collision')
        if key in clips and (clips[key]['fps'], clips[key]['total_num_frames']) != (dense['fps'], dense['total_num_frames']):
            refusals.append(dict(sig=e['sig'], dataset=e['dataset'], scene=e['scene'], code='clock_conflict',
                                 detail='same content as a sealed clip under another fps or frame count'))
            continue
        clips.setdefault(key, dense)
        index[e['sig']] = key
    return clips, index, refusals


def attach(row, sealed):
    """Give a row its dense_source (the tree's r2_dense.build_training input) by clip signature."""
    si = row['student_input']
    sig = signature_key(row.get('dataset'), row.get('scene'), si.get('fps'), si.get('total_num_frames'),
                        si.get('frame_indices'), [f['sha256'] for f in si['frames']])
    key = sealed['index'].get(sig)
    if key is None:
        raise KeyError('no dense clip for this row signature')
    dense = sealed['clips'][key]
    out = dict(row)
    out['student_input'] = dict(si, dense_source=dict(frames=[dict(f) for f in dense['frames']], clip_key=key))
    return out, key


def load_pixel_parity(path):
    """{(scene, ordinal, pinned, fetched): ok} from frame_fetch/bin/dparity.py (pixel rule max|d|<=1, frac<=1e-3)."""
    out = {}
    if path and os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            if not r['byte_equal']:
                out[(r['s'], r['k'], r['pinned'], r['fetched'])] = bool(r['ok'])
    return out


def parity(entries, got, pixel=None):
    """Student ordinals that the host produced again must match their pins: byte-equal, or decoded pixels within
    the dparity.py tolerance. A scene with any other mismatch is held."""
    pixel = pixel or {}
    equal, pixel_ok, differ, observed = 0, 0, [], set()
    for e in entries:
        for i, sha in zip(e['frame_indices'], e['student_sha256']):
            again = got.get((e['scene'], i))
            if again is None:
                continue
            observed.add(e['scene'])
            if again == sha:
                equal += 1
            elif pixel.get((e['scene'], i, sha, again)):
                pixel_ok += 1
            else:
                differ.append(dict(scene=e['scene'], ordinal=i, pinned=sha, fetched=again))
    # A scene that received new frames must have re-produced at least one student frame; no evidence holds it.
    produced = {e['scene'] for e in entries if any(f['origin'] in ('decode', 'range') for f in e['frames'])}
    missing = sorted(produced - observed)
    return dict(checked=equal + pixel_ok + len(differ), equal=equal, pixel_equal=pixel_ok, differ=len(differ),
                differ_list=differ[:200], parity_missing=missing,
                held_scenes=sorted({d['scene'] for d in differ} | set(missing)))


def cmd_seal(out, wd_out, wa_out, sealed_path, pixel_path=None):
    entries = json.load(gzip.open(os.path.join(out, 'plan.json.gz'), 'rt'))
    got, problems = read_outputs(wd_out, wa_out)
    par = parity(entries, got, load_pixel_parity(pixel_path))
    held = set(par['held_scenes'])
    missing = set(par['parity_missing'])
    refusals_held = [dict(sig=e['sig'], dataset=e['dataset'], scene=e['scene'],
                          code='parity_missing' if e['scene'] in missing else 'parity_held',
                          detail='no student frame of this scene was re-produced' if e['scene'] in missing
                          else 'a re-fetched student frame differs from its pin') for e in entries if e['scene'] in held]
    clips, index, refusals = seal([e for e in entries if e['scene'] not in held], got)
    refusals += refusals_held
    value = dict(parity=par, schema='r2-dense-manifest-v1', reconstruct_then_subsample=True, dense_frames=COUNT,
                 rule='student_pilot.dense_eval.nested_indices', clips=clips, index=index,
                 refusals=refusals, fetch_problems=problems[:200], fetch_problem_count=len(problems))
    with open(sealed_path, 'w') as fh:
        json.dump(value, fh, sort_keys=True)
    return dict(clips=len(clips), rows_index=len(index), refusals=len(refusals), problems=len(problems),
                parity={k: v for k, v in par.items() if k != 'differ_list'})


if __name__ == '__main__':
    if sys.argv[1] == 'plan':
        print(json.dumps(cmd_plan(*sys.argv[2:7]), indent=1))
    elif sys.argv[1] == 'seal':
        print(json.dumps(cmd_seal(*sys.argv[2:7])))
    else:
        raise SystemExit(__doc__)
