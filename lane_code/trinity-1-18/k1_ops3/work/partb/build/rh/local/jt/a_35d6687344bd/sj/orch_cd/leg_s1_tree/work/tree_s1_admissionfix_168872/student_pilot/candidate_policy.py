from dataclasses import dataclass
from itertools import combinations
import numpy as np
from scipy import ndimage

from .p3_provenance import load, pinned


NAME = "routed_default_v1"
COUNTING = frozenset(("object_counting", "absolute_count", "relative_count"))


def predict(model, features):
    missing = set(model["features"]) - set(features)
    if missing:
        raise ValueError("Candidate policy lacks features: " + ", ".join(sorted(missing)))
    x = np.asarray([features[key] for key in model["features"]], np.float64)
    if not np.isfinite(x).all():
        raise ValueError("Candidate policy received nonfinite features")
    z = ((x-np.asarray(model["mean"]))/np.asarray(model["scale"])) @ np.asarray(model["coefficient"])
    z = float(z) + model["intercept"]
    return float(np.exp(-np.logaddexp(0., -z)))


def depth_cut(mask, depth):
    mask, depth = np.asarray(mask, bool), np.asarray(depth, float)
    if mask.shape != depth.shape:
        raise ValueError("Candidate mask and depth grid differ")
    inner = ndimage.binary_erosion(mask, iterations=3)
    if inner.sum() < 20:
        inner = mask
    values = depth[inner]
    values = values[np.isfinite(values) & (values > 0)]
    if len(values) < 10:
        return mask.copy()
    low, high = np.percentile(values, (10, 90)) + np.array([-.15, .15])
    keep = mask & (depth >= low) & (depth <= high)
    return keep if keep.sum() >= 8 else mask.copy()


def disjoint(a, b):
    for frame in a.keys() & b.keys():
        first, second = np.asarray(a[frame], bool), np.asarray(b[frame], bool)
        if first.shape != second.shape:
            raise ValueError("Candidate masks use different rasters")
        if np.logical_and(first, second).sum() < .2 * min(first.sum(), second.sum()):
            return True
    return False


def merge(ids, probability, blocked, threshold=.2):
    groups = [[identity] for identity in ids]
    while len(groups) > 1:
        best = -1.
        selected = None
        for a, b in combinations(range(len(groups)), 2):
            if any(blocked(i, j) for i in groups[a] for j in groups[b]):
                continue
            score = float(np.mean([probability(i, j) for i in groups[a] for j in groups[b]]))
            if score > best:
                best, selected = score, (a, b)
        if best < threshold or selected is None:
            break
        a, b = selected
        groups[a] += groups.pop(b)
    order = {identity: index for index, identity in enumerate(ids)}
    return [sorted(group, key=order.get) for group in groups]


@dataclass
class Policy:
    config: dict
    question_type: str

    def __post_init__(self):
        if set(self.config) != {"name", "weights"} or self.config["name"] != NAME:
            raise ValueError("Unknown grounded candidate policy")
        self.weights = load(pinned(self.config["weights"]))
        fixed = dict(schema="routed-candidate-policy-v1", count_threshold=.15, merge_threshold=.2,
                     depth_erosion=3, depth_percentiles=[10, 90], depth_margin_m=.15,
                     disjoint_overlap=.2, name_prior=False)
        if any(self.weights.get(key) != value for key, value in fixed.items()):
            raise ValueError("Routed policy constants differ from the frozen default")

    def select(self, candidates, pair_features, depth):
        candidates = list(candidates)
        ids = [candidate["candidate_id"] for candidate in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("Candidate policy requires unique identities")
        if not candidates:
            return [], dict(policy=NAME, accepted=[], groups=[], probabilities={})
        by_id = dict(zip(ids, candidates, strict=True))
        probabilities = {identity: predict(self.weights["accept"], value["features"])
                         for identity, value in by_id.items()}
        best = max(ids, key=lambda identity: (probabilities[identity], by_id[identity]["features"]["peak"]))
        if self.question_type not in COUNTING:
            candidate = by_id[best]
            masks = {frame: depth_cut(mask, depth(frame, np.asarray(mask).shape))
                     for frame, mask in candidate["masks"].items()}
            selected = [dict(candidate_id=best, masks=masks, probability=probabilities[best])]
            return selected, dict(policy=NAME, accepted=[best], groups=[[best]], probabilities=probabilities,
                                  interior_depth_cut=True)
        chosen = [identity for identity in ids if probabilities[identity] >= .15] or [best]
        pairs = {frozenset((a, b)): predict(self.weights["pair"], pair_features(by_id[a], by_id[b]))
                 for a, b in combinations(chosen, 2)}
        groups = merge(chosen, lambda a, b: pairs[frozenset((a, b))],
                       lambda a, b: disjoint(by_id[a]["masks"], by_id[b]["masks"]))
        selected = []
        for group in groups:
            frames = sorted({frame for identity in group for frame in by_id[identity]["masks"]})
            masks = {}
            for frame in frames:
                masks[frame] = np.logical_or.reduce([by_id[identity]["masks"][frame]
                                                    for identity in group if frame in by_id[identity]["masks"]])
            selected.append(dict(candidate_id="+".join(group), masks=masks,
                                 probability=max(probabilities[identity] for identity in group)))
        return selected, dict(policy=NAME, accepted=chosen, groups=groups, probabilities=probabilities,
                              interior_depth_cut=False)
