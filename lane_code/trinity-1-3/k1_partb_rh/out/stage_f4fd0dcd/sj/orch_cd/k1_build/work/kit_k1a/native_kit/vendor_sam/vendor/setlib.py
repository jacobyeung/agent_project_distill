"""Set selection from the build table: accept per candidate, 3D identity merge, and member-level set metrics.

Accept: every candidate with p >= tau; a named object always exists, so the best candidate is accepted when none
passes. Merge (label-free): union of accepted candidates of one name whose tower centres lie within R metres,
unless both hold a different SAM 3 instance on one frame (cannot-link: distinct instances in that frame).
Within a merged instance a frame keeps one member (highest candidate p, then SAM 3 score).
Metrics (scoring only, from member GT matches at IoU > 0.5): per-frame instance recall over GT frame-instances
(>= min_px), precision of kept members (one-to-one: a second member on an already matched (frame, GT) is false),
identity purity of merged instances and the count error against GT instances seen."""
import json
from collections import defaultdict

import numpy as np

SAM3 = ['peak', 'logit_peak', 'support', 'n_members', 'exclusivity_margin', 'inst_score_mean', 'inst_score_max',
        'log_area_mean', 'log_area_max', 'sam_presence_members']
GEO3D = ['has_3d', 'member_spread_m', 'multi_view_3d', 'log_extent_max', 'log_extent_mid', 'reproj_vis', 'reproj_vis_other',
         'reproj_det', 'reproj_det_ratio', 'reproj_hit_score', 'dist_to_top_m', 'n_dupes_05m']
SETF = ['n_cands_name', 'peak_rank', 'peak_rank_frac', 'peak_rel', 'coverage', 'log_members']
STUDENT = ['model_pyes_members', 'model_pyes_members_max', 'box_iou_mean', 'box_iou_max', 'box_iou_weighted',
           'reproj_box', 'reproj_box_ratio']
GROUPS = dict(sam3=SAM3, geo3d=GEO3D, set=SETF, student=STUDENT, prior=['name_prior'])
FEATS = dict(portable=SAM3+GEO3D+SETF+['name_prior'], full=SAM3+GEO3D+SETF+STUDENT+['name_prior'],
             portable_np=SAM3+GEO3D+SETF, full_np=SAM3+GEO3D+SETF+STUDENT)
SWEEP_TAU = (.05, .1, .15, .2, .3, .4, .5, .6)
SWEEP_MERGE = (('heur', None), ('lm', .1), ('lm', .2), ('lm', .3), ('lm', .5), ('lm', .7), ('lm_nb', .3), ('lm_nb', .5))
PFEATS = ['has_c', 'd_c', 'd_rel', 'ext_max', 'ext_min', 'box_iou3d', 'box_ov3d', 'n_shared', 'shared_frac', 'iou2d_max',
          'iou2d_mean', 'ov2d_max', 'ov2d_mean', 'n_disjoint', 'disjoint_frac', 'n_union', 'reproj_max', 'reproj_min',
          'peak_max', 'peak_min', 'logm_max', 'logm_min']


def load(path):
    objs, cands = {}, defaultdict(list)
    for line in open(path):
        r = json.loads(line)
        if r['kind'] == 'object':
            objs[r['object_id']] = r
        else:
            cands[r['object_id']].append(r)
    return objs, cands


def room(scene):
    return scene.rsplit('_', 1)[0]


def name_prior(train_cands, alpha=5.):
    """Per-name positive rate from training rooms only, shrunk to the global rate."""
    pos, n = defaultdict(float), defaultdict(float)
    for r in train_cands:
        pos[r['name'].lower()] += r['y']
        n[r['name'].lower()] += 1
    g = sum(pos.values())/max(sum(n.values()), 1)
    return lambda name: (pos.get(name.lower(), 0.)+alpha*g)/(n.get(name.lower(), 0.)+alpha), g


def accept(cs, p, tau):
    acc = [c for c in cs if p[c['candidate_id']] >= tau]
    if not acc and cs:
        acc = [max(cs, key=lambda c: (p[c['candidate_id']], c['features']['peak']))]
    return acc


