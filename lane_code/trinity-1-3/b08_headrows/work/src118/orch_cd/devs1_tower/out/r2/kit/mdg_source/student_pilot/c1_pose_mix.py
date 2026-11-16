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


def validate_spec(spec):
    if spec.get('schema') != SCHEMA or not isinstance(spec.get('sources'), list) or not spec['sources']:
        raise ValueError('Pose mix needs schema c1-pose-mix-v1 and a source list')
    for source in spec['sources']:
        kind = source.get('kind') if isinstance(source, dict) else None
        if kind == 'c1r_clips':
            if set(source) != CLIP_KEYS or source['layout'] not in ('duplicate', 'paired', 'spread') \
                    or type(source['count']) is not int or source['count'] < 1:
                raise ValueError('C1-r clip source fields differ')
        elif kind == 'rows':
            if set(source) != ROW_KEYS or not (source['frame_prefix'] is None or isinstance(source['frame_prefix'], str)):
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


def prepare(spec_pin, output, benchmark, reported, excluded):
    """Freeze the mix population. Returns (stream entry, settings receipt of the row source)."""
    spec = validate_spec(load(pinned(spec_pin)))
    entries, order, settings = [], [], None
    totals = dict(benchmark_rows_dropped=0, reported_overlap_rows=0)
    for k, source in enumerate(spec['sources']):
        if source['kind'] == 'c1r_clips':
            pinned(source['dense_plan']); pinned(source['teacher']); pinned(source['model'])
            rows = 0
            with pinned(source['clips_plan']).open() as handle:
                for i, line in enumerate(handle):
                    row = json.loads(line)
                    if row['i'] != i or row['layout'] != source['layout']:
                        raise ValueError('Clip plan order or layout differs')
                    rows += 1
            if rows != source['count']:
                raise ValueError('Clip plan count differs from the mix spec')
            entries.append({**source})
            order += [[k, i] for i in range(rows)]
            continue
        receipt = load(pinned(source['receipt']))
        if (receipt.get('schema') not in ROW_SCHEMAS or receipt['settings']['anchors'] != list(range(1, 33))
                or receipt['settings']['temporal_grouping'] != 'fused_pairs_all_frames'):
            raise ValueError('Pose-row source must be an all-frame A1-schema stream')
        if settings is None:
            settings = receipt
        elif receipt['inputs']['division'] != settings['inputs']['division'] or receipt['model'] != settings['model']:
            raise ValueError('Pose-row sources disagree on division or model')
        pinned(receipt['database'])
        selected = []
        with connect(receipt['database']) as conn:
            for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
                row, target = json.loads(row), json.loads(target)
                if not _row_selected(row, target, source['frame_prefix']):
                    continue
                hit, overlap = excluded(row, benchmark, reported)
                totals['reported_overlap_rows'] += overlap
                if hit:
                    totals['benchmark_rows_dropped'] += 1
                    continue
                selected.append(index)
        if not selected:
            raise ValueError('Pose-row source selected no rows')
        entries.append(dict(kind='rows', receipt=source['receipt'], database=receipt['database'],
                            frame_prefix=source['frame_prefix'], count=len(selected)))
        order += [[k, i] for i in selected]
    if settings is None:
        raise ValueError('Pose mix needs one A1-schema row source for settings, model and division')
    path = Path(output)/'pose_mix_order.json'
    write(path, order)
    entry = dict(receipt=spec_pin, kind='mix', sources=entries, count=len(order), order=file_pin(path),
                 teacher_rows=sum(e['count'] for e in entries if e['kind'] == 'c1r_clips'), **totals)
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
