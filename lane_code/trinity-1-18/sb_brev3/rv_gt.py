"""Independent GT recompute from the pinned rasters.
(a) 200 seeded random rows: in/out of view at frame k, cited sighting frames, every relation clause, the answer.
(b) every delivered row: whether each 'last seen in frame f' citation matches the raster's actual last visible frame before k."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[k] = '1'
import collections as C
import hashlib
import json
import math
import random
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

W = Path('/scratch/jjyeung/orch_n30/sb_brev3')
B3 = Path('/scratch/jjyeung/orch_n30/sb_rowB3')
GT_DIR = Path('/scratch/jjyeung/orch_n30/sb_rowB2/inputs/gt')
FLOOR = 0.002
SAMPLE_SEED = 'sb_brev3|20261119|gt200'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def parse(trace, labels, fam):
    """Per object: (in_view, cited_frame, relation_text) from the object's own step line."""
    out = {}
    for lab in labels:
        name = re.escape('the object labelled "' + lab + '"')
        ls = [l for l in trace.splitlines() if re.match(r'Step \d+: ' + name + ' is ', l)]
        assert len(ls) == 1, (lab, ls)
        l = ls[0]
        m = re.match(r'Step \d+: ' + name + r' is in view in frame (\d+); (.*)\.$', l)
        if m:
            out[lab] = (True, None, int(m[1]), m[2])
            continue
        m = re.match(r'Step \d+: ' + name + r' is out of view in frame (\d+); it was last seen in frame (\d+) \(([^)]*)\); (.*)\.$', l)
        assert m, l
        out[lab] = (False, int(m[2]), int(m[1]), m[4], m[3])
    return out