def merge(acc, p, radius=0.5, centre=lambda c: c.get('centre')):
    """Union-find over accepted candidates; returns list of instances = lists of candidates."""
    n = len(acc)
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    slots = [{m['slot']: m['ii'] for m in c['members']} for c in acc]
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            a, b = centre(acc[i]), centre(acc[j])
            if a is None or b is None:
                continue
            d = float(np.linalg.norm(np.asarray(a)-np.asarray(b)))
            r = radius if radius != 'adaptive' else .3+.5*max(np.exp(acc[i]['features']['log_extent_max']), np.exp(acc[j]['features']['log_extent_max']))
            if d < r:
                pairs.append((d, i, j))
    groups = {i: {i} for i in range(n)}
    for d, i, j in sorted(pairs):
        ri, rj = find(i), find(j)
        if ri == rj:
            continue
        conflict = any(s in slots[b] and slots[b][s] != slots[a][s] for a in groups[ri] for b in groups[rj] for s in slots[a])
        if conflict:
            continue
        par[rj] = ri
        groups[ri] |= groups.pop(rj)
    order = sorted(groups.values(), key=lambda g: -max(p[acc[i]['candidate_id']] for i in g))
    return [[acc[i] for i in sorted(g, key=lambda i: -p[acc[i]['candidate_id']])] for g in order]


def merge_learned(ids, psame, thr=.5, blocked=lambda i, j: False):
    """Average-linkage agglomeration of candidate ids on the learned P(same object): repeatedly join the two groups
    with the highest mean cross-pair P while it is >= thr; a group pair holding a blocked pair never joins.
    psame(i, j) -> probability (missing pairs count as 0). Returns groups as lists of ids, original order kept."""
    groups = [[i] for i in ids]
    P = {(i, j): psame(i, j) for a, i in enumerate(ids) for j in ids[a+1:]}
    P.update({(j, i): v for (i, j), v in list(P.items())})
    while len(groups) > 1:
        best, bi, bj = -1., -1, -1
        for a in range(len(groups)):
            for b in range(a+1, len(groups)):
                if any(blocked(i, j) for i in groups[a] for j in groups[b]):
                    continue
                v = float(np.mean([P[(i, j)] for i in groups[a] for j in groups[b]]))
                if v > best:
                    best, bi, bj = v, a, b
        if best < thr:
            break
        groups[bi] += groups.pop(bj)
    order = {i: n for n, i in enumerate(ids)}
    return [sorted(g, key=order.get) for g in groups]


def instance_members(inst, p):
    """One member per frame within an instance: highest candidate p, then SAM 3 score."""
    best = {}
    for c in inst:
        for m in c['members']:
            key = (p[c['candidate_id']], m['score'])
            if m['slot'] not in best or key > best[m['slot']][0]:
                best[m['slot']] = (key, m)
    return [m for _, m in sorted(best.values(), key=lambda t: t[1]['slot'])]


def object_metrics(obj, instances, min_px=39):
    gtfi = {(int(k), i) for k, v in obj['gt_frames'].items() for i, px in v if px >= min_px}
    tp, kept, seen = set(), 0, set()
    purity_num = purity_den = 0
    for inst in instances:
        gids = []
        for m in inst:
            kept += 1
            key = (m['slot'], m['gid'])
            if m['gid'] >= 0 and key not in seen:
                seen.add(key)
                if key in gtfi:
                    tp.add(key)
            if m['gid'] >= 0:
                gids.append(m['gid'])
        if gids:
            purity_num += max(gids.count(g) for g in set(gids))
            purity_den += len(gids)
    fp = kept-len(seen)
    n_gt = len({i for _, i in gtfi})
    insts_with_hit = sum(any(m['gid'] >= 0 for m in inst) for inst in instances)
    split = defaultdict(set)
    for j, inst in enumerate(instances):
        for m in inst:
            if m['gid'] >= 0:
                split[m['gid']].add(j)
    return dict(gt=len(gtfi), tp=len(tp), kept=kept, true_kept=len(seen), fp=fp, purity_num=purity_num,
                purity_den=purity_den, n_inst=len(instances), n_gt_inst=n_gt, n_inst_hit=insts_with_hit,
                n_split=sum(len(v) > 1 for v in split.values()), count_exact=int(len(instances) == n_gt))


def flat(insts):
    return [m for inst in insts for m in inst]
