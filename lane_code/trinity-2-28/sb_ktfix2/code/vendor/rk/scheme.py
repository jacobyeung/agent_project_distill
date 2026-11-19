"""SPEC v3.11 frame selection and mask-surface geometry."""
import numpy as np

from .programs import Scene, closest_sets, run_vsi, T


class LiftFailure(ValueError):
    pass


class Refusal(ValueError):
    pass


class V311Scene(Scene):
    def __init__(self, geo, ground, gates=True):
        super().__init__(geo, ground, 'mask', scheme='spec')
        self.anchors = [k for k in range(1, 33) if geo.has(k)]
        self.gr.geo = geo
        self.direction_frames = {}
        self.gates = gates
        self.point_cache = {}

    def vis(self, obj, k):
        return self.gr.vis(obj, k)

    def choose_frames(self, a, b):
        A = [k for k in self.anchors if self.vis(a, k)[0]]
        B = [k for k in self.anchors if self.vis(b, k)[0]]
        common = set(A).intersection(B)
        if common:
            k = min(common, key=lambda k: (-min(self.vis(a, k)[1], self.vis(b, k)[1]), k))
            return k, k, 'both'
        if not A or not B:
            return None
        i, j = min(((i, j) for i in A for j in B), key=lambda p: (abs(p[0]-p[1]), *p))
        return i, j, 'pair'

    def prepare_direction(self, objects):
        objects = list(dict.fromkeys(objects))
        def rank(k):
            areas = [self.vis(obj, k)[1] for obj in objects if self.vis(obj, k)[0]]
            return (-len(areas), -min(areas) if areas else 0, k)
        anchor = min(self.anchors, key=rank)
        self.direction_frames = {}
        for obj in objects:
            visible = [k for k in self.anchors if self.vis(obj, k)[0]]
            if not visible:
                continue
            self.direction_frames[obj] = min(visible, key=lambda k: (abs(anchor-k), anchor, k))
        self.trace.append(dict(anchor=anchor, frames=dict(self.direction_frames)))

    def best_frame(self, obj):
        if obj in self.direction_frames:
            return self.direction_frames[obj]
        visible = [k for k in self.anchors if self.vis(obj, k)[0]]
        return min(visible, key=lambda k: (-self.vis(obj, k)[1], k)) if visible else None

    def points(self, obj, kind='mask', other=None, frames=None):
        points, used = [], []
        for k in self.anchors if frames is None else frames:
            try:
                if (obj, k) not in self.point_cache:
                    self.point_cache[obj, k] = self.gr.lifted(obj, k)[1]
                P = self.point_cache[obj, k]
            except (ValueError, FloatingPointError) as exc:
                raise LiftFailure(str(exc)) from exc
            if len(P):
                points.append(P)
                used.append(k)
        return np.concatenate(points) if points else np.empty((0, 3)), used, []

    def centroid(self, obj):
        k = self.best_frame(obj)
        if k is None:
            return None, []
        P, used, _ = self.points(obj, frames=[k])
        return (np.median(P, axis=0) if len(P) else None), used

    def pair_points(self, a, b, kind_a='mask', kind_b='mask'):
        visible_a = [k for k in self.anchors if self.vis(a, k)[0]]
        visible_b = [k for k in self.anchors if self.vis(b, k)[0]]
        common = set(visible_a).intersection(visible_b)
        if not visible_a or not visible_b:
            return None, None
        if common:
            order = sorted(common, key=lambda k: (-min(self.vis(a, k)[1], self.vis(b, k)[1]), k))
            pairs = [(k, k) for k in order]
        else:
            pairs = sorted(((i, j) for i in visible_a for j in visible_b),
                           key=lambda p: (abs(p[0]-p[1]), *p))
        for i, j in pairs:
            A = self.points(a, frames=[i])[0]
            B = self.points(b, frames=[j])[0]
            if len(A) and len(B):
                self.trace.append(dict(objects=[a, b], frames=[i, j], choice='both' if common else 'pair'))
                return A, B
        raise Refusal('common_frame_unclickable' if common else 'missing_eligible_operands')

    def distance(self, a, b):
        A, B = self.pair_points(a, b)
        if A is None:
            return None
        return closest_sets(A, B)

    def relative_distance(self, target, cands, options, farthest=False):
        distances = [self.distance(target, c) for c in cands]
        if any(d is None or not np.isfinite(d) for d in distances):
            raise Refusal('missing_eligible_operands')
        order = np.argsort(distances, kind='stable')
        if farthest:
            order = order[::-1]
        first, second = [distances[i] for i in order[:2]]
        gap = abs(second-first)
        relative = gap/second if second else (0.0 if not gap else None)
        self.trace.append(dict(distances=distances, margin_m=gap, margin_rel=relative))
        if self.gates and (gap < .10 or gap < .10*second):
            raise Refusal('near_tie')
        from .sets import clean
        answer = clean(cands[int(order[0])]).lower()
        return next((letter for letter, text in T.option_texts(options).items()
                     if clean(text).lower() == answer), None)

    def direction(self, roles, options, hard=False, away=False):
        objects = [roles[k] for k in ('stand', 'face', 'query')]
        self.prepare_direction(objects)
        cs = [self.centroid(obj)[0] for obj in objects]
        if any(c is None for c in cs):
            common = set.intersection(*[{k for k in self.anchors if self.vis(obj, k)[0]}
                                        for obj in objects])
            if common:
                for k in sorted(common, key=lambda k: (-min(self.vis(obj, k)[1] for obj in objects), k)):
                    self.direction_frames = dict.fromkeys(objects, k)
                    cs = [self.centroid(obj)[0] for obj in objects]
                    if all(c is not None for c in cs):
                        self.trace.append(dict(anchor=k, frames=dict(self.direction_frames)))
                        break
                else:
                    raise Refusal('common_frame_unclickable')
            else:
                anchor = self.trace[0]['anchor']
                for obj in objects:
                    visible = [k for k in self.anchors if self.vis(obj, k)[0]]
                    for k in sorted(visible, key=lambda k: (abs(anchor-k), k)):
                        if len(self.points(obj, frames=[k])[0]):
                            self.direction_frames[obj] = k
                            break
                    else:
                        raise Refusal('missing_eligible_operands')
                cs = [self.centroid(obj)[0] for obj in objects]
                self.trace.append(dict(anchor=anchor, frames=dict(self.direction_frames)))
        S, F, Q = cs
        if away:
            F = 2*S-F
        lengths = [float(np.linalg.norm((c-S)[:2])) for c in (F, Q)]
        if min(lengths) < 1e-9:
            raise Refusal('degenerate_direction')
        theta = T.floor_angle(S, F, Q)[0]
        boundaries = (0, 90, 180, 270) if hard else (0, 135, 225)
        margin = min(abs((theta-b+180) % 360-180) for b in boundaries)
        self.trace.append(dict(theta=theta, floor_vectors_m=lengths, boundary_margin_deg=margin))
        if self.gates and min(lengths) < .50:
            raise Refusal('short_floor_vector')
        if self.gates and margin < 10:
            raise Refusal('near_boundary_refused')
        kind = 'object_rel_direction_hard' if hard else 'object_rel_direction_medium'
        return T.letter_of(options, T.direction_label(kind, theta))

    def run(self, item):
        self.trace = []
        self.direction_frames = {}
        self.point_cache = {}
        from .sets import labels
        if not self.anchors:
            return None, 'no_frame'
        missing = [obj for obj in labels(item) if not any(self.vis(obj, k)[0] for k in self.anchors)]
        if missing:
            return None, 'object_not_visible: '+', '.join(missing)
        try:
            if item['set'] == 'revsi':
                from .revsi import execute
                pred = execute(item, self)
            elif item['type'].startswith('object_rel_direction'):
                roles = T.parse_vsi(dict(question_type=item['type'], question=item['question']))
                pred = self.direction(roles, item['options'], hard=item['type'].endswith('_hard'))
            elif item['type'] == 'object_rel_distance':
                roles = T.parse_vsi(dict(question_type=item['type'], question=item['question']))
                pred = self.relative_distance(roles['target'], roles['cands'], item['options'])
            else:
                pred = run_vsi(dict(question_type=item['type'], question=item['question'],
                                    options=item['options']), self, {})
        except Refusal as exc:
            return None, str(exc)
        except LiftFailure as exc:
            return None, 'lift_failure: '+str(exc)
        if pred is None or isinstance(pred, (float, np.floating)) and not np.isfinite(pred):
            return None, 'lift_failure_or_no_answer'
        return pred, None


def run(item, scene):
    return scene.run(item)
