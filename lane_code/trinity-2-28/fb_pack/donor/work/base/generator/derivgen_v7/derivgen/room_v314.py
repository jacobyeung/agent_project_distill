"""Mask-free room footprint from metric depth and gravity-aligned poses.

The sensor rule is programs.floor_area used by prog_v2. Predicted geometry
uses geomswap.floor_area_vote: distinct-frame votes before closing and filling.
The height is a lower cutoff, not a fitted floor plane. Every point above it
contributes to the footprint, including points on furniture and walls.
"""
import re
import numpy as np
from scipy import ndimage
from trace_format.room_v314 import format_result

CALL = '<ground mode="room">'
CELL_M = .05
CLOSING_M = .20
MIN_POINTS = 100
MAX_GRID_CELLS = 4_000_000
PARAMETERS = dict(cell_m=CELL_M, closing_radius_m=CLOSING_M,
                  height_percentile=1, height_margin_m=.10, min_points=MIN_POINTS,
                  head_raster_hw=[240, 320], pixel_stride=4, max_grid_cells=MAX_GRID_CELLS)


class RoomRefusal(ValueError):
    def __init__(self, code):
        self.code = 'room_' + code
        super().__init__(self.code)


def _finite(value):
    if not np.isfinite(value).all():
        raise RoomRefusal('nonfinite')


def _frames(geo):
    valid = getattr(geo, 'valid', None)
    if valid is not None:
        count = len(valid)
    else:
        count = 32
    if not 1 <= count <= 32:
        raise RoomRefusal('invalid_geometry')
    has = getattr(geo, 'has', lambda k: True)
    pose = getattr(geo, 'has_pose', lambda k: True)
    frames = [k for k in range(1, count + 1)
              if (valid is None or bool(valid[k-1])) and has(k) and pose(k)]
    frame_of = getattr(geo, 'frame_of', lambda k: k)
    # Repeated views cannot supply independent votes.
    frames = sorted(set(frame_of(k) for k in frames))
    if len(frames) < 2:
        raise RoomRefusal('too_few_frames')
    return frames


def _dense(geo, frame):
    """Use native sensor pixels, or the reference 240x320 raster for heads."""
    R, t = (np.asarray(v) for v in geo.cam(frame))
    if R.shape != (3, 3) or t.shape != (3,):
        raise RoomRefusal('invalid_geometry')
    _finite(R); _finite(t)
    if not np.allclose(R @ R.T, np.eye(3), atol=1e-4) or np.linalg.det(R) < 0:
        raise RoomRefusal('invalid_geometry')
    depth = getattr(geo, 'depth', None)
    if isinstance(depth, np.ndarray):
        D = depth[frame - 1][::4, ::4]
        _finite(D)
        ys, xs = np.nonzero(D > 0)
        pix = np.stack([xs * 4 + .5, ys * 4 + .5, np.ones(len(xs))], 1)
        Ks = getattr(geo, 'K_frames', None)
        if Ks is None:
            Ks = getattr(geo, 'Ks', None)
        K = np.asarray(Ks[frame - 1] if Ks is not None else geo.K)
        _finite(K)
        if K.shape != (3, 3) or min(K[0, 0], K[1, 1]) <= 0:
            raise RoomRefusal('invalid_geometry')
        pc = (pix @ np.linalg.inv(K).T) * D[ys, xs][:, None]
    else:
        # Endpoint-grid bilinear depth is rounded to float32 exactly as the
        # priced raster export. Never use HeadSource.dense's sparse grid nodes.
        ys, xs = np.mgrid[0:240:4, 0:320:4]
        uv = np.stack([(xs.ravel()+.5)/320*1000, (ys.ravel()+.5)/240*1000], 1)
        index = frame - 1
        if hasattr(geo, '_g'):
            index = geo._g(frame)
        elif getattr(geo, 'grid', np.empty((32,))).shape[0] == 16:
            index = frame // 2 - 1
        head_geometry = getattr(geo, 'geometry', None)
        if hasattr(head_geometry, 'grids'):
            head_geometry = head_geometry.geometry
        own = hasattr(geo, 'grids') and hasattr(head_geometry, 'fov')
        if own:
            # Read one 51x51 grid from the live depth head, as mask lifting does.
            if frame not in geo.grids:
                axis = np.linspace(0, 1000, 51, dtype=np.float32)
                u, v = np.meshgrid(axis, axis)
                values = np.asarray(head_geometry.depth(frame, np.column_stack((u.ravel(), v.ravel()))), dtype=np.float32)
                if values.shape != (2601,):
                    raise RoomRefusal('invalid_geometry')
                geo.grids[frame] = values.reshape(51, 51)
            grid = geo.grids[frame]
            _finite(grid)
            x, y = np.clip(uv * .05, 0, 50).T
            x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
            x1, y1 = np.minimum(x0+1, 50), np.minimum(y0+1, 50)
            fx, fy = x-x0, y-y0
            d = (grid[y0,x0]*(1-fx)*(1-fy)+grid[y0,x1]*fx*(1-fy)
                 +grid[y1,x0]*(1-fx)*fy+grid[y1,x1]*fx*fy).astype(np.float32)
        else:
            d = np.asarray(geo._depth(index, uv[:, 0], uv[:, 1]), dtype=np.float32)
        _finite(d)
        if hasattr(geo, 'rays'):
            rays = geo.rays(frame, uv)
        else:
            fh, fw = head_geometry.fov(frame) if own else geo.fov_of(frame)
            _finite([fh, fw])
            if not (0 < fh < np.pi and 0 < fw < np.pi):
                raise RoomRefusal('invalid_geometry')
            K = np.array([[160/np.tan(fw/2), 0, 160],
                          [0, 120/np.tan(fh/2), 120], [0, 0, 1]])
            pix = np.stack([xs.ravel()+.5, ys.ravel()+.5, np.ones(xs.size)], 1)
            rays = pix @ np.linalg.inv(K).T
        _finite(rays)
        pc = rays[d > 0] * d[d > 0, None]
    return pc @ R.T + t


