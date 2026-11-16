"""Metadata-only extraction of row clips from pinned row stores (no RGB read).

usage: python -I extract_meta.py SPEC.json OUT_DIR
SPEC: {"sources": [{"name": str, "stream": "vqa|routing|pointing|pose",
                    "kind": "sqlite" | "sqlite_parts" | "sqlite_tar" | "jsonl_gz_tar" | "jsonl",
                    "paths": [...], "member": str (tar kinds), "pose_prefix": str|null (pose only),
                    "limit": int|null}]}
Writes OUT_DIR/clips.jsonl.gz (one line per distinct clip signature), OUT_DIR/rows.jsonl.gz (one line per
row: source, stream, qid, dataset, scene, category, sig, selected), OUT_DIR/summary.json.
A clip signature is sha256 over (dataset, scene, fps, total, frame_indices, frame sha256s); paths are not
part of it (content identity never includes a path), but the distinct path roots seen are recorded.
Requires sqlro.py beside this file. Stdlib only (numpy not needed: the pose filter is reimplemented).
"""
import gzip
import hashlib
import json
import math
import os
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sqlro  # noqa: E402


def dense_pose_row(row, target):
    """Same predicate as student_pilot.carrier_c1_sweep.dense_pose_row, without numpy."""
    sample = row.get('pose_sample', {})
    mask = target.get('camera_mask', [])
    camera = target.get('camera', [])
    return (row.get('category') == 'camera_pose_only'
            and sample.get('recording', {}).get('sampling', {}).get('variant') == 'all_frames32'
            and len(row.get('student_input', {}).get('frames', [])) == 32
            and isinstance(mask, list) and len(mask) == 32 and all(bool(m) for m in mask)
            and isinstance(camera, list) and len(camera) == 32
            and all(isinstance(c, list) and len(c) == 9 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in c)
                    for c in camera))


DATASET_OF = {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}


def cat(row):
    value = row.get('question_type') or row.get('type') or row.get('category')
    return None if value is None else hashlib.sha1(str(value).encode()).hexdigest()[:10]


def root_of(path):
    parts = path.split('/')
    return '/'.join(parts[:3]) if len(parts) > 3 else path


def signature(row):
    si = row.get('student_input') or {}
    frames = si.get('frames') or []
    key = [row.get('dataset'), row.get('scene'), si.get('fps'), si.get('total_num_frames'),
           si.get('frame_indices'), [f.get('sha256') for f in frames]]
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest(), key


def records(src):
    kind, paths = src['kind'], src['paths']
    if kind in ('sqlite', 'sqlite_parts'):
        store = sqlro.Store(sqlro.SplitFile(paths))
    elif kind == 'sqlite_tar':
        off, size = sqlro.tar_member(paths[0], src['member'])
        store = sqlro.Store(sqlro.SplitFile(paths, off, size))
    elif kind == 'jsonl_gz_tar':
        with tarfile.open(paths[0], 'r:') as t:
            for m in t:
                if m.isfile() and m.name.endswith('.jsonl.gz') and (not src.get('member') or m.name == src['member']):
                    with gzip.open(t.extractfile(m), 'rt') as fh:
                        for line in fh:
                            yield json.loads(line), {}, m.name
        return
    elif kind == 'jsonl':
        for p in paths:
            with (gzip.open(p, 'rt') if p.endswith('.gz') else open(p)) as fh:
                for line in fh:
                    yield json.loads(line), {}, os.path.basename(p)
        return
    else:
        raise ValueError('unknown kind ' + kind)
    cols = None
    for rowid, vals in store.rows(src.get('table', 'rows')):
        row = json.loads(vals[1])
        target = json.loads(vals[2]) if len(vals) > 2 and isinstance(vals[2], str) and src['stream'] == 'pose' else {}
        yield row, target, None


def main():
    spec, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    clips, summary = {}, {'sources': {}, 'started': time.time()}
    with gzip.open(os.path.join(out, 'rows.jsonl.gz'), 'wt') as rows_out:
        for src in spec['sources']:
            t0, n, sel, nosi = time.time(), 0, 0, 0
            for row, target, member in records(src):
                if src.get('limit') and n >= src['limit']:
                    break
                n += 1
                si = row.get('student_input')
                selected = True
                if src['stream'] == 'pose':
                    selected = dense_pose_row(row, target)
                    pre = src.get('pose_prefix')
                    if selected and pre is not None:
                        selected = all(f['path'].startswith(pre) for f in si['frames'])
                fi = row.get('frame_indices') if isinstance(row.get('frame_indices'), list) else (si or {}).get('frame_indices')
                if (not isinstance(si, dict) or not si.get('frames')) and isinstance(fi, list):
                    ds = row.get('dataset') or DATASET_OF.get(str(row.get('canonical', '')).split('/')[0])
                    key = [ds, row.get('scene'), None, None, fi, None]
                    sig = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
                    c = clips.get(sig)
                    if c is None:
                        c = clips[sig] = dict(sig=sig, dataset=ds, scene=key[1], fps=None, total=None,
                                              frame_indices=key[4], sha256=None, roots={}, rows=0, streams={},
                                              map_joined=True)
                    c['rows'] += 1
                    c['streams'][src['stream']] = c['streams'].get(src['stream'], 0) + 1
                    sel += selected
                    rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                                   dataset=ds, scene=row.get('scene'), category=cat(row),
                                                   member=member, sig=sig, selected=selected, map_joined=True)) + '\n')
                    continue
                if not isinstance(si, dict) or not si.get('frames'):
                    nosi += 1
                    rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                                   dataset=row.get('dataset'), scene=row.get('scene'),
                                                   category=cat(row),
                                                   member=member, sig=None, selected=selected)) + '\n')
                    continue
                sig, key = signature(row)
                c = clips.get(sig)
                if c is None:
                    c = clips[sig] = dict(sig=sig, dataset=key[0], scene=key[1], fps=key[2], total=key[3],
                                          frame_indices=key[4], sha256=key[5], roots={}, rows=0, streams={})
                c['rows'] += 1
                c['streams'][src['stream']] = c['streams'].get(src['stream'], 0) + 1
                for f in si['frames']:
                    r = root_of(f['path'])
                    c['roots'][r] = c['roots'].get(r, 0) + 1
                if src['stream'] == 'pose':
                    c.setdefault('paths', [f['path'] for f in si['frames']])
                sel += selected
                rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                               dataset=row.get('dataset'), scene=row.get('scene'),
                                               category=cat(row),
                                               member=member, sig=sig, selected=selected)) + '\n')
            summary['sources'][src['name']] = dict(rows=n, selected=sel, without_student_input=nosi,
                                                   seconds=round(time.time() - t0, 1))
            print(json.dumps({src['name']: summary['sources'][src['name']]}), flush=True)
    with gzip.open(os.path.join(out, 'clips.jsonl.gz'), 'wt') as fh:
        for c in clips.values():
            fh.write(json.dumps(c, sort_keys=True) + '\n')
    summary['clips'] = len(clips)
    summary['finished'] = time.time()
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    print('END', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