def one_raster(args):
    path, digest, rows, full = args
    assert sha(path) == digest
    res = []
    with np.load(path, allow_pickle=False) as z:
        inst = z['inst']
        c2w = z['c2w'].astype(float)
        ids = [int(x) for x in z['ids']]
        labels_gt = [str(x).strip().lower() for x in z['labels']]
        cen = z['obb_centroid'].astype(float)
        axes = z['obb_axes'].astype(float)
        lens = z['obb_lengths'].astype(float)
        valid = np.asarray(z['valid'], bool) & (z['depth'] > 0).any(axis=(1, 2))
        findex = [int(x) for x in z['frame_indices']]
        down = np.median(c2w[valid, :3, 1], axis=0)
    for r in rows:
        p = r['provenance']
        fam = r['question_type']
        q = r['student_input']['question']
        k = int(re.search(r'frame (\d+) of 32', q)[1])
        rec = dict(qid=r['qid'], fam=fam, full=full, k_matches_provenance=k == p['camera_frame'],
                   frames_match=findex == r['student_input']['frame_indices'], k_valid=bool(valid[k - 1]))
        labels = [o['label'] for o in p['instances']]
        idof = {o['label']: o['id'] for o in p['instances']}
        rec['labels_match_raster'] = all(labels_gt[ids.index(idof[l])] == l for l in labels)
        shares = {l: (inst == idof[l]).reshape(32, -1).mean(axis=1) for l in labels}
        claims = parse(r['target'], labels, fam)
        cit = []
        for l in labels:
            s = shares[l]
            in_view = bool(s[k - 1] >= FLOOR)
            c = claims[l]
            d = dict(label=l, in_view_true=in_view, in_view_claim=c[0], k_in_line=c[2] == k)
            if not c[0]:
                f = c[1]
                vis = [i + 1 for i in range(32) if s[i] >= FLOOR]
                vis_valid = [i + 1 for i in range(32) if s[i] >= FLOOR and valid[i]]
                before = [i for i in vis if i < k]
                d.update(cited=f, cited_visible=bool(1 <= f <= 32 and s[f - 1] >= FLOOR), future=f > k,
                         true_last_before_k=max(before) if before else None,
                         true_last_before_k_valid=max([i for i in vis_valid if i < k], default=None),
                         visible_frames_between=len([i for i in vis if f < i < k]),
                         rule_text=c[4])
            cit.append(d)
        rec['objects'] = cit
        if full:
            pose = c2w[k - 1]
            cam = pose[:3, 3]
            R = pose[:3, :3]
            up = np.asarray(p['geometry_audit']['up'], float)
            rec['up_axis_aligned'] = bool(np.isclose(np.abs(up).max(), 1) and np.isclose(np.abs(up).sum(), 1))
            rec['up_opposes_image_down'] = bool(float(down @ up) < 0)
            vals = {}
            front = {}
            for l in labels:
                j = ids.index(idof[l])
                ax = axes[j].reshape(3, 3)
                if p['geometry_audit']['axes_layout'] == 'columns':
                    ax = ax.T
                half = lens[j] * p['geometry_audit']['box_half_factor']
                local = ax @ (cam - cen[j])
                dist = float(np.linalg.norm(np.maximum(np.abs(local) - half, 0)))
                pc = np.linalg.solve(R, cen[j] - cam)
                bear = math.atan2(pc[0], pc[2])
                height = float(cen[j] @ up)
                front[l] = pc[2] > 0
                vals[l] = dist if (fam.startswith('camera_') or fam.endswith('_nf')) else bear if fam.endswith('_lr') else height
            gv = p['geometry_values']
            if fam.startswith('camera_'):
                order = sorted(labels, key=vals.get)
                rec['values_match_provenance'] = bool(np.allclose(sorted(vals.values()), gv, rtol=1e-5, atol=1e-5))
                sem = order[0]
                rec['min_adjacent_gap_m'] = min(vals[b] - vals[a] for a, b in zip(order, order[1:]))
                rel_ok = True
                for l in labels:
                    i = order.index(l)
                    t = claims[l][3]
                    want = []
                    if i > 0:
                        want.append('farther than the ' + order[i - 1])
                    if i + 1 < len(order):
                        want.append('nearer than the ' + order[i + 1])
                    rel_ok &= t == 'relative to that camera, its closest point is ' + ' and '.join(want)
                rel_ok &= ('the objects are ' + ', then '.join(order) + '.') in r['target']
                rel_ok &= ('So the closest object to that camera is the ' + sem + '.') in r['target']
            else:
                a, b = labels
                rec['values_match_provenance'] = bool(np.allclose([vals[a], vals[b]], gv, rtol=1e-5, atol=1e-5))
                if fam.endswith('_nf'):
                    sem = 'Near' if vals[a] < vals[b] else 'Far'
                    word = lambda x, y: 'relative to that camera, its closest point is ' + ('nearer' if vals[x] < vals[y] else 'farther') + ' than the closest point of the ' + y
                    final = f'So relative to that camera, the closest point of the {a} is {"nearer" if sem == "Near" else "farther"} than the closest point of the {b}.'
                elif fam.endswith('_lr'):
                    sem = 'Left' if vals[a] < vals[b] else 'Right'
                    rec['both_in_front'] = bool(front[a] and front[b])
                    word = lambda x, y: 'from that camera viewpoint, its centre is to the ' + ('left' if vals[x] < vals[y] else 'right') + ' of the centre of the ' + y
                    final = f'So from that camera viewpoint, the centre of the {a} is to the {sem.lower()} of the centre of the {b}.'
                else:
                    sem = 'Up' if vals[a] > vals[b] else 'Down'
                    word = lambda x, y: "in that camera's level horizon, its centre is " + ('higher' if vals[x] > vals[y] else 'lower') + ' than the centre of the ' + y
                    final = f"So the centre of the {a} is {'higher' if sem == 'Up' else 'lower'} than the centre of the {b} in that camera's level horizon."
                rel_ok = claims[a][3] == word(a, b) and claims[b][3] == word(b, a) and final in r['target']
            ans = r['student_input']['options'][ord(r['answer']) - 65].split('. ', 1)[1]
            rec.update(answer_true=sem, answer_row=ans, answer_ok=ans == sem, relations_ok=bool(rel_ok),
                       target_ends_with_answer=r['target'].endswith('</think>\n\n' + r['answer']))
        res.append(rec)
    return res


