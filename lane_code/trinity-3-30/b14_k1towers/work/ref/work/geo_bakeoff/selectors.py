import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage

from .reference import modules
from .paths import path as data_path


RAW = data_path("/dev/shm/jjyeung_mdg_next/recache_vsi")
TABLE = data_path("/scratch/jjyeung/orch_cd/grd_selector/work/setsel/data/vsi_tab.jsonl")
PROBS = data_path("/scratch/jjyeung/orch_cd/grd_selector/work/setsel/data/probs/probs.json")
TOWER = data_path("/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd")
TYPES = {
    "object_abs_distance", "object_counting", "object_size_estimation", "object_rel_distance",
    "object_rel_direction_easy", "object_rel_direction_medium", "object_rel_direction_hard",
}
FIXES = "frameidx,axes,memory,extent,identity,round,vocab,gbox0".split(",")


def item_names(parsed):
    return [parsed[k].lower() for k in ("a", "b", "cat", "target", "stand", "face", "query") if k in parsed] + [x.lower() for x in parsed.get("cands", [])]


def rle_decode(rle):
    counts = np.asarray(rle["counts"], np.int64)
    if (counts < 0).any() or int(counts.sum()) != int(np.prod(rle["size"])):
        raise ValueError("Invalid selector mask RLE")
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape(rle["size"], order="F")


def load_tables(table=TABLE, probabilities=PROBS):
    objects, candidates = {}, defaultdict(list)
    with open(table) as f:
        for line in f:
            row = json.loads(line)
            if row["kind"] == "object":
                objects[row["object_id"]] = row
            else:
                candidates[row["object_id"]].append(row)
    probs = json.loads(Path(probabilities).read_text())["DEPLOY|portable|logistic"]
    return objects, candidates, probs


class TowerGeometry:
    def __init__(self, path):
        self.h = modules()["programs"].load_heads(str(path))
        yy, xx = np.mgrid[:240, :320]
        self.u, self.v = (xx + .5) / 320 * 1000, (yy + .5) / 240 * 1000
        self.frames = list(range(1, 33))
        self._depth = {}

    def depth(self, k):
        if k not in self._depth:
            self._depth[k] = self.h._depth(k - 1, self.u.ravel(), self.v.ravel()).reshape(240, 320).astype(np.float32)
        return self._depth[k]

    def cam(self, k):
        return self.h.cam(k)

    def rays(self, k):
        fh, fw = self.h.fov[k - 1]
        return np.stack([(self.u / 500 - 1) * math.tan(fw / 2), (self.v / 500 - 1) * math.tan(fh / 2), np.ones_like(self.u)], -1)


class GTGeometry:
    def __init__(self, gt):
        self.gt = gt
        yy, xx = np.mgrid[:240, :320]
        self._rays = np.stack([xx + .5, yy + .5, np.ones_like(xx, float)], -1) @ gt.Kinv.T
        self.frames = [k for k in range(1, 33) if gt.has(k)]

    def depth(self, k):
        return self.gt.depth[k - 1]

    def cam(self, k):
        return self.gt.cam(k)

    def rays(self, k):
        return self._rays


def depth_cut(mask, depth):
    inner = ndimage.binary_erosion(mask, iterations=3)
    if inner.sum() < 20:
        inner = mask
    values = depth[inner]
    values = values[values > 0]
    if len(values) < 10:
        return mask
    lo, hi = np.percentile(values, 10) - .15, np.percentile(values, 90) + .15
    keep = mask & (depth >= lo) & (depth <= hi)
    return keep if keep.sum() >= 8 else mask


def lift(geometry, frame, mask, cut=False):
    depth = geometry.depth(frame)
    if cut:
        mask = depth_cut(mask, depth)
    use = mask[::2, ::2] & (depth[::2, ::2] > 0)
    if use.sum() < 3:
        return None
    z = depth[::2, ::2][use]
    r, t = geometry.cam(frame)
    return (geometry.rays(frame)[::2, ::2][use] * z[:, None]) @ r.T + t


