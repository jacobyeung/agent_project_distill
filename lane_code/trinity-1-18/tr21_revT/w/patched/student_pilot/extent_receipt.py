"""Training-input admission against an independently pinned box-extent audit."""
from .p3_provenance import digest, load, pinned


def required(row, stream):
    if isinstance(row.get('routing'), dict):
        row = {**row, **row['routing']}
    record = row.get('ground_record', row)
    kind = row.get('question_type', row.get('type', record.get('type')))
    return (stream == 'routing' or row.get('answer_form') == 'routed') and (
        kind in ('object_abs_distance', 'absolute_distance_object', 'camera_object_abs_distance', 'recovery', 'units')
        or bool(record.get('not_seen')))


def content(row):
    """Bind supervision and geometry; frame joins have separate admission pins."""
    if isinstance(row.get('routing'), dict):
        row = {**row, **row['routing']}
    return {key: row.get(key) for key in (
        'qid', 'source_qid', 'candidate_id', 'dataset', 'scene', 'question', 'question_type',
        'answer', 'gt_answer', 'target', 'ground_record', 'provenance', 'tool_output_spans')}


class Extents:
    def __init__(self, pin, pool_sources=None):
        if pool_sources is not None and (not isinstance(pool_sources, list)
                or any(not isinstance(name, str) or not name for name in pool_sources)):
            raise ValueError('EXTENT_POOL_SOURCES_INVALID')
        self.pool_sources = frozenset(pool_sources or ())
        self.exempted = 0
        self.receipt = load(pinned(pin)) if pin else None
        if self.receipt is not None and self.receipt.get('schema') != 'full-extent-receipt-v1':
            raise ValueError('EXTENT_RECEIPT_SCHEMA')

    def exempt(self, row, stream):
        # The native pool builder writes this field from its pinned selection;
        # callers authenticate database bytes or sealed row membership first.
        source = row.get('s1_source')
        return bool(self.pool_sources and stream == 'routing'
                    and not str(row.get('qid', '')).startswith('a0_')
                    and not row.get('r1_source') and isinstance(source, dict)
                    and source.get('name') in self.pool_sources)

    def check(self, row, stream):
        if self.exempt(row, stream):
            self.exempted += 1
            return
        if not required(row, stream):
            return
        if self.receipt is None:
            raise ValueError('EXTENT_RECEIPT_REQUIRED')
        entry = self.receipt['rows'].get(row.get('qid'))
        if entry is None or entry.get('content_sha256') != digest(content(row)):
            raise ValueError('EXTENT_ROW_UNAUDITED')
        statuses = entry.get('box_statuses', [])
        value = {**row, **row['routing']} if isinstance(row.get('routing'), dict) else row
        boxes = value.get('ground_record', value).get('program_audit', {}).get('independent_ordered_boxes', [])
        if not boxes or len(statuses) != len(boxes) or any(s != 'full' for s in statuses):
            raise ValueError('EXTENT_BOX_NOT_FULL')
        repair = row.get('provenance', {}).get('repair')
        if entry.get('repair_sha256') != (digest(repair) if repair else None):
            raise ValueError('EXTENT_REPAIR_UNCERTIFIED')
