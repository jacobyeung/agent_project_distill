"""Final-mode composite pose stream: teacher-covered C1-r dense-plan clips plus pose-row
databases without teacher targets (A2), sampled as one shuffled population.

Every row carries `aux_g3t_cam`/`aux_g3t_valid` (zero teacher weight when uncovered) and
the point-depth target keys, so every rank runs the same pose graph in a pose microstep.
"""
import json
from pathlib import Path
import sqlite3

import torch

from . import carrier_c1_data as data
from .p3_provenance import file_pin, load, pinned, write

SCHEMA = 'c1-pose-mix-v1'
CLIP_KEYS = {'kind', 'clips_plan', 'dense_plan', 'teacher', 'cache_root', 'model', 'layout', 'count'}
ROW_KEYS = {'kind', 'receipt', 'frame_prefix'}
ROW_SCHEMAS = ('pose-stream-a2-v1', 'decoupled-v-preparation-v1')
# Row streams in A1's all_frames32 row/target schema whose receipts carry no settings, model or
# division (A3). They need the spec-level division; settings and model come from an A1-schema source.
ROWS_ONLY_SCHEMAS = {'pose-stream-a3-v1': 'A1 all_frames32 pose-only rows; every slot carries depth',
                     'pose-stream-a4-v1': 'A1 all_frames32 pose-only rows; every slot carries depth',
                     'pose-stream-a4m-v1': 'A1 all_frames32 pose-only rows; A3 layout; MP3D rooms'}
DIVISION_SCHEMA = 'diagnostic-whole-scene-division-v1'


def _pin(value):
    return (isinstance(value, dict) and set(value) == {'path', 'sha256'} and isinstance(value['path'], str)
            and isinstance(value['sha256'], str))


def validate_spec(spec):
    from .pose_source_guard import refuse_a4_r_s
    refuse_a4_r_s(spec)
    if spec.get('schema') != SCHEMA or not isinstance(spec.get('sources'), list) or not spec['sources']:
        raise ValueError('Pose mix needs schema c1-pose-mix-v1 and a source list')
    if 'division' in spec and (set(spec) - {'schema', 'sources', 'division'} or not _pin(spec['division'])):
        raise ValueError('Pose mix spec fields differ')
    for source in spec['sources']:
        kind = source.get('kind') if isinstance(source, dict) else None
        if kind == 'c1r_clips':
            if set(source) != CLIP_KEYS or source['layout'] not in ('duplicate', 'paired', 'spread') \
                    or type(source['count']) is not int or source['count'] < 1:
                raise ValueError('C1-r clip source fields differ')
        elif kind == 'rows':
            if (set(source) not in (ROW_KEYS, ROW_KEYS | {'count'})
                    or not (source['frame_prefix'] is None or isinstance(source['frame_prefix'], str))
                    or ('count' in source and (type(source['count']) is not int or source['count'] < 1))):
                raise ValueError('Pose-row source fields differ')
        else:
            raise ValueError('Unknown pose mix source kind')
    return spec


def depth_placeholders(points):
    return dict(aux_point_depth_uv=torch.zeros(1, 32, points, 2),
                aux_point_depth_gt=torch.zeros(1, 32, points),
                aux_point_depth_mask=torch.zeros(1, 32, points, dtype=torch.bool))


def connect(pin):
    return sqlite3.connect(Path(pin['path']).as_uri()+'?mode=ro', uri=True)


def _row_selected(row, target, prefix):
    from .carrier_c1_sweep import dense_pose_row
    if not dense_pose_row(row, target):
        return False
    if prefix is None:
        return True
    return all(f['path'].startswith(prefix) for f in row['student_input']['frames'])


def _division(pin):
    """(division, train scenes, held-out scenes) of a pinned training-only whole-scene division."""
    division = load(pinned(pin))
    if division.get('schema') != DIVISION_SCHEMA or division.get('training_only') is not True:
        raise ValueError('Pose mix division must be a training-only whole-scene division')
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    if not train or train & heldout:
        raise ValueError('Pose mix division train and held-out scenes overlap')
    return division, train, heldout


MAX_ANCESTRY = 4


def ancestor_admits(division_pin, ancestor_pin):
    """True when ancestor_pin is division_pin or reached through parent_division links (at most
    MAX_ANCESTRY) where every child keeps its parent's train scenes on the train side and its parent's
    held-out scenes held out (A4 extends A3, which extends A1). Rows built under the ancestor lie in its
    train scenes, so they can never touch a held-out scene of the descendant."""
    if division_pin == ancestor_pin:
        return True
    try:
        child_pin, child = division_pin, _division(division_pin)
        for _ in range(MAX_ANCESTRY):
            parent_pin = child[0].get('parent_division')
            if not _pin(parent_pin):
                return False
            parent = _division(parent_pin)
            if not (parent[1] <= child[1] and parent[2] <= child[2]):
                return False
            if parent_pin == ancestor_pin:
                return True
            child_pin, child = parent_pin, parent
    except ValueError:
        return False
    return False