class MaskFused:
    def __init__(self, geometry, instances, cut=False):
        self.pts, self.px, self._box = {}, {}, {}
        self.min_px = 154
        for obj, frames in instances.items():
            for frame, mask in frames.items():
                n = int(mask.sum())
                self.px.setdefault(obj, {})[frame] = n
                if n < 154 or frame not in geometry.frames:
                    continue
                points = lift(geometry, frame, mask, cut)
                if points is not None:
                    self.pts.setdefault(obj, []).append(points)

    def points(self, obj):
        parts = self.pts.get(obj)
        return np.concatenate(parts) if parts else None

    def box(self, obj):
        if obj not in self._box:
            points = self.points(obj)
            if points is not None and len(points) > 4000:
                points = points[np.random.default_rng(0).choice(len(points), 4000, replace=False)]
            self._box[obj] = modules()["scene_gt"].minimal_obb(points) if points is not None else None
        return self._box[obj]

    def seen(self, obj, min_px=None):
        return any(n >= (self.min_px if min_px is None else min_px) for n in self.px.get(obj, {}).values())


class MaskContext:
    def __init__(self, geometry, masks, cut=False, rule=None):
        self.gt, self.fixes, self.level = geometry, set(FIXES), "B"
        self.name2ids, instances = {}, {}
        for name, objects in masks.items():
            self.name2ids[name] = []
            for frames in objects:
                obj = len(instances)
                self.name2ids[name].append(obj)
                instances[obj] = frames
        self.fused = MaskFused(geometry, instances, cut=cut) if rule is None else PolicyMaskFused(geometry, instances, cut, rule)

    def ids(self, name):
        return self.name2ids.get(name.lower(), [])


def union(parts):
    out = {}
    for frames in parts:
        for frame, mask in frames.items():
            out[frame] = out[frame] | mask if frame in out else mask
    return out


def merge_candidates(parts, geometry, probabilities):
    centres, extents = [], []
    for _, frames in parts:
        points = [lift(geometry, k, m) for k, m in frames.items() if k in geometry.frames]
        points = [p for p in points if p is not None]
        centres.append(np.median(np.stack([np.median(p, 0) for p in points]), 0) if points else None)
        all_points = np.concatenate(points) if points else None
        extents.append(float(np.max(np.percentile(all_points, 90, 0) - np.percentile(all_points, 10, 0))) if points else 0.)
    groups = {i: {i} for i in range(len(parts))}
    roots = list(range(len(parts)))
    def root(i):
        while roots[i] != i:
            i = roots[i]
        return i
    pairs = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if centres[i] is None or centres[j] is None:
                continue
            distance = float(np.linalg.norm(centres[i] - centres[j]))
            if distance < .3 + .5 * max(extents[i], extents[j]):
                pairs.append((distance, i, j))
    for _, i, j in sorted(pairs):
        ri, rj = root(i), root(j)
        if ri == rj:
            continue
        blocked = any(
            np.logical_and(parts[a][1][k], parts[b][1][k]).sum() < .2 * min(parts[a][1][k].sum(), parts[b][1][k].sum())
            for a in groups[ri] for b in groups[rj] for k in set(parts[a][1]) & set(parts[b][1])
        )
        if not blocked:
            roots[rj] = ri
            groups[ri] |= groups.pop(rj)
    return [union([parts[i][1] for i in sorted(group, key=lambda x: -probabilities[parts[x][0]])]) for group in groups.values()]


def masks_for_scene(scene, questions, base, tables):
    objects, candidates, probabilities = tables
    with np.load(RAW / f"scannet__{scene}.npz", allow_pickle=False) as z:
        raw = json.loads(z["payload"].tobytes())
    ref = modules()
    ground = ref["programs"].GTGround(base)
    ref["prog_v2"].use_vocab(ground)
    names = sorted({name for q in questions for name in item_names(ref["tplib"].parse_vsi(q))})
    gt_masks, unique, counting = {}, {}, {}
    tower = TowerGeometry(TOWER / f"scannet__{scene}.npz")
    for name in names:
        gt_masks[name] = [{k: base.inst[k - 1] == i for k in range(1, 33) if (base.inst[k - 1] == i).any()}
                          for i in ground.instances(name)]
        key = f"scannet/{scene}::{name}"
        obj = objects.get(key)
        if obj is None:
            continue
        cs = candidates.get(key, [])
        prob = {c["candidate_id"]: probabilities.get(f"{key}|{c['candidate_id']}", 0.) for c in cs}
        decoded = {}
        for candidate in cs:
            decoded[candidate["candidate_id"]] = {
                m["slot"] + 1: rle_decode(raw["frames"][str(m["slot"])]["phrases"][obj["phrase"]]["instances"][m["ii"]]["mask"])[::2, ::2]
                for m in candidate["members"]
            }
        best = max(cs, key=lambda c: (prob[c["candidate_id"]], c["features"]["peak"])) if cs else None
        unique[name] = [decoded[best["candidate_id"]]] if best else []
        accepted = [c for c in cs if prob[c["candidate_id"]] >= .5] or ([best] if best else [])
        parts = [(c["candidate_id"], decoded[c["candidate_id"]]) for c in accepted]
        counting[name] = merge_candidates(parts, tower, prob)
    return gt_masks, unique, counting


