"""Produce R1 populations in the final native reader's offset space."""
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from .p3_provenance import digest, file_pin, load, pinned, write
from .r1_training import STREAMS

# P's sealed family question types, renamed to the R1 card vocabulary.
TYPES = {
    'camera_displacement':'camera_displacement', 'camera_movement_direction':'camera_movement_direction',
    'camera_rotation':'camera_rotation', 'object_abs_distance':'absolute_distance',
    'absolute_distance_object':'absolute_distance', 'object_rel_distance':'relative_distance',
    'relative_distance_object':'relative_distance', 'camera_obj_rel_dist':'relative_distance',
    'camera_obj_abs_dist':'camera_object_abs_distance', 'obj_appearance_order':'appearance_order',
    'appearance_order':'appearance_order', 'first_seen_frame':'first_seen_frame',
    'box_3d':'box_3d', 'route_planning':'route_planning',
    'camera_obj_rel_dist_v1':'camera_object_rel_distance_v1',
    'camera_obj_rel_dist_v2':'camera_object_rel_distance_v2',
    'camera_obj_rel_dist_v3':'camera_object_rel_distance_v3',
    'obj_obj_relative_pos_lr':'object_object_left_right',
    'obj_obj_relative_pos_nf':'object_object_near_far',
    'obj_obj_relative_pos_ud':'object_object_up_down',
    **dict.fromkeys(('room_size_estimation','absolute_size_room'), 'room_size'),
    **dict.fromkeys(('object_size_estimation','absolute_size_object','relative_size_object'), 'object_size'),
    **dict.fromkeys(('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard',
                    'relative_direction_object','absolute_direction_object'), 'direction'),
    **dict.fromkeys(('object_counting','absolute_count','relative_count'), 'counting'),
}
SLICE_CELLS = ('recovery', 'absolute_distance', 'units')


def family(row, stream):
    if stream not in ('vqa', 'routing'):
        return stream
    raw = row.get('routing', row)
    typ = raw.get('question_type', row.get('question_type'))
    if stream == 'routing':
        record = raw.get('ground_record', {})
        qid = str(row.get('qid', raw.get('qid', '')))
        if record.get('not_seen') or qid.startswith('a0_recovery_'):
            return 'recovery'
        if record.get('unit') or qid.startswith('a0_units_'):
            return 'units'
        if typ not in ('camera_displacement','camera_movement_direction','camera_rotation',
                       'object_abs_distance','absolute_distance_object'):
            return 'unassigned:'+str(typ)
    kind = TYPES.get(typ, 'unassigned:'+str(typ))
    if kind == 'direction' and row.get('facing') in ('toward','away'):
        return 'facing_pairs'
    if kind == 'counting' and row.get('count_kind') == 'total':
        return 'totals'
    return kind


class Membership:
    """Authenticate composed slice QIDs and source hashes; never infer them from prose."""
    def __init__(self, pin, *, minimal=False):
        self.pin = pin
        self.minimal = minimal
        value = load(pinned(pin))
        if value.get('schema') != 'r1-source-membership-v1':
            raise ValueError('R1_SOURCE_MEMBERSHIP_INVALID')
        self.rows = {}
        self.sources = value['sources']
        if minimal:
            from .r1_coverage import deferred
            deferred({'r1_training': {'routing_slices': 'deferred_first_boundary'}}, membership=value)
        from .r1_coverage import PINS, source_names
        source_names(self.sources)
        for kind, source in self.sources.items():
            if kind not in (*SLICE_CELLS,*PINS):
                raise ValueError('R1_SLICE_CELL_INVALID:'+kind)
            pinned(source['source'])
            for qid, row_hash in source['rows'].items():
                if qid in self.rows:
                    raise ValueError('R1_SLICE_QID_OVERLAP:'+qid)
                self.rows[qid] = (kind, source['source']['sha256'], row_hash)

    def cell(self, row, stream):
        if self.minimal and stream == 'routing':
            if row.get('r1_source'):
                raise ValueError('R1_DEFERRED_ROW_PRESENT:'+row['qid'])
            return 'routing_base'
        entry = self.rows.get(row['qid']) if stream == 'routing' else None
        marker = row.get('r1_source')
        if entry is None:
            if marker:
                raise ValueError('R1_SLICE_ROW_MISFILED:'+row['qid'])
            kind = family(row, stream)
            if stream == 'routing' and kind in SLICE_CELLS:
                raise ValueError('R1_BASE_DISTANCE_OR_UNIT_RETAINED:'+row['qid'])
            return kind
        kind, source_hash, row_hash = entry
        if marker != dict(family=kind, sha256=source_hash) or digest(row) != row_hash:
            raise ValueError('R1_SLICE_ROW_MISFILED:'+row['qid'])
        return 'coverage' if kind in ('coverage_units','coverage_distance') else kind