def main():
    rows = [json.loads(s) for s in (B3 / 'out/rows.jsonl').read_text().splitlines()]
    order = sorted(r['qid'] for r in rows)
    sample = set(random.Random(SAMPLE_SEED).sample(order, 200))
    groups = C.defaultdict(list)
    for r in rows:
        groups[r['provenance']['raster_sha256']].append(r)
    jobs = []
    for h, rr in groups.items():
        p = GT_DIR / (h + '.npz')
        jobs.append((str(p), h, rr, None))
    tasks = []
    for path, h, rr, _ in jobs:
        tasks.append((path, h, [r for r in rr if r['qid'] in sample], True))
        tasks.append((path, h, [r for r in rr if r['qid'] not in sample], False))
    tasks = [t for t in tasks if t[2]]
    recs = []
    with ProcessPoolExecutor(16) as ex:
        for out in ex.map(one_raster, tasks, chunksize=4):
            recs += out
    assert len(recs) == len(rows)
    full = [r for r in recs if r['full']]
    assert len(full) == 200
    s = C.Counter()
    for r in full:
        for key in ('k_matches_provenance', 'frames_match', 'k_valid', 'labels_match_raster', 'up_axis_aligned', 'up_opposes_image_down',
                    'values_match_provenance', 'answer_ok', 'relations_ok', 'target_ends_with_answer'):
            s[key + ('_ok' if r[key] else '_FAIL')] += 1
        if 'both_in_front' in r:
            s['lr_both_in_front_' + str(r['both_in_front'])] += 1
        for o in r['objects']:
            s['objects'] += 1
            s['visibility_claim_' + ('ok' if o['in_view_true'] == o['in_view_claim'] else 'FAIL')] += 1
            if not o['in_view_claim']:
                s['out_objects'] += 1
                s['cited_frame_visible_' + str(o['cited_visible'])] += 1
                s['cited_is_true_last_before_k_' + str(o['cited'] == o['true_last_before_k'])] += 1
                s['cited_future_' + str(o['future'])] += 1
    s200 = dict(sorted(s.items()))
    s200['rows_with_any_wrong_last_seen'] = sum(any((not o['in_view_claim']) and o['cited'] != o['true_last_before_k'] for o in r['objects']) for r in full)
    s200['min_camera_adjacent_gap_m'] = min(r['min_adjacent_gap_m'] for r in full if 'min_adjacent_gap_m' in r)
    s200['by_family'] = dict(C.Counter(r['fam'] for r in full))
    # population citation stats
    pop = C.Counter()
    fam_rows_bad = C.Counter()
    fam_rows = C.Counter()
    examples = []
    for r in recs:
        fam_rows[r['fam']] += 1
        bad = False
        for o in r['objects']:
            pop['objects'] += 1
            pop['visibility_' + ('ok' if o['in_view_true'] == o['in_view_claim'] else 'FAIL')] += 1
            if o['in_view_claim']:
                continue
            pop['out_of_view_objects'] += 1
            if o['future']:
                pop['cited_future_frame'] += 1
                pop['cited_future_but_visible_before_k'] += o['true_last_before_k'] is not None
                bad = True
            elif o['cited'] == o['true_last_before_k']:
                pop['cited_past_correct'] += 1
            else:
                pop['cited_past_wrong'] += 1
                pop['cited_past_wrong_gap_frames'] += o['true_last_before_k'] - o['cited']
                bad = True
                if len(examples) < 5:
                    examples.append(dict(qid=r['qid'], label=o['label'], cited=o['cited'], true_last_before_k=o['true_last_before_k'],
                                         visible_frames_between=o['visible_frames_between']))
            pop['cited_visible_' + str(o['cited_visible'])] += 1
            pop['valid_mask_changes_last_seen'] += o['true_last_before_k'] != o['true_last_before_k_valid']
        fam_rows_bad[r['fam']] += bad
    pop['rows'] = len(recs)
    pop['rows_with_false_last_seen_statement'] = sum(fam_rows_bad.values())
    pop = dict(pop)
    pop['mean_gap_when_wrong'] = round(pop.get('cited_past_wrong_gap_frames', 0) / max(1, pop.get('cited_past_wrong', 0)), 2)
    pop['rows_with_false_last_seen_by_family'] = {f: f'{fam_rows_bad[f]}/{fam_rows[f]}' for f in sorted(fam_rows)}
    result = dict(sample_seed=SAMPLE_SEED, sample_qids=sorted(sample), sample200=s200, population=pop, examples=examples,
                  rasters=len(groups), script_sha256=sha(__file__), rows_sha256=sha(B3 / 'out/rows.jsonl'),
                  failures=[r for r in full if not (r['answer_ok'] and r['relations_ok'] and r['values_match_provenance'])][:5])
    (W / 'out/RV_GT.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(sample200=s200, population=pop, examples=examples), indent=1))


if __name__ == '__main__':
    main()