def _admitted_division(run_pin, run, source_pin):
    """The mix division itself, or an ancestor whose train scenes every link keeps on the train side
    and whose held-out scenes every link keeps held out."""
    return ancestor_admits(run_pin, source_pin)


def _clip_scenes(source):
    """recording_fingerprint -> 'dataset/scene' for every recording of the clips' pinned A1 plan."""
    from .c1r_clips import fingerprint, load_a1
    scenes = load_a1(load(pinned(source['dense_plan']))['a1_plan'])
    return {fingerprint(scene): f"{scene['dataset']}/{scene['scene']}" for scene in scenes}


def _a1_schema_row(row):
    sample = row.get('pose_sample', {})
    return sample.get('anchors') == list(range(1, 33)) and sample.get('temporal_grouping') == 'fused_pairs_all_frames'


def prepare(spec_pin, output, benchmark, reported, excluded, check=None):
    """Freeze the mix population. Returns (stream entry, settings receipt of the row source).

    With a spec-level division, every row source must pin that division or its admitted parent
    (rows-only sources pin none), every selected row's scene must be a train scene of that division,
    and the returned settings carry that division. A row source's optional `count` is the number of
    rows it must select before benchmark exclusion. `check(row, target)` validates each selected row
    before training encodes it and returns the (min, max) of its masked point-depth uv, or None."""
    spec = validate_spec(load(pinned(spec_pin)))
    run_pin = spec.get('division')
    run = _division(run_pin) if run_pin is not None else None
    entries, order, settings = [], [], None
    totals = dict(benchmark_rows_dropped=0, reported_overlap_rows=0)
    for k, source in enumerate(spec['sources']):
        if source['kind'] == 'c1r_clips':
            pinned(source['dense_plan']); pinned(source['teacher']); pinned(source['model'])
            scenes = _clip_scenes(source) if run is not None else None
            rows, outside = 0, 0
            with pinned(source['clips_plan']).open() as handle:
                for i, line in enumerate(handle):
                    row = json.loads(line)
                    if row['i'] != i or row['layout'] != source['layout']:
                        raise ValueError('Clip plan order or layout differs')
                    if scenes is not None and scenes.get(row['recording_fingerprint']) not in run[1]:
                        outside += 1
                    rows += 1
            if outside:
                raise ValueError(f'Clip source {k} has {outside} clips outside the pose mix division train scenes')
            if rows != source['count']:
                raise ValueError('Clip plan count differs from the mix spec')
            entries.append({**source})
            order += [[k, i] for i in range(rows)]
            continue
        receipt = load(pinned(source['receipt']))
        from .pose_source_guard import refuse_a4_r_s
        refuse_a4_r_s(receipt)
        rows_only = receipt.get('schema') in ROWS_ONLY_SCHEMAS
        if rows_only:
            if run is None:
                raise ValueError('A rows-only pose source needs the pose mix division')
            if (receipt.get('row_schema') != ROWS_ONLY_SCHEMAS[receipt['schema']]
                    or receipt.get('test_scene_hits_in_rows') != 0 or type(receipt.get('count')) is not int):
                raise ValueError('Rows-only pose source must be an all-frame A1-schema stream')
        else:
            if (receipt.get('schema') not in ROW_SCHEMAS or receipt['settings']['anchors'] != list(range(1, 33))
                    or receipt['settings']['temporal_grouping'] != 'fused_pairs_all_frames'):
                raise ValueError('Pose-row source must be an all-frame A1-schema stream')
            if run is not None and not _admitted_division(run_pin, run, receipt['inputs']['division']):
                raise ValueError('Pose-row source division is neither the mix division nor its admitted parent')
            if settings is None:
                settings = receipt
            elif ((run is None and receipt['inputs']['division'] != settings['inputs']['division'])
                    or receipt['model'] != settings['model']):
                raise ValueError('Pose-row sources disagree on division or model')
        pinned(receipt['database'])
        selected, outside, hits, uv = [], 0, 0, None
        with connect(receipt['database']) as conn:
            if rows_only and conn.execute('SELECT count(*) FROM rows').fetchone()[0] != receipt['count']:
                raise ValueError('Rows-only pose source count differs from its receipt')
            for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
                row, target = json.loads(row), json.loads(target)
                if not _row_selected(row, target, source['frame_prefix']):
                    continue
                if rows_only and not _a1_schema_row(row):
                    raise ValueError('Rows-only pose source row is not an all-frame A1-schema row')
                if run is not None and f"{row['dataset']}/{row['scene']}" not in run[1]:
                    outside += 1
                    continue
                if check is not None:
                    try:
                        span = check(row, target)
                    except Exception as error:
                        raise ValueError(f'Pose source {k} row {index} fails the training row check: {error}') from error
                    if span is not None:
                        uv = list(span) if uv is None else [min(uv[0], span[0]), max(uv[1], span[1])]
                hit, overlap = excluded(row, benchmark, reported)
                totals['reported_overlap_rows'] += overlap
                if hit:
                    hits += 1
                    continue
                selected.append(index)
        totals['benchmark_rows_dropped'] += hits
        counts = dict(source=k, selected=len(selected), benchmark_rows_dropped=hits, division_rows_outside=outside,
                      expected=source.get('count'), uv_range=uv)
        print(json.dumps({'pose_mix_source': counts}), flush=True)
        if outside:
            raise ValueError(f'Pose source {k} has {outside} selected rows outside the mix division train scenes')
        if 'count' in source and len(selected) + hits != source['count']:
            raise ValueError(f'Pose source {k} selected {len(selected) + hits} rows; the spec expects {source["count"]}')
        if not selected:
            raise ValueError('Pose-row source selected no rows')
        part = dict(kind='rows', receipt=source['receipt'], database=receipt['database'],
                    frame_prefix=source['frame_prefix'], count=len(selected))
        if run is not None or check is not None:
            part.update(benchmark_rows_dropped=hits, uv_range=uv)
        entries.append(part)
        order += [[k, i] for i in selected]
    if settings is None:
        raise ValueError('Pose mix needs one A1-schema row source for settings, model and division')
    if run is not None:
        settings = {**settings, 'inputs': {**settings['inputs'], 'division': run_pin}}
    path = Path(output)/'pose_mix_order.json'
    write(path, order)
    entry = dict(receipt=spec_pin, kind='mix', sources=entries, count=len(order), order=file_pin(path),
                 teacher_rows=sum(e['count'] for e in entries if e['kind'] == 'c1r_clips'), **totals)
    if run is not None:
        entry['division'] = run_pin
    return entry, settings


