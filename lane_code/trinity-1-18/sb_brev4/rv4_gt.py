"""Independent GT recompute from the pinned rasters for sb_rowB4.
(a) every delivered row: in/out of view at k for every object, and every sighting citation against the raster
    (past: latest frame before k with share >= floor; none before k: first visible frame after k), every frame mention accounted for;
(b) 200 seeded random rows: additionally geometry, every relation clause and the answer."""
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

W = Path('/scratch/jjyeung/orch_n30/sb_brev4')
B4 = Path('/scratch/jjyeung/orch_n30/sb_rowB4')
GT_DIR = Path('/scratch/jjyeung/orch_n30/sb_rowB2/inputs/gt')
FLOOR = 0.002
SAMPLE_SEED = 'sb_brev4|20261119|gt200'
WORKERS = 6


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def parse(trace, labels):
    """Per object: in_view, k in its line, past citation, future citation (f, k), relation text. Raises on any grammar surprise."""
    steps = re.findall(r'^Step (\d+): (.*)$', trace, re.M)
    numbering_ok = [int(n) for n, _ in steps] == list(range(1, len(steps) + 1))
    out = {}
    for lab in labels:
        name = re.escape('the object labelled "' + lab + '"')
        ls = [(int(n), b) for n, b in steps if re.match(name + ' is ', b)]
        assert len(ls) == 1, (lab, ls)
        n, b = ls[0]
        d = dict(step=n, past=None, future=None)
        m = re.match(name + r' is in view in frame (\d+); (.*)\.$', b)
        if m:
            d.update(in_view=True, k=int(m[1]), rel=m[2])
        else:
            m = re.match(name + r' is out of view in frame (\d+); it was last seen in frame (\d+); (.*)\.$', b)
            if m:
                d.update(in_view=False, k=int(m[1]), past=int(m[2]), rel=m[3])
            else:
                m = re.match(name + r' is out of view in frame (\d+); (.*)\.$', b)
                assert m, b
                d.update(in_view=False, k=int(m[1]), rel=m[2])
        fut = [(int(n2), b2) for n2, b2 in steps if b2.startswith('for the object instance labelled "' + lab + '", ')]
        assert len(fut) <= 1, fut
        if fut:
            n2, b2 = fut[0]
            m2 = re.match(r'for the object instance labelled "' + re.escape(lab) + r'", it first appears in frame (\d+), after frame (\d+)\.$', b2)
            assert m2, b2
            d['future'] = (int(m2[1]), int(m2[2]))
            d['future_step_follows'] = n2 == n + 1
        out[lab] = d
    return out, numbering_ok, len(steps)


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
    flat = inst.reshape(32, -1)
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
        shares = {l: (flat == idof[l]).mean(axis=1) for l in labels}
        claims, numbering_ok, nsteps = parse(r['target'], labels)
        rec['numbering_ok'] = numbering_ok
        rec['step1_ok'] = r['target'].startswith(f'<think>\nStep 1: take the camera viewpoint of frame {k} of 32.')
        expected_mentions = C.Counter([k])
        cit = []
        for l in labels:
            s = shares[l]
            c = claims[l]
            vis = [i + 1 for i in range(32) if s[i] >= FLOOR]
            before = [i for i in vis if i < k]
            after = [i for i in vis if i > k]
            d = dict(label=l, in_view_true=bool(s[k - 1] >= FLOOR), in_view_claim=c['in_view'], k_in_line=c['k'] == k,
                     never_visible=not vis, past=c['past'], future=c['future'],
                     true_last_before_k=max(before) if before else None, true_first_after_k=min(after) if after else None,
                     last_before_k_valid=max([i for i in before if valid[i - 1]], default=None))
            expected_mentions[k] += 1
            if c['past'] is not None:
                expected_mentions[c['past']] += 1
            if c['future'] is not None:
                expected_mentions[c['future'][0]] += 1
                expected_mentions[c['future'][1]] += 1
                d['future_step_follows'] = c['future_step_follows']
            if d['in_view_claim']:
                d['citation_ok'] = c['past'] is None and c['future'] is None
                d['kind'] = 'in_view'
            elif before:
                d['kind'] = 'past'
                d['citation_ok'] = c['past'] == max(before) and c['future'] is None
            else:
                d['kind'] = 'future'
                d['citation_ok'] = c['past'] is None and c['future'] is not None and bool(after) and c['future'] == (min(after), k)
            cit.append(d)
        rec['objects'] = cit
        rec['frame_mentions_accounted'] = C.Counter(int(x) for x in re.findall(r'frame (\d+)', r['target'])) == expected_mentions
        rec['all_mentions_in_1_32'] = all(1 <= int(x) <= 32 for x in re.findall(r'frame (\d+)', r['target']))
        ev = p['sb_rowB4']['visibility']
        rec['provenance_visibility_matches'] = all(
            ev[o['label']]['in_view'] == o['in_view_true'] and (o['in_view_true'] or ev[o['label']]['recorded_frame'] ==
                                                                 (o['true_last_before_k'] if o['kind'] == 'past' else o['true_first_after_k']))
            for o in cit)
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
                    want = []
                    if i > 0:
                        want.append('farther than the ' + order[i - 1])
                    if i + 1 < len(order):
                        want.append('nearer than the ' + order[i + 1])
                    rel_ok &= claims[l]['rel'] == 'relative to that camera, its closest point is ' + ' and '.join(want)
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
                rel_ok = claims[a]['rel'] == word(a, b) and claims[b]['rel'] == word(b, a) and final in r['target']
            ans = r['student_input']['options'][ord(r['answer']) - 65].split('. ', 1)[1]
            rec.update(answer_true=sem, answer_row=ans, answer_ok=ans == sem, relations_ok=bool(rel_ok),
                       target_ends_with_answer=r['target'].endswith('</think>\n\n' + r['answer']))
        res.append(rec)
    return res


