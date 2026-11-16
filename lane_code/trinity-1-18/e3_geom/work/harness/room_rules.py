"""Lane room rules; R0 remains the imported deployed kernel."""
import numpy as np
from scipy import ndimage
from trace_format import room_v314 as room


def r1(points, frames, geometry_mode, *, gravity_source):
    """Use the R0 raster kernel with a bounded floor voting band."""
    if geometry_mode not in ('sensor', 'predicted'):
        raise ValueError('geometry_mode must be sensor or predicted')
    if len(frames) < 2:
        raise room.RoomRefusal('too_few_frames')
    if (len(frames) != len(points) or sorted(set(frames)) != list(frames)
            or any(type(k) is not int or not 1 <= k <= 32 for k in frames)):
        raise room.RoomRefusal('invalid_geometry')
    pts = [np.asarray(p) for p in points]
    for p in pts:
        if p.ndim != 2 or p.shape[1] != 3:
            raise room.RoomRefusal('invalid_geometry')
        room._finite(p)
    P = np.concatenate(pts)
    if len(P) < room.MIN_POINTS:
        raise room.RoomRefusal('no_floor_seen')
    height = float(np.percentile(P[:, 2], 1) - .1)
    room._finite([height])
    band = [p[(p[:, 2] > height) & (p[:, 2] <= height + .40)] for p in pts]
    above = np.concatenate(band)
    if not len(above):
        raise room.RoomRefusal('no_floor_seen')
    lo = above[:, :2].min(0)
    extent = (P[:, :2].max(0) - lo) / room.CELL_M
    if not np.isfinite(extent).all() or np.any(extent > room.MAX_GRID_CELLS):
        raise room.RoomRefusal('extent_limit')
    cells = [np.unique(((p[:, :2] - lo) / room.CELL_M).astype(np.int64), axis=0) for p in band]
    ij = np.concatenate(cells)
    shape = ij.max(0) + 1
    if any(int(n) <= 0 for n in shape) or int(shape[0]) * int(shape[1]) > room.MAX_GRID_CELLS:
        raise room.RoomRefusal('extent_limit')
    votes = np.zeros(shape, np.uint8)
    np.add.at(votes, (ij[:, 0], ij[:, 1]), 1)
    threshold = 1 if geometry_mode == 'sensor' else 2
    grid = votes >= threshold
    supported = int(grid.sum())
    if not supported:
        raise room.RoomRefusal('no_floor_seen')
    radius = int(round(room.CLOSING_M / room.CELL_M))
    yy, xx = np.mgrid[-radius:radius+1, -radius:radius+1]
    grid = ndimage.binary_closing(np.pad(grid, radius+1), structure=xx**2 + yy**2 <= radius*radius)
    grid = ndimage.binary_fill_holes(grid)
    count = int(grid.sum())
    area = float(count * room.CELL_M * room.CELL_M)
    if not count or float(f'{area:.2f}') <= 0:
        raise room.RoomRefusal('no_floor_seen')
    return dict(frames=list(frames), floor_height_m=height, area_m2=area,
                floor_cells=count, supported_cells=supported, min_frames=threshold,
                geometry_mode=geometry_mode, gravity_source=gravity_source, **room.PARAMETERS)
