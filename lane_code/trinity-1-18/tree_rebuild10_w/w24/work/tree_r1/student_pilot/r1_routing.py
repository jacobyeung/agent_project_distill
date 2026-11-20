"""Compose vehicle N's admitted routing stream before native preparation."""
from collections import Counter
from pathlib import Path
import json
import sqlite3
from .p3_provenance import digest, file_pin, load, pinned, write
from .r1_population import family, SLICE_CELLS, Membership


def check_local_size(size):
    """Check the local proof's storage ceiling before publishing database bytes."""
    import os
    if size > 200_000_000 and os.uname().nodename.startswith('trinity'):
        raise ValueError('R1_LOCAL_COMPOSITION_STORAGE_LIMIT')


class Filters:
    """The native preparation predicates, also used by the local census entry."""
    def __init__(self, cfg, division_pin):
        from .r1_launch22 import validate_removals
        validate_removals(cfg)
        from .row_removals import Removals
        from .s1_exclusions import Exclusions
        from .carrier_c1_routing import load_exclusions
        self.cfg = cfg
        self.removals = Removals(cfg.get('remove_files', []))
        self.scenes = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
        division = load(pinned(division_pin))
        self.train = set(division['train_scenes'])
        self.heldout = set(division['heldout_scenes'])
        self.benchmark = load_exclusions(cfg.get('exclusions'))
        self.reported = load_exclusions(cfg.get('report_exclusions'))
        self.qids = {k:set(v) for k,v in load(pinned(cfg['exclude_qids'])).items()} if cfg.get('exclude_qids') else {}

    def reason(self, row, stream):
        from .carrier_c1_run import held_row, routed_type, excluded_row
        if not self.removals.keep(row, stream):
            return 'remove_files'
        scene = row.get('dataset','')+'/'+row.get('scene','')
        if scene in self.heldout:
            return 'division_heldout'
        if scene not in self.train:
            return 'division_outside'
        if held_row(row, stream, self.qids, self.cfg.get('exclude_sources') or {}):
            return 'exclude_qids'
        if stream == 'vqa' and routed_type(row, self.cfg):
            return 'routed_type'
        if excluded_row(row, self.benchmark, self.reported, stream)[0]:
            return 'benchmark_exclusion'
        if self.scenes.excluded(row):
            return 'scene_exclusion'
        return None


