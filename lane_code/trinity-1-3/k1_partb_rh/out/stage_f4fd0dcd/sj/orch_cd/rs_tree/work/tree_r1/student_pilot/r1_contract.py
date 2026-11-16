"""Fail-closed repair trace admission. A renderer checksum is not source evidence."""
from copy import deepcopy
from pathlib import Path
import json
import sqlite3
from contextlib import closing
from . import r1_evidence as evidence
from .p3_provenance import pinned, load, digest
from . import r2_trace

CONTRACT = r2_trace.CONTRACT


def row_binding(row):
    """Freeze trusted membership before training; never derive this from a live row."""
    return {k: deepcopy(row.get(k)) for k in
            ('qid', 'source_qid', 'canonical', 'dataset', 'scene', 'room', 'question',
             'options', 'question_type', 'frames_pending', 'provenance', 'repair', 'target', 'answer', 'student_input',
             'events', 'tool_output_spans', 'form', 'trace_revision', 'trace_r2', 'ground_record', 'routing')}


def validate(row, *, expected=None, exclusions=None, require_frames=False):
    if row.get('routing'):
        r2_trace.encoded(row)
    elif row.get('events'):
        from .carrier_c1_routing import check_row
        check_row(row)
    else:
        r2_trace.direct(row)
    inputs = row.get('student_input', {})
    provenance = row.get('provenance', {})
    pending = row.get('frames_pending') or provenance.get('frames_pending')
    if pending is not None and (pending.get('d') != row.get('dataset')
            or pending.get('s') != row.get('scene')
            or pending.get('i') != inputs.get('frame_indices')):
        raise ValueError('Wrong scene or frame lineage')
    if row.get('canonical') and provenance.get('canonical', row['canonical']) != row['canonical']:
        raise ValueError('Wrong scene or frame lineage')
    if expected is not None:
        actual = digest(row_binding(row)) if isinstance(expected, str) else row_binding(row)
        if actual != expected:
            raise ValueError('Stale pin or row differs from sealed source membership')
    if exclusions is not None and exclusions.excluded(row):
        raise ValueError('Excluded benchmark or held-out scene')
    if require_frames:
        frames = inputs.get('frames')
        if not isinstance(frames, list) or len(frames) != 32:
            raise ValueError('R1 requires 32 pinned native RGB frames')
        if len(inputs['frame_indices']) != 32 or inputs['frame_indices'] != sorted(set(inputs['frame_indices'])):
            raise ValueError('R1 frame order')
        for frame in frames:
            from .r3_frames import verify_frame
            verify_frame(frame)
    return row


class Admission:
    """Read a pinned, reviewed membership manifest once; enforce it on each read."""
    def __init__(self, spec):
        from .s1_exclusions import Exclusions
        if spec.get('contract') != CONTRACT:
            raise ValueError('R1 contract version')
        manifest = pinned(spec['membership'])
        if manifest.stat().st_size > 20_000_000:
            raise ValueError('Large R1 membership must use a pinned SQLite database')
        self.members = load(manifest)
        self.exclusions = Exclusions(spec['exclusions']['dev'], spec['exclusions']['benchmark'])
        if self.members.get('schema') != 'r1-trace-membership-v1':
            raise ValueError('R1 membership schema')
        # Production populations can use membership(qid TEXT PRIMARY KEY, binding_sha256 TEXT).
        self.database = pinned(self.members['database']) if 'database' in self.members else None
        self.rows = self.members.get('rows', {})

    def check(self, row, *, require_frames=True):
        # The production direct-row adapter keeps the complete original evidence.
        source = row.get('repair_source_row', row)
        expected = self.rows.get(source['qid'])
        if self.database is not None:
            with closing(sqlite3.connect(self.database.as_uri()+'?mode=ro&immutable=1', uri=True)) as conn:
                found = conn.execute('SELECT binding_sha256 FROM membership WHERE qid=?', (source['qid'],)).fetchone()
                expected = found[0] if found else None
        if expected is None:
            raise ValueError('R1 row missing from sealed membership')
        validate(source, expected=expected, exclusions=self.exclusions, require_frames=require_frames)
        if source is not row and (row['target'] != source['target'] or row['student_input'] != source['student_input']):
            raise ValueError('R1 encoded row differs from admitted evidence')
        return row


def preserve_direct(raw):
    r2_trace.direct(raw)
    validate(raw)
    return deepcopy(raw), False
