"""Parameter-free metric geometry; no grounding, GT correction or automatic retries."""
import json
import math

import numpy as np

from .head_programs import camera_ray, level_rotation
from .p3_grammar import ToolError, frame, pixel


def finite(a, shape=None):
    a = np.asarray(a, dtype=np.float64)
    if not np.isfinite(a).all() or (shape is not None and a.shape != shape):
        raise ToolError('invalid_measurement', f'expected finite {shape}, got {a.shape}')
    return a


def rotation(a):
    a = finite(a, (3, 3))
    if not np.allclose(a.T @ a, np.eye(3), atol=1e-4) or not np.isclose(np.linalg.det(a), 1, atol=1e-4):
        raise ToolError('invalid_rotation', 'expected SO(3)')
    return a


class Geometry:
    """Camera-to-reference poses, optical-axis depth, centred FoV, gravity and one scale.

    All backing translations/depths share `unit_scale_m`. Metric head predictions use
    1, NOT the predicted trajectory-step scale a second time. Percentiles use numpy
    `method=linear`. Stencil coordinates clamp to [0,1000], retaining repeated edge
    samples; finite positive depths alone enter ALL percentiles. An empty patch fails.
    """
    def __init__(self, rotations, centres, fov, depth, *, anchors=tuple(range(2, 33, 2)),
                 origin_rotation=np.eye(3), up=(0, -1, 0), unit_scale_m=1., nframes=32,
                 translation_scale_m=None,depth_scale_m=None,pose_input=None):
        if pose_input not in (None, 'spatial_tokens_v1'):
            raise ValueError('Unknown geometry pose input')
        self.pose_input = pose_input
        self.anchors = tuple(anchors)
        if (not self.anchors or tuple(sorted(set(self.anchors))) != self.anchors
                or any(frame(k, nframes) != k for k in self.anchors)):
            raise ToolError('bad_anchors', str(anchors))
        n = len(anchors)
        self.r = np.stack([rotation(r) for r in finite(rotations, (n, 3, 3))])
        self.c, self.fov = finite(centres, (n, 3)), finite(fov, (n, 2))
        if np.any(self.fov <= 0) or np.any(self.fov >= math.pi):
            raise ToolError('invalid_fov', 'FoV must be radians in (0,pi)')
        if not math.isfinite(unit_scale_m) or unit_scale_m <= 0:
            raise ToolError('invalid_scale', str(unit_scale_m))
        self.translation_scale=unit_scale_m if translation_scale_m is None else translation_scale_m
        self.depth_scale=unit_scale_m if depth_scale_m is None else depth_scale_m
        if any(not math.isfinite(s) or s<=0 for s in (self.translation_scale,self.depth_scale)):
            raise ToolError('invalid_scale','depth/translation scale must be positive finite')
        self.depth_fn, self.nframes = depth, nframes
        self.r0, self.up = rotation(origin_rotation), finite(up, (3,))
        if np.linalg.norm(self.up) < 1e-6:
            raise ToolError('invalid_gravity', 'zero up vector')
        self.level1 = level_rotation(self.r0, self.up)
        self.y_up = np.diag([1., -1., 1.]) @ self.level1

    def effective(self, requested, *, pose=False):
        frame(requested, self.nframes)
        if pose and requested == 1:
            return 1
        if requested in self.anchors:
            return requested
        if requested % 2 and requested + 1 in self.anchors:
            return requested + 1
        raise ToolError('unsupported_frame', str(requested))

    def camera(self, requested):
        k = self.effective(requested, pose=True)
        if k == 1:
            return k, self.r0, np.zeros(3)
        g = self.anchors.index(k)
        return k, self.r[g], finite(self.c[g] * self.translation_scale,(3,))

    def image(self, call):
        k = self.effective(call['frame'])
        if call.get('image_frame', call['frame']) != k:
            raise ToolError('effective_image_required', f'requested {call["frame"]}, effective {k}; click image_frame={k}')
        return k

    def samples(self, k, points):
        values = np.asarray(self.depth_fn(k, np.asarray(points, dtype=float)), dtype=float)
        if values.shape != (len(points),):
            raise ToolError('invalid_depth_shape', str(values.shape))
        return values

    def click(self, requested, k, xy):
        x, y = [pixel(a) for a in xy]
        points = [(np.clip(x + dx, 0, 1000), np.clip(y + dy, 0, 1000))
                  for dx in (-10, -5, 0, 5, 10) for dy in (-10, -5, 0, 5, 10)]
        patch = self.samples(k, points)
        patch = patch[np.isfinite(patch) & (patch > 0)]
        if not len(patch):
            raise ToolError('invalid_patch', 'no finite positive depths')
        p20, p30, p50, p80 = np.percentile(patch, [20, 30, 50, 80], method='linear')
        cam = camera_ray([x, y], self.fov[self.anchors.index(k)]) * p30 * self.depth_scale
        _, r, c = self.camera(k)
        common = self.y_up @ (r @ cam + c)
        finite(cam,(3,));finite(common,(3,))
        spread=float((p80-p20)/p50)
        if not math.isfinite(spread):raise ToolError('invalid_patch','nonfinite patch spread')
        return {'requested_frame': requested, 'effective_frame': k, 'pixel': [x, y],
                'camera_m': cam.tolist(), 'f1_m': common.tolist(),
                'spread': spread}

    def execute(self, call):
        name = call['name']
        if name == 'depth_at':
            k = self.image(call)
            points = call.get('points', [[call.get('x'), call.get('y')]])
            return {'type': 'depth_at', 'points': [self.click(call['frame'], k, p) for p in points]}
        if name == 'pose':
            k, r, c = self.camera(call['frame'])
            level = self.y_up @ level_rotation(r, self.up).T
            return {'type': 'pose', 'requested_frame': call['frame'], 'effective_frame': k,
                    'f1_m': (self.y_up @ c).tolist(), 'camera_to_f1': (self.y_up @ r).tolist(),
                    'level_to_f1': level.tolist(),
                    'yaw_deg': round(math.degrees(math.atan2(-level[0, 2], level[2, 2])))}
        if name == 'move':
            a, ra, ca = self.camera(call['from'])
            b, _, cb = self.camera(call['to'])
            delta = level_rotation(ra, self.up) @ (cb - ca)
            return {'type': 'move', 'requested_from': call['from'], 'requested_to': call['to'],
                    'effective_from': a, 'effective_to': b, 'delta_m': delta.tolist(),
                    'distance_m': float(np.linalg.norm(delta)), 'dy_convention': 'positive_down'}
        if name == 'box_3d':
            k = self.image(call)
            x1, y1, x2, y2 = [call[key] for key in ('x1', 'y1', 'x2', 'y2')]
            if not (0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000):
                raise ToolError('malformed_box', str(call))
            xs = np.linspace(x1 + .1 * (x2-x1), x2 - .1 * (x2-x1), 12)
            ys = np.linspace(y1 + .1 * (y2-y1), y2 - .1 * (y2-y1), 12)
            xy = np.array([(x, y) for x in xs for y in ys])
            d = self.samples(k, xy)
            valid = np.where(np.isfinite(d) & (d > 0))[0]
            if not len(valid):
                raise ToolError('invalid_patch', 'box has no finite positive depths')
            keep = valid[np.argsort(d[valid], kind='stable')[:max(1, math.ceil(.6 * len(valid)))]]
            _, r, c = self.camera(k)
            pts = np.stack([self.y_up @ (r @ (camera_ray(xy[i], self.fov[self.anchors.index(k)])
                                              * d[i] * self.depth_scale) + c) for i in keep])
            finite(pts)
            lo, hi = pts.min(0), pts.max(0)
            return {'type': 'box_3d', 'requested_frame': call['frame'], 'effective_frame': k,
                    'f1_centre_m': ((lo+hi)/2).tolist(), 'sides_xyz_m': (hi-lo).tolist(), 'yaw_deg': 0.,
                    'backing': 'gravity_aligned_front_surface_aabb', 'retained_samples': len(keep)}
        raise ToolError('unknown_tool', name)


def render(output):
    """The JSON body is ordinary text, with explicit coordinates, units and frame identities."""
    if isinstance(output,dict) and output.get('type')=='depth_at':
        return '\n'.join(json.dumps({'type':'depth_at',**point,
                         'camera_axes':'OpenCV +x right,+y down,+z forward',
                         'f1_axes':'gravity aligned +x right,+y up,+z forward'},sort_keys=True,separators=(',',':'),allow_nan=False)
                         for point in output['points'])
    if isinstance(output,dict) and output.get('type') in ('pose','box_3d'):
        output={**output,'f1_axes':'gravity aligned +x right,+y up,+z forward'}
    if isinstance(output,dict) and output.get('type')=='move':
        output={**output,'axes':'local level +x right,+y down,+z forward'}
    return json.dumps(output, sort_keys=True, separators=(',', ':'), allow_nan=False)


def response(geometry, call):
    try:
        return geometry.execute(call)
    except (ToolError, ValueError, IndexError) as exc:
        return {'type': 'tool_error', 'code': getattr(exc, 'code', 'invalid_measurement'), 'detail': str(exc)}
