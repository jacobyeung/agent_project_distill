"""Table stubs: perception and geometry that return stated values per view (the conformance tests T-1, T-10 and the
unit tests). They key on the view (role, step) the provider passes, never on hidden state."""
import hashlib
import json

import numpy as np

from ..geometry_viewset import ViewSetResult
from .base import Proposal


def _sha(name, payload):
    return hashlib.sha256(json.dumps([name, payload], sort_keys=True, default=str).encode()).hexdigest()


class TablePerception:
    """p_yes: {(role, phrase): float}; points: {(role, phrase): (u1000, v1000) or None};
    proposals: {(role, noun): [Proposal]}. Missing entries give P(yes) 0, no point and no proposals."""

    def __init__(self, p_yes, points, proposals, name='table'):
        self.p, self.points, self.props, self.name = dict(p_yes), dict(points), dict(proposals), name

    def p_yes(self, image, phrase, view):
        return float(self.p.get((view[0], phrase), 0.0))

    def point(self, image, phrase, view):
        return self.points.get((view[0], phrase))

    def propose(self, images, noun, views):
        return [list(self.props.get((v[0], noun), [])) for v in views]

    def sha(self):
        return _sha(self.name, sorted(map(str, self.p.items())))


class TableGeometry:
    """views: {(role, step): dict(T0=4x4 T_view0<-view, K=3x3, depth=[H, W], conf=[H, W] or None)}. T0 of the
    stated views is relative to the view the provider names first."""

    def __init__(self, views, metric_flag=None, name='table_geometry'):
        self.views, self.metric_flag, self.name = views, metric_flag, name

    def run(self, images, views):
        rows = [self.views[tuple(v)] for v in views]
        T_base = [np.asarray(r['T_base'], dtype=np.float64) for r in rows]
        unit = [r.get('unit', 1.0) for r in rows]
        T0 = []
        for T, u in zip(T_base, unit):
            rel = np.linalg.inv(T_base[0]) @ T
            rel[:3, 3] *= u
            T0.append(rel)
        K = np.stack([r['K'] for r in rows])
        fov = np.array([[2 * np.arctan(r['depth'].shape[0] / (2 * k[1, 1])),
                         2 * np.arctan(r['depth'].shape[1] / (2 * k[0, 0]))] for r, k in zip(rows, K)])
        conf = None if any(r.get('conf') is None for r in rows) else [r['conf'] for r in rows]
        return ViewSetResult(list(views), np.stack(T0), fov, K, [r['depth'] for r in rows], conf,
                             metric_flag=self.metric_flag)

    def sha(self):
        return _sha(self.name, sorted(map(str, self.views)))


def rect_mask(shape, r0, r1, c0, c1):
    m = np.zeros(shape, dtype=bool)
    m[max(r0, 0):r1 + 1, max(c0, 0):c1 + 1] = True
    return m


__all__ = ['TablePerception', 'TableGeometry', 'Proposal', 'rect_mask']
