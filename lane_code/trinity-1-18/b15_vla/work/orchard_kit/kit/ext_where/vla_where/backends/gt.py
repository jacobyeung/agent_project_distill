"""Ground-truth backends (the `gt_where` evaluation check, the pre-check reference) and noisy stubs (CPU pre-check).

GT enters through a GTStore side channel that the evaluator binds per episode, never through the Observation:
  store.bind(frames, names, nouns, episode) with
    frames: {step: dict(agent=view, wrist=view)}, view = dict(depth=[H, W] metres, seg={object: [H, W] bool},
            T_base_cam=4x4 OpenCV camera-to-base, K=3x3)
    names:  {phrase: object}           the step's target and place objects
    nouns:  {noun: [object, ...]}      every instance SAM 3 would propose for the noun
Every GT backend sets `reads_gt = True`; T-10 (hidden-state perturbation) applies to the others.
"""
import hashlib
import json

import numpy as np

from ..geometry_viewset import ViewSetResult
from .base import Proposal


def _sha(name, **params):
    return hashlib.sha256(json.dumps(dict(name=name, **params), sort_keys=True).encode()).hexdigest()


def rng_for(*parts):
    digest = hashlib.sha256(json.dumps([str(p) for p in parts]).encode()).hexdigest()
    return np.random.default_rng(int(digest[:16], 16))


def gt_point(mask):
    """The student pointing rows' rule (carrier_c1_data.mask_target): the foreground pixel nearest the centroid whose
    uv1000 grid point maps back inside the mask."""
    yx = np.argwhere(mask)
    if not len(yx):
        return None
    h, w = mask.shape
    for y, x in yx[np.square(yx - yx.mean(axis=0)).sum(axis=1).argsort(kind='stable')]:
        u, v = min(int((x + .5) / w * 1000), 1000), min(int((y + .5) / h * 1000), 1000)
        if all(mask[min(int(b), h - 1), min(int(a), w - 1)]
               for a, b in ((u * w / 1000, v * h / 1000), (u * w / 1000 + .5, v * h / 1000 + .5))):
            return (u, v)
    return None


class GTStore:
    def __init__(self):
        self.frames, self.names, self.nouns, self.episode = {}, {}, {}, ''

    def bind(self, frames, names, nouns, episode=''):
        self.frames, self.names, self.nouns = frames, dict(names), {k: list(v) for k, v in nouns.items()}
        self.episode = episode

    def view(self, view):
        role, step = view
        return self.frames[step][role]

    def mask(self, view, phrase):
        return self.view(view)['seg'].get(self.names.get(phrase, phrase))


class GTPresence:
    reads_gt = True

    def __init__(self, store, min_pixels=20):
        self.store, self.min_pixels = store, min_pixels

    def p_yes(self, image, phrase, view):
        m = self.store.mask(view, phrase)
        return float(m is not None and int(m.sum()) >= self.min_pixels)

    def sha(self):
        return _sha('gt_presence', min_pixels=self.min_pixels)


class GTPointer:
    reads_gt = True

    def __init__(self, store):
        self.store = store

    def point(self, image, phrase, view):
        m = self.store.mask(view, phrase)
        return None if m is None else gt_point(m)

    def sha(self):
        return _sha('gt_pointer')


class GTProposals:
    reads_gt = True

    def __init__(self, store, min_pixels=1):
        self.store, self.min_pixels = store, min_pixels

    def propose(self, images, noun, views):
        out = []
        for v in views:
            seg = self.store.view(v)['seg']
            out.append([Proposal(seg[o].copy(), 1.0) for o in self.store.nouns.get(noun, [noun])
                        if o in seg and seg[o].sum() >= self.min_pixels])
        return out

    def sha(self):
        return _sha('gt_proposals')


class GTGeometry:
    """Metric depth and poses. flag: 'proprio_handeye' for gt_where (in-distribution flag), 'metric_test' in tests."""
    reads_gt = True

    def __init__(self, store, flag='proprio_handeye'):
        self.store, self.flag = store, flag

    def run(self, images, views):
        rows = [self.store.view(v) for v in views]
        T0 = np.stack([np.linalg.inv(rows[0]['T_base_cam']) @ r['T_base_cam'] for r in rows])
        K = np.stack([r['K'] for r in rows])
        fov = np.array([[2 * np.arctan(r['depth'].shape[0] / (2 * k[1, 1])),
                         2 * np.arctan(r['depth'].shape[1] / (2 * k[0, 0]))] for r, k in zip(rows, K)])
        return ViewSetResult(list(views), T0, fov, K, [np.asarray(r['depth'], dtype=np.float64) for r in rows],
                             None, metric_flag=self.flag)

    def sha(self):
        return _sha('gt_geometry', flag=self.flag)