def compose(base_pin, sources, batches, cfg, output):
    """Consume authenticated intake batches, preserving source identity in stored rows."""
    from .carrier_c1_run import Rows
    from .carrier_c1_routing import ROUTING_SCHEMA
    base = load(pinned(base_pin))
    if base.get('schema') != ROUTING_SCHEMA or base.get('scene_role','train') != 'train' or base.get('heldout_overlap') != 0:
        raise ValueError('R1_ROUTING_BASE_INVALID')
    filters = Filters(cfg, base['division'])
    from .r1_rooms import Rooms
    authority = cfg['r1_training'].get('room_authority')
    rooms = Rooms(authority) if authority else None
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    members = dict(schema='r1-source-membership-v1', sources={
        k:dict(source=v, rows={}) for k,v in sources.items()})
    from .r1_coverage import source_names
    if set(sources) != set(source_names(sources)):
        raise ValueError('R1_ROUTING_SLICES_REQUIRED')
    for pin in sources.values():
        pinned(pin)
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    reader = Rows(dict(streams={}, r1_training=cfg['r1_training'], extent_receipt=cfg.get('extent_receipt'),
                       remove_files=cfg.get('remove_files', [])), None)
    reader.connections['routing'] = db
    seen, counts, refused, scenes = set(), Counter(), Counter(), set()
    n = 0

    def add(row, target, origin):
        nonlocal n
        qid = row['qid']
        if qid in seen:
            raise ValueError('R1_ROUTING_DUPLICATE_QID:'+qid)
        seen.add(qid)
        why = filters.reason(row, 'routing')
        if why:
            refused[origin+':'+why] += 1
            return
        if rooms is not None and origin in sources:
            rooms.admit(row)
        db.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)', (n,json.dumps(row),json.dumps(target)))
        try:
            reader.row('routing', n)
        except (ValueError, KeyError, TypeError) as error:
            # Replace this candidate at the same offset; failed candidates never advance n.
            refused[origin+':reader:'+str(error)] += 1
            return
        counts[origin] += 1
        scenes.add(row['dataset']+'/'+row['scene'])
        if origin in members['sources']:
            members['sources'][origin]['rows'][qid] = digest(row)
        n += 1

    source = sqlite3.connect(pinned(base['database']).as_uri()+'?mode=ro', uri=True)
    try:
        for raw, target in source.execute('SELECT row,target FROM rows ORDER BY i'):
            row = json.loads(raw)
            if family(row, 'routing') in SLICE_CELLS:
                refused['base:replaced_cell'] += 1
                continue
            add(row, json.loads(target), 'base')
    finally:
        source.close()
    evidence = []
    for kind, source_pin, items, intake_pin in batches:
        if sources.get(kind) != source_pin:
            raise ValueError('R1_SLICE_SOURCE_DIFFERS:'+kind)
        pinned(intake_pin)
        evidence.append(intake_pin)
        for item in items:
            row = dict(item['row'])
            if row.get('events') and not row.get('routing'):
                from .carrier_c1_routing import c1_row
                inputs = row['student_input']
                rgb = dict(inputs, frames=[dict(pin, source_index=i) for i,pin in
                    zip(inputs['frame_indices'], inputs['frames'], strict=True)])
                row = c1_row(row, rgb)
            row['r1_source'] = dict(family=kind, sha256=source_pin['sha256'])
            add(row, item.get('target', {}), kind)
    # A trailing refused candidate must not become a stored row. Build the final
    # database from admitted offsets only, without modifying any source database.
    final = sqlite3.connect(':memory:')
    # The native layout repeats the ground record at top level and in routing.
    # Store it once and expose the exact native JSON through a SQLite view.
    final.execute('CREATE TABLE payloads(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    final.execute("CREATE VIEW rows AS SELECT i, CASE WHEN json_type(row,'$.ground_record')='object' AND json_type(row,'$.routing')='object' THEN json_set(row,'$.routing.ground_record',json_extract(row,'$.ground_record')) ELSE row END AS row,target FROM payloads")
    for i,raw,target in db.execute('SELECT i,row,target FROM rows WHERE i<? ORDER BY i',(n,)):
        row = json.loads(raw)
        if row.get('ground_record') and row.get('routing'):
            row = dict(row, routing={k:v for k,v in row['routing'].items() if k != 'ground_record'})
        final.execute('INSERT INTO payloads VALUES(?,?,?)',(i,json.dumps(row),target))
    write(output/'membership.json', members)
    membership = Membership(file_pin(output/'membership.json'))
    for (raw,) in final.execute('SELECT row FROM rows ORDER BY i'):
        membership.cell(json.loads(raw), 'routing')
    final.commit()
    payload = final.serialize()
    check_local_size(len(payload))
    (output/'rows.sqlite').write_bytes(payload)
    final.close()
    reader.close()
    result = dict(schema=ROUTING_SCHEMA, stream='routing', count=n, scenes=len(scenes),
        database=file_pin(output/'rows.sqlite'), division=base['division'], heldout_overlap=0, scene_role='train',
        source_membership=file_pin(output/'membership.json'), base=base_pin,
        per_source=dict(counts), refused=dict(refused), intake_evidence=evidence)
    write(output/'receipt.json', result)
    return result


def compose_native(cfg, base_pin, output):
    """Host envelopes must bind the exact source slices and independent scene coverage."""
    from .r2_intake import intake
    specs = load(pinned(cfg['r1_training']['row_sources']))
    from .r1_coverage import source_names, validate_binding
    validate_binding(cfg)
    names = source_names(specs)
    sources = {k:specs[k]['source'] for k in names}
    staged = cfg['r1_training'].get('row_slice_inputs', sources)
    if set(staged) != set(sources) or any(staged[k]['sha256'] != v['sha256'] for k,v in sources.items()):
        raise ValueError('R1_SLICE_SOURCE_DIFFERS:staging')
    sources = staged
    manifests = cfg['r1_training']['routing_inputs']
    catalog = load(pinned(cfg['r1_training']['source_membership']))
    if catalog.get('schema') != 'r1-source-catalog-v1' or set(catalog.get('sources', {})) != set(sources):
        raise ValueError('R1_SOURCE_CATALOG_INVALID')
    for kind, pin in sources.items():
        if catalog['sources'][kind]['source']['sha256'] != pin['sha256']:
            raise ValueError('R1_SOURCE_CATALOG_DIFFERS:'+kind)

    def batches():
        for kind in names:
            manifest_pin = manifests[kind]
            manifest = load(pinned(manifest_pin))
            if (manifest['rows'] != sources[kind] or manifest['family'] != kind
                    or manifest['stream'] != 'routing' or manifest.get('extent_receipt') != cfg.get('extent_receipt')):
                raise ValueError('R1_SLICE_MANIFEST_DIFFERS:'+kind)
            items, report = intake(pinned(manifest_pin), limit=None)
            if any(item['row']['qid'] not in catalog['sources'][kind]['qids'] for item in items):
                raise ValueError('R1_SLICE_ROW_MISFILED:'+kind)
            write(Path(output)/(kind+'_intake.json'), report)
            yield kind, sources[kind], items, manifest_pin
    Path(output).mkdir(parents=True, exist_ok=True)
    return compose(base_pin, sources, batches(), cfg, output)
