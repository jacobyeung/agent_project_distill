"""Read-only profiling hooks; no sealed file changes and no extra model forwards."""
import hashlib
import json
import math
import sys
import zlib
from pathlib import Path
import numpy as np

CAP_BYTES = 1_900_000_000


def plain(x):
    if hasattr(x, 'detach'):
        x = x.detach().cpu().numpy()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


def rle(mask):
    a = np.asarray(mask, dtype=bool)
    if a.ndim != 2:
        raise ValueError('mask must be H,W')
    f = a.ravel(order='F')
    edges = np.flatnonzero(f[1:] != f[:-1]) + 1
    counts = np.diff(np.r_[0, edges, f.size]).tolist()
    if f.size and f[0]:
        counts.insert(0, 0)
    return dict(size=list(a.shape), counts=counts, order='F')


def unrle(value):
    h, w = value['size']; counts = value['counts']
    if value.get('order') != 'F' or any(type(n) is not int or n < 0 for n in counts) or sum(counts) != h*w:
        raise ValueError('invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')


def summary(points, frames):
    p = np.asarray(points, float).reshape(-1, 3)
    if not np.isfinite(p).all():
        raise ValueError('nonfinite lift')
    return dict(point_count=len(p), centroid=p.mean(0).tolist() if len(p) else None,
                extent=(p.max(0)-p.min(0)).tolist() if len(p) else None,
                frame_count=len(set(map(int, frames))), frames=list(map(int, frames)),
                coordinate_frame='reader_gravity_world_metric')


def geometry_record(g):
    c = g.contract
    return dict(K=plain(g.K), canvas_to_source=plain(g.A), camera_to_world_metric=plain(g.C),
                camera_to_world_unscaled=plain(c.camera_to_world), scale=float(c.scale),
                source_indices=list(g.frame_map.source_indices),
                reference_source_frame=int(c.reference_source_frame),
                depth_scale_count=int(g.depth_scale_count), pose_scale_count=int(g.pose_scale_count),
                camera_axes=c.camera_axes, world_axes=c.world_axes, depth_kind=c.depth_kind,
                pixel_centres=c.pixel_centres, gravity_up=plain(c.gravity_up),
                depth_grid_sha256=hashlib.sha256(g.depth_grid.tobytes()).hexdigest(),
                identity=g.identity)