class NoisyPerception:
    """GT presence, point and proposals with injected errors, reproducible per (view, phrase): false_yes (P(yes) high
    on absent views), miss (low on visible views), wrong (the point lands on another instance of the noun), jitter_px
    (point noise). P(yes) is drawn from Beta-like ranges so AUROC and tau refits have something to read."""
    reads_gt = True

    def __init__(self, store, false_yes=0.0, miss=0.0, wrong=0.0, jitter_px=0.0):
        self.store, self.false_yes, self.miss, self.wrong, self.jitter = store, false_yes, miss, wrong, jitter_px
        self.gt = GTProposals(store)

    def _visible(self, view, phrase):
        m = self.store.mask(view, phrase)
        return m is not None and m.sum() >= 20

    def p_yes(self, image, phrase, view):
        r = rng_for('p', view, phrase, self.store.episode)
        if self._visible(view, phrase):
            return float(r.uniform(0.0, 0.5) if r.random() < self.miss else r.uniform(0.6, 1.0))
        return float(r.uniform(0.5, 1.0) if r.random() < self.false_yes else r.uniform(0.0, 0.4))

    def point(self, image, phrase, view):
        r = rng_for('pt', view, phrase, self.store.episode)
        target = self.store.mask(view, phrase)
        mask = target
        if r.random() < self.wrong:
            noun = next((n for n, objs in self.store.nouns.items() if self.store.names.get(phrase) in objs), None)
            others = [o for o in self.store.nouns.get(noun, []) if o != self.store.names.get(phrase)]
            seg = self.store.view(view)['seg']
            others = [o for o in others if o in seg and seg[o].sum() >= 20]
            if others:
                mask = seg[others[int(r.integers(len(others)))]]
        if mask is None or not mask.any():
            return None
        u, v = gt_point(mask) or (None, None)
        if u is None:
            return None
        if self.jitter:
            u, v = (int(np.clip(round(c + r.normal(0, self.jitter * 1000 / mask.shape[1])), 0, 1000)) for c in (u, v))
        return (u, v)

    def propose(self, images, noun, views):
        return self.gt.propose(images, noun, views)

    def sha(self):
        return _sha('noisy_perception', false_yes=self.false_yes, miss=self.miss, wrong=self.wrong, jitter=self.jitter)


class NoisyGeometry:
    """GT geometry in an arbitrary unit (depth and translations x unit), with multiplicative depth noise and pose
    noise; confidence is 1 + noise so the median-confidence filter keeps about half the pixels."""
    reads_gt = True

    def __init__(self, store, unit=0.37, depth_sigma=0.0, pose_t_sigma=0.0, pose_r_deg=0.0, mirror=False):
        """mirror: GT cameras use K with fx < 0 (LIBERO dataset orientation); emit what G3T would, mirrored frames
        (T_g = M T M, K_g with fx > 0, flag mirror) so that the provider's X_wrist = s M X_g is under test (P-2)."""
        self.store, self.unit, self.depth_sigma, self.t_sigma, self.r_deg = store, unit, depth_sigma, pose_t_sigma, pose_r_deg
        self.mirror = bool(mirror)

    def run(self, images, views):
        from .. import geometry as G
        base = GTGeometry(self.store, flag=None).run(images, views)
        T0, depth, conf = [], [], []
        for k, (v, d) in enumerate(zip(views, base.depth)):
            r = rng_for('geo', v, self.store.episode)
            T = base.T0[k].copy()
            if k > 0:
                T[:3, 3] += r.normal(0, self.t_sigma, 3)
                T[:3, :3] = G.axis_angle_to_matrix(r.normal(0, np.radians(self.r_deg), 3)) @ T[:3, :3]
            T[:3, 3] *= self.unit
            T0.append(T)
            noise = np.exp(r.normal(0, self.depth_sigma, d.shape)) if self.depth_sigma else 1.0
            depth.append(d * noise * self.unit)
            conf.append(1.0 + r.random(d.shape))
        K = base.K.copy()
        if self.mirror:
            M = np.diag([-1.0, 1.0, 1.0, 1.0])
            T0 = [M @ T @ M for T in T0]
            K[:, 0, 0] *= -1
        return ViewSetResult(list(views), np.stack(T0), base.fov, K, depth, conf, metric_flag=None,
                             mirror=self.mirror)

    def sha(self):
        return _sha('noisy_geometry', unit=self.unit, depth_sigma=self.depth_sigma, t=self.t_sigma, r=self.r_deg,
                    mirror=self.mirror)


class DistractorPerception(NoisyPerception):
    """NoisyPerception plus cross-noun grounding errors, so that single-instance entities (the plate) can be grounded
    wrongly too: SAM 3 also proposes every other visible scene object at score 0.5 (false positives), and with
    probability wrong_any the point lands on one of them (reproducible per view and phrase)."""
    BACKGROUND = ('table',)

    def __init__(self, store, wrong_any=0.0, **kwargs):
        super().__init__(store, **kwargs)
        self.wrong_any = wrong_any

    def _others(self, view, phrase):
        seg, own = self.store.view(view)['seg'], self.store.names.get(phrase, phrase)
        return sorted(o for o in seg if o != own and not any(b in o for b in self.BACKGROUND) and seg[o].sum() >= 20)

    def point(self, image, phrase, view):
        r = rng_for('any', view, phrase, self.store.episode)
        if r.random() < self.wrong_any:
            others = self._others(view, phrase)
            if others:
                return gt_point(self.store.view(view)['seg'][others[int(r.integers(len(others)))]])
        return super().point(image, phrase, view)

    def propose(self, images, noun, views):
        out = super().propose(images, noun, views)
        for found, v in zip(out, views):
            seg, mine = self.store.view(v)['seg'], set(self.store.nouns.get(noun, [noun]))
            found += [Proposal(seg[o].copy(), 0.5) for o in sorted(seg) if o not in mine
                      and not any(b in o for b in self.BACKGROUND) and seg[o].sum() >= 1]
        return out

    def sha(self):
        return _sha('distractor_perception', base=super().sha(), wrong_any=self.wrong_any)
