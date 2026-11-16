"""Shared loaders, the benchmark's own box sampler, scoring and paired scene-cluster bootstrap."""
import collections
import json
import re
import sys

import numpy as np

import tplib as T  # noqa: E402

W = '/scratch/jjyeung/orch_cd/gt_ceiling/work'
VSI_FULL = '/scratch/jjyeung/orch_cd/aws_32/a_build/eval/orchard_bin/cp4tk_eval/official/meta_5130.jsonl'
VSTI_FULL = f'{W}/data/vstibench_test.json'
META = '/scratch/jjyeung/orch_cd/toolprog/work/meta_info/%s_meta_info_val.json'
GTNPZ = '/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet/%s.npz'
D_VSI = '/scratch/jjyeung/orch_cd/official_reads/ref/8d19426a_final_official5130_native.per_question_scores.jsonl'
D_VSTI = '/scratch/jjyeung/orch_cd/official_reads/ref/8d19426a_arm_vstiv3.items.json'


def vsi_items():
    return [json.loads(l) for l in open(VSI_FULL)]


def vsti_items():
    out = []
    for q in json.load(open(VSTI_FULL)):
        q = dict(q, dataset='scannet', scene_name=q['video_path'].split('/')[-1][:-4], options=q.get('options') or [])
        q['ground_truth'] = q['mc_answer'] if q['options'] else q['ground_truth']
        q['M'] = int(re.search(r'of (\d+)', q['question']).group(1))
        out.append(q)
    return out


def load_meta():
    out = {}
    for ds in ('scannet', 'arkitscenes', 'scannetpp'):
        for k, v in json.load(open(META % ds)).items():
            out[(ds, k)] = v
    return out


def box_grid(obb, step=0.05):
    """VLM-3R / VSI-Bench sample_points_in_oriented_bbox_uniform: a 5 cm grid inside the box minus the inner half box."""
    ext = np.asarray(obb['axesLengths'], float)
    n = np.maximum(np.ceil(ext / step).astype(int), 1)
    axes = [np.linspace(-e / 2, e / 2, k) for e, k in zip(ext, n)]
    xx, yy, zz = np.meshgrid(*axes)
    p = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], 1)
    p = p[np.any(np.abs(p) > ext / 4, axis=1)]
    if not len(p):
        p = np.zeros((1, 3))
    R = np.asarray(obb['normalizedAxes'], float).reshape(3, 3)  # rows = unit axes
    return p @ R + np.asarray(obb['centroid'], float)


def box_box_dist(A, B):
    from scipy.spatial import cKDTree
    best = None
    for a in A:
        ta = cKDTree(box_grid(a))
        for b in B:
            d = float(ta.query(box_grid(b))[0].min())
            best = d if best is None or d < best else best
    return best


def score(t, pred, gt):
    return T.score(t, pred, gt)


def paired_ci(rows_a, rows_b, key=lambda r: r['scene'], n=2000, seed=0):
    """Mean difference a - b (points) with a 95% scene-cluster bootstrap; rows are dicts id -> (scene, score)."""
    ids = sorted(set(rows_a) & set(rows_b))
    if not ids:
        return None
    by = collections.defaultdict(list)
    for i in ids:
        by[rows_a[i][0]].append(rows_a[i][1] - rows_b[i][1])
    scenes = list(by)
    sums = np.array([sum(by[s]) for s in scenes]); cnt = np.array([len(by[s]) for s in scenes])
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        k = rng.integers(0, len(scenes), len(scenes))
        bs.append(sums[k].sum() / cnt[k].sum())
    return 100 * sums.sum() / cnt.sum(), 100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5), len(ids)


def ci_mean(vals_by_scene, n=2000, seed=0):
    scenes = list(vals_by_scene)
    sums = np.array([sum(vals_by_scene[s]) for s in scenes]); cnt = np.array([len(vals_by_scene[s]) for s in scenes])
    rng = np.random.default_rng(seed)
    bs = [sums[k].sum() / cnt[k].sum() for k in (rng.integers(0, len(scenes), len(scenes)) for _ in range(n))]
    return 100 * sums.sum() / cnt.sum(), 100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5)