def produce(reader, card_pin, membership_pin, evidence, output, *, cfg=None):
    """Walk every prepared offset. Reader failures refuse the population, never disappear."""
    from .r1_coverage import deferred, deferred_card
    minimal = deferred(cfg, read_pins=True)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    card = load(pinned(card_pin))
    deferred(cfg, card=card)
    if minimal:
        deferred_card(card)
    membership = Membership(membership_pin, minimal=minimal)
    groups = {c['type']:[] for c in card['cells']}
    streams = {c['type']:c['stream'] for c in card['cells']}
    unknown, pairs = Counter(), defaultdict(Counter)
    units, overrides = Counter(), Counter()
    examples = defaultdict(list)
    for stream in STREAMS:
        for offset in range(reader.count(stream)):
            row, _ = reader.row(stream, offset)
            kind = membership.cell(row, stream)
            if card.get('counting_admission') == 'procedure_only_v1':
                from .r1_counting import admit
                admit(row, kind)
            if streams.get(kind) != stream:
                unknown[kind] += 1
                continue
            groups[kind].append(offset)
            if stream == 'routing' and row.get('r1_source') and family(row, stream) != kind:
                overrides[kind] += 1
            if kind == 'units':
                from .r2_units import asked_unit
                units[asked_unit(row)] += 1
            if kind == 'facing_pairs':
                pairs[row.get('pair_id')][row.get('facing')] += 1
            if len(examples[kind]) < 5:
                examples[kind].append(dict(qid=row['qid'], row_sha256=digest(row)))
    if unknown:
        raise ValueError('R1_UNASSIGNED_TYPES:'+str(dict(sorted(unknown.items()))))
    counts = {k:len(v) for k,v in groups.items()}
    if minimal:
        deferred_card(card, counts, groups)
    population = dict(schema='r1-population-v1', complete=True, after_all_filters=True,
        card_sha256=card_pin['sha256'], counts=counts, evidence=[*evidence, membership_pin],
        source_membership=membership_pin, examples=dict(examples),
        asked_units=dict(units), source_identity_overrides=dict(overrides),
        facing=dict(draw_unit='single row', pair_ids=len(pairs),
            complete_pair_ids=sum(set(v)=={'toward','away'} for v in pairs.values()),
            incomplete_pair_ids=sum(set(v)!={'toward','away'} for v in pairs.values()),
            rows=sum(sum(v.values()) for v in pairs.values())))
    write(output/'population.json', population)
    pop_pin = file_pin(output/'population.json')
    write(output/'indices.json', dict(population_sha256=pop_pin['sha256'], cells=groups))
    binding = dict(schema='r1-sampling-v1', card=card_pin, population=pop_pin,
                   indices=file_pin(output/'indices.json'))
    from .r1_mix import plans
    next(plans(binding, {s:reader.count(s) for s in STREAMS}, 1))
    write(output/'binding.json', binding)
    return binding


