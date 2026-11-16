"""Evaluation/training click labels. Runtime lift/controller are vla_where's implementations."""
import math
import numpy as np
from vla_where.nav import ClickTranslator, floor_plane, bearing_range, controller, travel
from vla_where.nav import CLICK
from .vendor import nav_text as NT

def relative(point, position, heading):
    d = np.asarray(point) - np.asarray(position)
    # Habitat forward is -Z; positive heading rotates left about +Y.
    forward = -math.sin(heading)*d[0] - math.cos(heading)*d[2]
    right = math.cos(heading)*d[0] - math.sin(heading)*d[2]
    return right, forward, d[1]

def project(point, position, heading, height=1.25):
    x, z, dy = relative(point, position, heading)
    if z <= 0:
        return None
    return (.5 + .5*x/z, .5 + .5*(height-dy)/z)

def lead_point(path, metres=2.):
    points = [np.asarray(p, float) for p in path]
    if not points:
        raise ValueError('Empty lead path')
    for a, b in zip(points, points[1:]):
        length = float(np.linalg.norm(b-a))
        if length >= metres and length > 0:
            return a + (b-a)*metres/length
        metres -= length
    return points[-1]

def gt_lead_point(locations, position, metres=None):
    """Interpolate along GT from the nearest 3-D location; first index wins ties."""
    points = np.asarray(locations, float)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points):
        raise ValueError('Need a nonempty GT path of 3-D locations')
    nearest = int(np.argmin(np.linalg.norm(points-np.asarray(position), axis=1)))
    return lead_point(points[nearest:], CLICK['max_leg_m'] if metres is None else metres)

def label(position, heading, point, goal_distance, history_frames=32, depth=None):
    if goal_distance < 1.0:
        return 'stop', 'stop'
    x, z, _ = relative(point, position, heading)
    beta = math.degrees(math.atan2(-x, z))
    uv = project(point, position, heading)
    if uv is not None and 0 <= uv[0] < 1 and uv[1] >= 0:
        if uv[1] >= 1:
            return NT.click_text(history_frames, uv[0], .99), 'near_point_clamp'
        if depth is None or abs(float(depth(uv)) - z) <= .3:
            return NT.click_text(history_frames, uv[0], uv[1]), 'click'
    return ('turn_around' if abs(beta) > 135 else 'turn_left 90' if beta >= 0 else 'turn_right 90'), 'out_of_view'