def sample(geometry, geometry_mode='sensor'):
    if geometry_mode not in ('sensor', 'predicted'):
        raise ValueError('geometry_mode must be sensor or predicted')
    # GT row geometry otherwise uses a frame-1 basis. A discrete occupancy
    # raster is not exactly yaw invariant: preserve the native label basis.
    geo = getattr(geometry, 'room_geometry', geometry) if geometry_mode == 'sensor' else geometry
    if geo is None:
        raise RoomRefusal('geometry_unavailable')
    try:
        frames = _frames(geo)
        points = [_dense(geo, k) for k in frames]
    except RoomRefusal:
        raise
    except (AttributeError, IndexError, TypeError, ValueError, np.linalg.LinAlgError) as exc:
        raise RoomRefusal('invalid_geometry') from exc
    return dict(points=points, frames=frames, geometry_mode=geometry_mode,
                gravity_source='scene_z_up' if geometry_mode == 'sensor'
                else str(getattr(geo, 'gravity_source', 'own' if hasattr(geo, 'grids') else 'geometry_z_up')))


def measure(geometry, geometry_mode='sensor'):
    return from_points(**sample(geometry, geometry_mode))


def from_points(points, frames, geometry_mode, *, gravity_source):
    """Pure kernel; frames identify distinct sampled views in a z-up world."""
    if geometry_mode not in ('sensor', 'predicted'):
        raise ValueError('geometry_mode must be sensor or predicted')
    if len(frames) < 2:
        raise RoomRefusal('too_few_frames')
    if (len(frames) != len(points) or sorted(set(frames)) != list(frames)
            or any(type(k) is not int or not 1 <= k <= 32 for k in frames)):
        raise RoomRefusal('invalid_geometry')
    pts = [np.asarray(p) for p in points]
    for p in pts:
        if p.ndim != 2 or p.shape[1] != 3:
            raise RoomRefusal('invalid_geometry')
        _finite(p)
    P = np.concatenate(pts)
    if len(P) < MIN_POINTS:
        raise RoomRefusal('no_floor_seen')
    height = float(np.percentile(P[:, 2], 1) - .1)
    _finite([height])
    above = P[P[:, 2] > height]
    if not len(above):
        raise RoomRefusal('no_floor_seen')
    lo = above[:, :2].min(0)
    extent = (P[:, :2].max(0) - lo) / CELL_M
    if not np.isfinite(extent).all() or np.any(extent > MAX_GRID_CELLS):
        raise RoomRefusal('extent_limit')
    cells = [np.unique(((p[p[:, 2] > height, :2] - lo) / CELL_M).astype(np.int64), axis=0)
             for p in pts]
    ij = np.concatenate(cells)
    shape = ij.max(0) + 1
    if any(int(n) <= 0 for n in shape) or int(shape[0]) * int(shape[1]) > MAX_GRID_CELLS:
        raise RoomRefusal('extent_limit')
    votes = np.zeros(shape, np.uint8)
    np.add.at(votes, (ij[:, 0], ij[:, 1]), 1)
    threshold = 1 if geometry_mode == 'sensor' else 2
    grid = votes >= threshold
    supported = int(grid.sum())
    if not supported:
        raise RoomRefusal('no_floor_seen')
    r = int(round(CLOSING_M / CELL_M))
    yy, xx = np.mgrid[-r:r+1, -r:r+1]
    grid = ndimage.binary_closing(np.pad(grid, r+1), structure=xx**2 + yy**2 <= r*r)
    grid = ndimage.binary_fill_holes(grid)
    count = int(grid.sum())
    if not count:
        raise RoomRefusal('no_floor_seen')
    area = float(count * CELL_M * CELL_M)
    _finite([height, area])
    if float(f'{area:.2f}') <= 0:
        raise RoomRefusal('no_floor_seen')
    return dict(frames=list(frames), floor_height_m=height, area_m2=area,
                floor_cells=count, supported_cells=supported, min_frames=threshold,
                geometry_mode=geometry_mode, gravity_source=gravity_source, **PARAMETERS)


def parse_response(body):
    f = r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}'
    m = re.fullmatch(r'room: frames ([1-9][0-9]*(?:,[1-9][0-9]*)*)\n'
                     r'floor height ('+f+r') m\nfloor cells ([1-9][0-9]*); '
                     r'supported cells ([1-9][0-9]*); cell size 0.05 m; min frames ([12])\n'
                     r'area ('+f+r') m\^2', body)
    if not m:
        raise ValueError('malformed_room_response')
    frames = [int(k) for k in m[1].split(',')]
    if len(frames) < 2 or frames != sorted(set(frames)) or frames[-1] > 32:
        raise ValueError('malformed_room_frames')
    expected = f'{int(m[3]) * CELL_M * CELL_M:.2f}'
    if m[6] != expected or float(m[6]) <= 0:
        raise ValueError('room_area_cell_mismatch')
    return dict(frames=frames, floor_height_m=float(m[2]), floor_cells=int(m[3]),
                supported_cells=int(m[4]), min_frames=int(m[5]), area_m2=float(m[6]))