class Capture:
    """Observe exact function returns, including StageOne.select's complete slots.

    Code objects are supplied by the loaded reader, so an unrelated same-name
    function cannot enter the record. A single synchronous worker is required.
    """
    def __init__(self, stage_class, grounding):
        import inspect
        self.codes = {inspect.unwrap(stage_class.features).__code__: 'features',
                      inspect.unwrap(stage_class.select).__code__: 'select',
                      grounding.lift_bestspread.__code__: 'lift',
                      grounding.MinAreaBoxProvider.__call__.__code__: 'box'}
        self.objects = []
        self.by_name = {}
        self.geometry = None

    def __enter__(self):
        if sys.getprofile() is not None:
            raise RuntimeError('existing profiler; refuse to replace it')
        sys.setprofile(self.observe)
        return self

    def __exit__(self, *exc):
        sys.setprofile(None)

    def observe(self, frame, event, result):
        if event != 'return' or frame.f_code not in self.codes or result is None:
            return
        role = self.codes[frame.f_code]; v = frame.f_locals
        if role == 'features':
            obj, name = v['self'], v['name']
            if self.geometry is None:
                self.geometry = geometry_record(obj.geometry)
            raw = [dict(id=f'{f}:{i}', frame=f, source_index=self.geometry['source_indices'][f-1],
                        prompt=name, score=float(p['score']), presence=float(p['presence']), mask=rle(p['mask']))
                   for f, entries in enumerate(obj.raw[name], 1) for i, p in enumerate(entries)]
            tracks = [dict(id=c.id, members=[f'{p.frame}:{p.index}' for p in c.proposals],
                           features=plain(c.features)) for c in v['pools'][name]]
            candidates = [dict(id=c['candidate_id'], masks={str(f): rle(m) for f, m in c['masks'].items()},
                               features=plain(c['features'])) for c in v['accepted']]
            lifted = [dict(proposal=f'{p.frame}:{p.index}', summary=summary(p.points, [p.frame]))
                      for p in v['proposals']]
            record = dict(name=name, proposals=raw, linked_tracks=tracks, candidates=candidates,
                          early_lifts=lifted, early_rejections=plain(v['lift_outcomes']),
                          selector=dict(inputs=plain(v['x']), rule=obj.rule, slots=None,
                                        null_index=len(candidates), choice=-1, invoked=False),
                          selected_masks={}, lift=None, fitted_box=None)
            self.objects.append(record); self.by_name[name] = record
        elif role == 'select':
            rec = self.by_name[v['inputs']['name']]
            rec['selector'].update(slots=plain(v.get('slots')), choice=int(result), invoked=True,
                                   inputs=plain(v['inputs']['x']))
            if int(result) >= 0:
                rec['selected_masks'] = rec['candidates'][int(result)]['masks']
        elif role == 'lift':
            rec = self.by_name[v['name']]
            parts = [np.asarray(p, float).reshape(-1, 3) for p in result['points'].values()]
            rec['lift'] = summary(np.concatenate(parts) if parts else [], result['frames'])
            rec['lift'].update(best=result.get('best'), seen=bool(result['seen']),
                               point_frames=list(map(int, result['points'])))
        elif role == 'box':
            # min_area_box is fitted in reader world; the provider return is f1.
            self.by_name[v['name']]['fitted_box'] = dict(world=plain(v['raw']), f1=plain(result))


def validate(row):
    if row['schema'] != 'ground-capture-v1' or len(row['source_indices']) != 32:
        raise ValueError('schema/anchors')
    if len(set(row['source_indices'])) != 32:
        raise ValueError('duplicate anchors')
    for o in row['objects']:
        ids = {p['id'] for p in o['proposals']}
        for p in o['proposals']:
            if not 1 <= p['frame'] <= 32 or p['source_index'] != row['source_indices'][p['frame']-1]:
                raise ValueError('proposal frame')
            unrle(p['mask'])
        for t in o['linked_tracks']:
            if not set(t['members']) <= ids:
                raise ValueError('unbound track')
        s=o['selector']; n=len(o['candidates'])
        if len(s['inputs']) != n or s['null_index'] != n or not -1 <= s['choice'] < n:
            raise ValueError('selector shape/choice')
        if n and (not s['invoked'] or len(s['slots']) != n+1):
            raise ValueError('selector null slot missing')
        if not n and (s['invoked'] or s['slots'] is not None):
            raise ValueError('empty pool must preserve skipped selector')
        expected={} if s['choice'] == -1 else o['candidates'][s['choice']]['masks']
        if o['selected_masks'] != expected:
            raise ValueError('selection masks differ')
    if row['objects'] and row['geometry'] is None:
        raise ValueError('missing geometry')


class Writer:
    """One compressed JSON stream. A receipt is issued only after all-item parity."""
    def __init__(self, path, cap=CAP_BYTES):
        self.stream = Path(path).open('xb')
        self.codec = zlib.compressobj(6, zlib.DEFLATED, 31)
        self.cap=cap; self.bytes=0; self.items=0
    def _write(self, b):
        if self.bytes+len(b) > self.cap:
            raise RuntimeError('output byte cap exceeded; incomplete and untrusted')
        self.stream.write(b); self.bytes+=len(b)
    def append(self, row):
        validate(row)
        data=(json.dumps(row,separators=(',', ':'),allow_nan=False)+'\n').encode()
        self._write(self.codec.compress(data)+self.codec.flush(zlib.Z_SYNC_FLUSH))
        self.items+=1
    def close(self):
        self._write(self.codec.flush()); self.stream.close()