class ClipSource:
    """C1-r ClipRows over the dense teacher store (cache_root); every row is teacher-covered."""
    def __init__(self, source, processor, placement, points, wait_timeout=120.):
        from .c1r_data import ClipRows, processor_identity
        cfg = dict(streams=dict(clips_plan=source['clips_plan'], dense_plan=source['dense_plan']),
                   teacher=source['teacher'], cache_root=source['cache_root'], model=source['model'],
                   frames=dict(layout=source['layout']), carrier_placement=placement,
                   max_sequence_tokens=16384, align=dict(cam=dict(layer='final', weight=0.), patch=None))
        receipt = dict(schema='c1r-dense-binding-v2', plan=source['clips_plan'], teacher=source['teacher'],
                       cache_root=source['cache_root'], dense_plan=source['dense_plan'],
                       processor=processor_identity(load(pinned(source['model']))))
        # A missing record must surface as a row error within minutes, never a 45-min wait.
        self.rows = ClipRows(receipt, processor, cfg, wait_timeout=wait_timeout, wait_poll=5.)
        if len(self.rows.plan) != source['count']:
            raise ValueError('Clip plan count differs')
        self.points = points

    def get(self, index):
        batch, targets, audit = self.rows.get_dense(index)
        targets = {**targets, **depth_placeholders(self.points), 'aux_g3t_valid': torch.ones(1, dtype=torch.bool)}
        if tuple(targets['aux_g3t_cam'].shape) != (1, 32, 2048):
            raise ValueError('Teacher camera tokens must be [1, 32, 2048]')
        return batch, targets, {**audit, 'source': 'c1r_clips'}

    def close(self):
        self.rows.close()


class RowSource:
    """A1-schema pose rows (A2); no teacher target: zero teacher weight, full pose loss."""
    def __init__(self, source, processor, placement, mode, layout, gap):
        self.conn = connect(source['database'])
        self.processor, self.placement, self.mode, self.layout, self.gap = processor, placement, mode, layout, gap

    def get(self, index):
        from .c1r_align import uncovered_targets
        found = self.conn.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
        if found is None:
            raise ValueError('Missing planned pose-mix row')
        row, target = json.loads(found[0]), json.loads(found[1])
        options = {} if self.layout == 'spread' else dict(frame_layout=self.layout, frame_pair_gap_seconds=self.gap)
        batch, targets, audit = data.encode(self.processor, row, target, 'pose', self.placement, self.mode, **options)
        return batch, {**targets, **uncovered_targets()}, {**(audit or {}), 'source': 'rows', 'dataset': row.get('dataset')}

    def close(self):
        self.conn.close()


class PoseMix:
    def __init__(self, entry, processor, placement, mode, layout, gap, points):
        self.order = load(pinned(entry['order']))
        if len(self.order) != entry['count']:
            raise ValueError('Pose mix order differs from its count')
        self.sources = [ClipSource(s, processor, placement, points) if s['kind'] == 'c1r_clips'
                        else RowSource(s, processor, placement, mode, layout, gap) for s in entry['sources']]

    def get(self, index):
        k, i = self.order[index]
        return self.sources[k].get(i)

    def close(self):
        for source in self.sources:
            source.close()