def main():
    rows = [json.loads(s) for s in (B4 / 'out/rows.jsonl').read_text().splitlines()]
    sample = set(random.Random(SAMPLE_SEED).sample(sorted(r['qid'] for r in rows), 200))
    groups = C.defaultdict(list)
    for r in rows:
        groups[r['provenance']['raster_sha256']].append(r)
    tasks = []
    for h, rr in groups.items():
        p = str(GT_DIR / (h + '.npz'))
        for full in (True, False):
            sub = [r for r in rr if (r['qid'] in sample) == full]
            if sub:
                tasks.append((p, h, sub, full))
    recs = []
    with ProcessPoolExecutor(WORKERS) as ex:
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
            s['visibility_' + ('ok' if o['in_view_true'] == o['in_view_claim'] else 'FAIL')] += 1
            s['citation_' + ('ok' if o['citation_ok'] else 'FAIL')] += 1
    s200 = dict(sorted(s.items()))
    s200['min_camera_adjacent_gap_m'] = min(r['min_adjacent_gap_m'] for r in full if 'min_adjacent_gap_m' in r)
    s200['by_family'] = dict(C.Counter(r['fam'] for r in full))
    pop = C.Counter()
    fam_bad = C.Counter()
    fam_rows = C.Counter()
    examples = []
    for r in recs:
        fam_rows[r['fam']] += 1
        for key in ('k_matches_provenance', 'frames_match', 'k_valid', 'labels_match_raster', 'numbering_ok', 'step1_ok',
                    'frame_mentions_accounted', 'all_mentions_in_1_32', 'provenance_visibility_matches'):
            pop[key + ('_ok' if r[key] else '_FAIL')] += 1
        bad = False
        for o in r['objects']:
            pop['objects'] += 1
            pop['visibility_' + ('ok' if o['in_view_true'] == o['in_view_claim'] else 'FAIL')] += 1
            pop['never_visible'] += o['never_visible']
            if o['in_view_claim'] != o['in_view_true']:
                bad = True
            if o['in_view_claim']:
                pop['in_view_with_citation'] += not o['citation_ok']
                continue
            pop['out_of_view_references'] += 1
            pop['citations_' + o['kind']] += 1
            pop['citations_' + o['kind'] + ('_ok' if o['citation_ok'] else '_FALSE')] += 1
            if o['kind'] == 'past':
                pop['past_object_also_visible_after_k'] += o['true_first_after_k'] is not None
                pop['past_valid_mask_would_change_frame'] += o['last_before_k_valid'] != o['true_last_before_k']
            else:
                pop['future_step_directly_follows'] += o.get('future_step_follows', False)
            if not o['citation_ok']:
                bad = True
                if len(examples) < 5:
                    examples.append(dict(qid=r['qid'], **{k: o[k] for k in ('label', 'kind', 'past', 'future', 'true_last_before_k', 'true_first_after_k')}))
        fam_bad[r['fam']] += bad
    pop['rows'] = len(recs)
    pop['rows_with_any_false_visibility_or_citation'] = sum(fam_bad.values())
    pop = dict(sorted(pop.items()))
    pop['by_family_rows_bad'] = {f: f'{fam_bad[f]}/{fam_rows[f]}' for f in sorted(fam_rows)}
    result = dict(sample_seed=SAMPLE_SEED, sample_qids=sorted(sample), sample200=s200, population=pop, examples=examples,
                  rasters=len(groups), script_sha256=sha(__file__), rows_sha256=sha(B4 / 'out/rows.jsonl'),
                  failures=[{k: v for k, v in r.items() if k != 'objects'} for r in full
                            if not (r['answer_ok'] and r['relations_ok'] and r['values_match_provenance'])][:5])
    (W / 'out/RV4_GT.json').write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + '\n')
    print(json.dumps(dict(sample200=s200, population=pop, examples=examples), indent=1, default=str))


if __name__ == '__main__':
    main()