def bind_prepared(cfg, output):
    """Publish a new preparation and config after native reader filtering and production."""
    from .carrier_c1_run import Rows, prepared, identity
    from .source_seal import binding as seal_binding
    from .r1_coverage import deferred
    deferred(cfg, read_pins=True)
    receipt, _ = prepared(cfg)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    from .r1_coverage import deferred
    routing = load(pinned(cfg['streams']['routing']))
    if deferred(cfg):
        if routing.get('source_membership'):
            raise ValueError('R1_DEFERRED_MEMBERSHIP_NONEMPTY')
        write(output/'base_membership.json', dict(schema='r1-source-membership-v1', sources={},
              base=cfg['streams']['routing'], routing_slices='deferred_first_boundary'))
        membership_pin = file_pin(output/'base_membership.json')
    else:
        membership_pin = routing['source_membership']
    current = deepcopy(receipt)
    refusals = {}
    reader = Rows(receipt, None)
    try:
        for stream in STREAMS:
            selected, refused = [], Counter()
            key = 'order' if stream in reader.mixes else 'indices'
            original = reader.mixes[stream].order if stream in reader.mixes else reader.indices.get(stream, range(reader.count(stream)))
            for i in range(reader.count(stream)):
                try:
                    reader.row(stream, i)
                except (ValueError, KeyError, TypeError) as error:
                    refused[type(error).__name__+':'+str(error)] += 1
                else:
                    selected.append(original[i])
            write(output/(stream+'_'+key+'.json'), selected)
            current['streams'][stream].update(reader_source=deepcopy(receipt['streams'][stream]),
                count=len(selected), **{key:file_pin(output/(stream+'_'+key+'.json'))})
            refusals[stream] = dict(refused)
    finally:
        reader.close()
    write(output/'reader_filters.json', dict(parent=cfg['preparation'], refusals=refusals))
    reader = Rows(current, None)
    try:
        result = produce(reader, cfg['r1_training']['mix'],
            membership_pin,
            [cfg['preparation'], file_pin(output/'reader_filters.json'),
             *[v['receipt'] for v in current['streams'].values()]], output, cfg=cfg)
    finally:
        reader.close()
    cfg = deepcopy(cfg)
    cfg['r2_sampling'] = result
    cfg['r1_training']['row_plan_sha256'] = digest(result)
    if cfg['r1_training'].get('handover_receipt'):
        from .r1_handover import bind_target
        cfg = bind_target(cfg,output/'handover.json')
    current.update(r2_sampling=result, r1_training=cfg['r1_training'], config_sha256=identity(cfg))
    sealed = seal_binding(load(pinned(cfg['code'])), current['config_sha256'])
    if sealed is not None:
        current['source_seal'] = sealed
    write(output/'receipt.json', current)
    cfg['preparation'] = file_pin(output/'receipt.json')
    write(output/'config.json', cfg)
    return file_pin(output/'config.json')


def scene_receipt(receipt):
    """Validate reader-filter subsets, then expose the unchanged scene-filter proof."""
    result = deepcopy(receipt)
    for stream, value in receipt['streams'].items():
        if 'reader_source' not in value:
            continue
        original = value['reader_source']
        key = 'order' if original.get('kind') == 'mix' else 'indices'
        offsets = load(pinned(value[key]))
        parent = load(pinned(original[key])) if key in original else list(range(original['count']))
        keys = [tuple(x) if isinstance(x,list) else x for x in offsets]
        parent_keys = [tuple(x) if isinstance(x,list) else x for x in parent]
        selected = set(keys)
        if (len(selected) != len(keys) or len(offsets) != value['count']
                or [x for x in parent_keys if x in selected] != keys
                or {k:v for k,v in value.items() if k not in ('reader_source','count',key)}
                   != {k:v for k,v in original.items() if k not in ('count',key)}):
            raise ValueError('R1_READER_SELECTION_DIFFERS:'+stream)
        result['streams'][stream] = original
    return result