class PolicyMaskFused(MaskFused):
    def __init__(self, geometry, instances, cut, rule):
        self.pts, self.px, self._box, self._fused = {}, {}, {}, {}
        self.min_px, self.rule = 154, rule
        for obj, frames in instances.items():
            for frame, mask in frames.items():
                count = int(mask.sum())
                self.px.setdefault(obj, {})[frame] = count
                if count < self.min_px or frame not in geometry.frames:
                    continue
                points = lift(geometry, frame, mask, cut)
                if points is not None:
                    self.pts.setdefault(obj, []).append((frame, points, count))

    def points(self, obj):
        if obj not in self._fused:
            parts = self.pts.get(obj)
            self._fused[obj] = modules()["geomswap"].fuse_points(parts, self.rule) if parts else None
        return self._fused[obj]


def deployed_tables():
    data = TABLE.parent
    config = json.loads(data_path("/scratch/jjyeung/orch_cd/grd_selector/out/price2_vsi/config.json").read_text())
    probabilities = json.loads((data / "probs2/probs.json").read_text())[f"DEPLOY|{config['acc']['np']}"]
    pairs = json.loads((data / "pairs_fit/pair_probs.json").read_text())[f"DEPLOY|{config['pair_model']}"]
    objects, candidates = modules()["setlib"].load(TABLE)
    if config["merge"] != "lm":
        raise ValueError("The frozen deployed selector must use its learned disjoint-aware merge")
    return objects, candidates, probabilities, pairs, config


def deployed_masks(scene, questions, base, tables):
    objects, candidates, probabilities, pairs, config = tables
    ref, gt_masks, unique, counting = modules(), {}, {}, {}
    ground = ref["programs"].GTGround(base)
    ref["prog_v2"].use_vocab(ground)
    names = sorted({name for q in questions for name in item_names(ref["tplib"].parse_vsi(q))})
    with np.load(RAW / f"scannet__{scene}.npz", allow_pickle=False) as z:
        raw = json.loads(z["payload"].tobytes())
    selection = ref["setlib"]
    for name in names:
        gt_masks[name] = [{k: base.inst[k-1] == i for k in range(1, 33) if (base.inst[k-1] == i).any()}
                          for i in ground.instances(name)]
        key = f"scannet/{scene}::{name}"
        obj, cs = objects.get(key), candidates.get(key, [])
        if obj is None:
            continue
        prob = {c["candidate_id"]: probabilities.get(f"{key}|{c['candidate_id']}", 0.) for c in cs}
        decoded = {c["candidate_id"]: {
            m["slot"] + 1: rle_decode(raw["frames"][str(m["slot"])]["phrases"][obj["phrase"]]["instances"][m["ii"]]["mask"])[::2, ::2]
            for m in c["members"]
        } for c in cs}
        unique[name] = [decoded[c["candidate_id"]] for c in selection.accept(cs, prob, 2.)]
        accepted = [c["candidate_id"] for c in selection.accept(cs, prob, config["tau_count"])]
        def blocked(i, j):
            return any(np.logical_and(decoded[i][k], decoded[j][k]).sum() < .2 * min(decoded[i][k].sum(), decoded[j][k].sum())
                       for k in set(decoded[i]) & set(decoded[j]))
        def same(i, j):
            return pairs.get(f"{key}|{i}|{j}", pairs.get(f"{key}|{j}|{i}", 0.))
        groups = selection.merge_learned(accepted, same, config["thr_merge"], blocked) if accepted else []
        counting[name] = [union([decoded[c] for c in sorted(group, key=lambda c: -prob[c])]) for group in groups]
    return gt_masks, unique, counting
